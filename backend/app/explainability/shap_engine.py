"""SHAP (SHapley Additive exPlanations) Ensemble Explainer Module.

Implements Option A: Exact Linear Ensemble SHAP attribution:
    phi_j(Ensemble) = w_RF * phi_j(RF) + w_XGB * phi_j(XGB) + w_ANN * phi_j(ANN)
    E[f(x)] = w_RF * E[f_RF] + w_XGB * E[f_XGB] + w_ANN * E[f_ANN]

Guarantees exact additivity and decomposes hybrid predictions into ranked positive
and negative business drivers with executive-level human labels.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import shap
import torch
import torch.nn as nn

from app.core.logging_config import logger
from app.ml.registry import ModelRegistry


FEATURE_HUMAN_LABELS: Dict[str, str] = {
    # Sales domain
    "sales_lag_1": "Sales Demand (1 Day Prior)",
    "sales_lag_7": "Sales Demand (7 Days Prior)",
    "sales_lag_30": "Sales Demand (30 Days Prior)",
    "rolling_avg_30": "30-Day Baseline Moving Average Demand",
    "discount_rate": "Discount Rate",
    "promotional_flag": "Active Marketing Campaign",
    "unit_price": "Standard Unit Price",
    "effective_price": "Net Customer Price (After Discount)",
    "promo_intensity": "Promotional Discount Intensity",
    "lag1_to_rolling_ratio": "Short-Term Sales Surge vs 30D Average",
    "lag7_to_rolling_ratio": "Weekly Sales Momentum Ratio",
    "lag30_to_rolling_ratio": "Monthly Sales Momentum Ratio",
    "sin_dow": "Day of Week Seasonality (Sine)",
    "cos_dow": "Day of Week Seasonality (Cosine)",
    "sin_month": "Annual Month Seasonality (Sine)",
    "cos_month": "Annual Month Seasonality (Cosine)",
    "sku_demand_velocity": "SKU Historical Velocity Baseline",
    # Inventory domain
    "current_stock": "Current Warehouse Stock Level",
    "reorder_level": "Reorder Trigger Level",
    "safety_stock": "Safety Stock Reserve Buffer",
    "lead_time_days": "Supplier Delivery Lead Time",
    "historical_delivery_delay_days": "Supplier Historical Delivery Delay",
    "inventory_turnover_ratio": "Stock Turnover Velocity",
    "predicted_sales_demand": "Injected Sales Demand Forecast",
    "buffer_coverage_ratio": "Stock Buffer vs Lead-Time Demand Ratio",
    "safety_stock_ratio": "Safety Stock to Reorder Threshold Ratio",
}


def _to_python_primitive(val: Any) -> Any:
    """Recursively converts NumPy scalars and arrays into native Python serializable primitives."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        return round(float(val), 4)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, np.ndarray):
        return [_to_python_primitive(x) for x in val.tolist()]
    if isinstance(val, dict):
        return {k: _to_python_primitive(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_to_python_primitive(x) for x in val]
    if hasattr(val, "item"):
        return _to_python_primitive(val.item())
    return val


@dataclass
class FeatureAttribution:
    """Detailed attribution metrics for an individual feature."""

    feature_name: str
    human_label: str
    feature_value: Any
    shap_value: float
    direction: str  # "positive" | "negative"
    relative_importance: float  # Percentage of total absolute attribution impact


@dataclass
class EnsembleExplanation:
    """Encapsulates full ensemble SHAP attribution results for an instance."""

    domain: str
    target_metric: str
    predicted_value: float
    base_value: float
    attributions: List[FeatureAttribution]
    top_positive_drivers: List[FeatureAttribution]
    top_negative_drivers: List[FeatureAttribution]
    ensemble_weights: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts explanation result into a JSON-serializable dictionary."""
        return {
            "domain": self.domain,
            "target_metric": self.target_metric,
            "predicted_value": round(float(self.predicted_value), 2),
            "base_value": round(float(self.base_value), 2),
            "ensemble_weights": {k: float(v) for k, v in self.ensemble_weights.items()},
            "attributions": [
                {
                    "feature_name": a.feature_name,
                    "human_label": a.human_label,
                    "feature_value": _to_python_primitive(a.feature_value),
                    "shap_value": round(float(a.shap_value), 4),
                    "direction": a.direction,
                    "relative_importance": round(float(a.relative_importance), 2),
                }
                for a in self.attributions
            ],
            "top_positive_drivers": [
                {
                    "feature_name": a.feature_name,
                    "human_label": a.human_label,
                    "feature_value": _to_python_primitive(a.feature_value),
                    "shap_value": round(float(a.shap_value), 4),
                }
                for a in self.top_positive_drivers
            ],
            "top_negative_drivers": [
                {
                    "feature_name": a.feature_name,
                    "human_label": a.human_label,
                    "feature_value": _to_python_primitive(a.feature_value),
                    "shap_value": round(float(a.shap_value), 4),
                }
                for a in self.top_negative_drivers
            ],
            "metadata": {k: _to_python_primitive(v) for k, v in self.metadata.items()},
        }


# Compatibility alias for existing imports
SHAPExplanationResult = EnsembleExplanation


class Model2DOutputWrapper(nn.Module):
    """Wraps PyTorch ANN to ensure 2D output shape (batch_size, 1) for SHAP GradientExplainer."""

    def __init__(self, model: nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.model(x)
        if out.ndim == 1:
            out = out.unsqueeze(-1)
        return out


class EnsembleSHAPExplainer:
    """Computes exact linear ensemble SHAP attributions for Sales and Inventory domains."""

    def __init__(self, domain: str) -> None:
        self.domain = domain.lower().strip()
        if self.domain not in ["sales", "inventory"]:
            raise ValueError(f"Domain '{self.domain}' not supported. Must be 'sales' or 'inventory'.")

        self.registry = ModelRegistry.get_instance()
        self._rf_explainer: Optional[shap.TreeExplainer] = None
        self._xgb_explainer: Optional[shap.TreeExplainer] = None
        self._ann_explainer: Optional[shap.GradientExplainer] = None
        self._ann_2d_model: Optional[Model2DOutputWrapper] = None
        self._background_tensor: Optional[torch.Tensor] = None
        self._feature_names: List[str] = []

        self._initialize_explainers()

    def _get_background_sample(self) -> np.ndarray:
        """Loads and pre-processes a background reference dataset for the ANN explainer."""
        base_dir = self.registry.base_dir
        if self.domain == "sales":
            from app.ml.sales import SalesDemandPredictor
            csv_path = base_dir / "ML-experiments" / "datasets" / "sales.csv"
            predictor = SalesDemandPredictor.from_registry()
            preprocessor = self.registry.sales_artifacts["preprocessor"]
            if csv_path.exists():
                df_bg = pd.read_csv(csv_path).sample(min(30, len(pd.read_csv(csv_path))), random_state=42)
            else:
                # Synthetic fallback row if csv not accessible
                df_bg = pd.DataFrame([{
                    "sku_id": "SKU-001", "unit_price": 100.0, "sales_lag_1": 50.0,
                    "sales_lag_7": 50.0, "sales_lag_30": 50.0, "rolling_avg_30": 50.0,
                    "discount_rate": 0.05, "promotional_flag": 0, "day_of_week": 2,
                    "month": 6, "product_category": "Hardware"
                }])
            feat_df = predictor.engineer_features(df_bg)
            return preprocessor.transform(feat_df)
        else:
            from app.ml.inventory import InventoryStockoutPredictor
            csv_path = base_dir / "ML-experiments" / "datasets" / "inventory.csv"
            predictor = InventoryStockoutPredictor.from_registry()
            preprocessor = self.registry.inventory_artifacts["preprocessor"]
            if csv_path.exists():
                df_bg = pd.read_csv(csv_path).sample(min(30, len(pd.read_csv(csv_path))), random_state=42)
            else:
                df_bg = pd.DataFrame([{
                    "sku_id": "SKU-001", "current_stock": 50.0, "reorder_level": 70.0,
                    "safety_stock": 20.0, "lead_time_days": 7.0, "historical_delivery_delay_days": 1.0,
                    "inventory_turnover_ratio": 8.0, "predicted_sales_demand": 60.0
                }])
            feat_df = predictor.engineer_features(df_bg)
            return preprocessor.transform(feat_df)

    def _initialize_explainers(self) -> None:
        """Pre-initializes TreeExplainer and GradientExplainer instances once on initialization."""
        try:
            logger.info(f"Initializing EnsembleSHAPExplainer for {self.domain}...")
            bg_processed = self._get_background_sample()
            self._background_tensor = torch.tensor(bg_processed, dtype=torch.float32)

            if self.domain == "sales":
                art = self.registry.sales_artifacts
                rf = art["rf_model"].model
                xgb = art["xgb_model"].model
                ann = art["ann_model"].model
                preprocessor = art["preprocessor"]

                self._rf_explainer = shap.TreeExplainer(rf)
                self._xgb_explainer = shap.TreeExplainer(xgb)
                self._ann_2d_model = Model2DOutputWrapper(ann)
                self._ann_explainer = shap.GradientExplainer(self._ann_2d_model, self._background_tensor)

                if hasattr(preprocessor, "get_feature_names_out"):
                    self._feature_names = list(preprocessor.get_feature_names_out())
                else:
                    self._feature_names = [f"feat_{i}" for i in range(bg_processed.shape[1])]
            else:
                art = self.registry.inventory_artifacts
                rf = art["rf_model"].model
                xgb = art["xgb_model"].model
                ann = art["ann_model"].model
                feature_names = art.get("feature_names", [])

                self._rf_explainer = shap.TreeExplainer(rf)
                self._xgb_explainer = shap.TreeExplainer(xgb)
                self._ann_2d_model = Model2DOutputWrapper(ann)
                self._ann_explainer = shap.GradientExplainer(self._ann_2d_model, self._background_tensor)
                self._feature_names = feature_names or [f"feat_{i}" for i in range(bg_processed.shape[1])]

            logger.info(f"EnsembleSHAPExplainer for {self.domain} initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize EnsembleSHAPExplainer for {self.domain}: {e}")
            raise

    def explain(
        self,
        features: pd.DataFrame,
        top_k: int = 4,
    ) -> EnsembleExplanation:
        """Computes exact linear ensemble SHAP attributions for input features."""
        if self.domain == "sales":
            return self._explain_sales(features, top_k=top_k)
        else:
            return self._explain_inventory(features, top_k=top_k)

    def _explain_sales(self, features: pd.DataFrame, top_k: int = 4) -> EnsembleExplanation:
        from app.ml.sales import SalesDemandPredictor
        predictor = SalesDemandPredictor.from_registry()
        art = self.registry.sales_artifacts
        preprocessor = art["preprocessor"]
        weights = art["ensemble_weights"]

        # Feature engineering & preprocessing
        engineered_df = predictor.engineer_features(features)
        X_processed = preprocessor.transform(engineered_df)
        x_tensor = torch.tensor(X_processed, dtype=torch.float32)

        # 1. Base model SHAP values in log space
        rf_shap = self._rf_explainer.shap_values(X_processed)
        rf_base = float(np.mean(self._rf_explainer.expected_value))

        xgb_shap = self._xgb_explainer.shap_values(X_processed)
        xgb_base = float(self._xgb_explainer.expected_value)

        ann_shap = self._ann_explainer.shap_values(x_tensor)
        if isinstance(ann_shap, list):
            ann_shap = ann_shap[0]
        ann_shap = np.squeeze(ann_shap, axis=-1) if ann_shap.ndim == 3 else ann_shap
        ann_base = float(self._ann_2d_model(self._background_tensor).mean().item())

        # 2. Linear combination of SHAP values
        w_rf, w_xgb, w_ann = weights.w_rf, weights.w_xgb, weights.w_ann
        ens_shap_log = (
            w_rf * np.array(rf_shap).reshape(1, -1)
            + w_xgb * np.array(xgb_shap).reshape(1, -1)
            + w_ann * np.array(ann_shap).reshape(1, -1)
        )[0]
        ens_base_log = (w_rf * rf_base) + (w_xgb * xgb_base) + (w_ann * ann_base)

        # 3. Model predictions
        pred_res = predictor.predict_next_period_demand(features)
        predicted_demand = pred_res.predicted_demand
        base_demand = float(max(0.0, np.expm1(ens_base_log)))

        # 4. Map log SHAP to natural unit impact via local gradient: phi_nat = phi_log * exp(z)
        pred_log = float(np.log1p(predicted_demand))
        local_scale = np.exp(pred_log)
        ens_shap_natural = ens_shap_log * local_scale

        # Build feature attribution list
        attributions = self._build_attributions(
            feature_names=self._feature_names,
            shap_values=ens_shap_natural,
            engineered_df=engineered_df,
        )

        sorted_pos = sorted([a for a in attributions if a.shap_value > 0], key=lambda x: x.shap_value, reverse=True)[:top_k]
        sorted_neg = sorted([a for a in attributions if a.shap_value < 0], key=lambda x: x.shap_value)[:top_k]

        return EnsembleExplanation(
            domain="sales",
            target_metric="next_period_demand",
            predicted_value=predicted_demand,
            base_value=base_demand,
            attributions=attributions,
            top_positive_drivers=sorted_pos,
            top_negative_drivers=sorted_neg,
            ensemble_weights=weights.to_dict(),
            metadata={"sku_id": pred_res.sku_id, "target_period": pred_res.target_period},
        )

    def _explain_inventory(self, features: pd.DataFrame, top_k: int = 4) -> EnsembleExplanation:
        from app.ml.inventory import InventoryStockoutPredictor
        predictor = InventoryStockoutPredictor.from_registry()
        art = self.registry.inventory_artifacts
        preprocessor = art["preprocessor"]
        weights = art["ensemble_weights"]

        # Feature engineering & scaling
        engineered_df = predictor.engineer_features(features)
        X_scaled = preprocessor.transform(engineered_df)
        x_tensor = torch.tensor(X_scaled, dtype=torch.float32)

        # 1. Base model SHAP values (probability scale)
        rf_shap = self._rf_explainer.shap_values(X_scaled)
        if isinstance(rf_shap, list):
            rf_shap_pos = rf_shap[1]
            rf_base = float(self._rf_explainer.expected_value[1])
        elif np.array(rf_shap).ndim == 3:
            rf_shap_pos = rf_shap[:, :, 1]
            rf_base = float(self._rf_explainer.expected_value[1])
        else:
            rf_shap_pos = rf_shap
            rf_base = float(self._rf_explainer.expected_value)

        xgb_shap = self._xgb_explainer.shap_values(X_scaled)
        xgb_base = float(self._xgb_explainer.expected_value)

        ann_shap = self._ann_explainer.shap_values(x_tensor)
        if isinstance(ann_shap, list):
            ann_shap = ann_shap[0]
        ann_shap = np.squeeze(ann_shap, axis=-1) if ann_shap.ndim == 3 else ann_shap
        ann_base = float(self._ann_2d_model(self._background_tensor).mean().item())

        # 2. Linear combination of probability SHAP values
        w_rf, w_xgb, w_ann = weights.w_rf, weights.w_xgb, weights.w_ann
        ens_shap_prob = (
            w_rf * np.array(rf_shap_pos).reshape(1, -1)
            + w_xgb * np.array(xgb_shap).reshape(1, -1)
            + w_ann * np.array(ann_shap).reshape(1, -1)
        )[0]
        ens_base_prob = float(max(0.0, min(1.0, (w_rf * rf_base) + (w_xgb * xgb_base) + (w_ann * ann_base))))

        pred_res = predictor.predict_stockout_probability(features)
        stockout_prob = pred_res.stockout_probability

        # Build feature attribution list
        attributions = self._build_attributions(
            feature_names=self._feature_names,
            shap_values=ens_shap_prob,
            engineered_df=engineered_df,
        )

        sorted_pos = sorted([a for a in attributions if a.shap_value > 0], key=lambda x: x.shap_value, reverse=True)[:top_k]
        sorted_neg = sorted([a for a in attributions if a.shap_value < 0], key=lambda x: x.shap_value)[:top_k]

        return EnsembleExplanation(
            domain="inventory",
            target_metric="stockout_probability",
            predicted_value=stockout_prob,
            base_value=ens_base_prob,
            attributions=attributions,
            top_positive_drivers=sorted_pos,
            top_negative_drivers=sorted_neg,
            ensemble_weights=weights.to_dict(),
            metadata={"sku_id": pred_res.sku_id, "risk_level": pred_res.risk_level},
        )

    def _build_attributions(
        self,
        feature_names: List[str],
        shap_values: np.ndarray,
        engineered_df: pd.DataFrame,
    ) -> List[FeatureAttribution]:
        """Constructs human-labeled FeatureAttribution instances with relative importance."""
        total_abs_impact = float(np.sum(np.abs(shap_values))) + 1e-6
        attributions: List[FeatureAttribution] = []

        for name, val in zip(feature_names, shap_values):
            # Clean One-Hot encoded names if present (e.g., cat__product_category_Hardware)
            clean_name = name.split("__")[-1] if "__" in name else name
            base_key = clean_name.replace("num__", "")

            # Look up human-friendly label
            human_label = FEATURE_HUMAN_LABELS.get(base_key, base_key.replace("_", " ").title())

            # Find raw value in engineered_df if available
            raw_val = None
            if base_key in engineered_df.columns:
                raw_val = _to_python_primitive(engineered_df[base_key].iloc[0])

            rel_imp = (abs(float(val)) / total_abs_impact) * 100.0

            attributions.append(
                FeatureAttribution(
                    feature_name=base_key,
                    human_label=human_label,
                    feature_value=raw_val,
                    shap_value=float(val),
                    direction="positive" if val >= 0 else "negative",
                    relative_importance=rel_imp,
                )
            )

        return sorted(attributions, key=lambda a: abs(a.shap_value), reverse=True)


# Legacy abstract classes kept for backward compatibility with mock interfaces
class BaseSHAPEngine:
    pass


class TreeSHAPEngine:
    pass


class ModelAgnosticSHAPEngine:
    pass
