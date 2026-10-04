"""Sales & Demand ML Predictor.

Forecasts next-period demand using the hybrid ensemble (RF, XGBoost, ANN)
trained on log-space target with feature engineering and SLSQP weights.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd

from app.ml.base import BaseMLModel
from app.ml.ensemble import EnsembleWeights, HybridEnsemblePredictor


@dataclass
class SalesPredictionResult:
    """Encapsulates sales and demand prediction outcomes."""

    predicted_demand: float
    base_predictions: Dict[str, float]
    ensemble_weights: Dict[str, float]
    target_period: str = "next_30_days"
    sku_id: Optional[str] = None


class SalesDemandPredictor:
    """Inference orchestrator for next-period sales demand forecasting."""

    def __init__(
        self,
        rf_model: Optional[BaseMLModel] = None,
        xgb_model: Optional[BaseMLModel] = None,
        ann_model: Optional[BaseMLModel] = None,
        preprocessor: Optional[Any] = None,
        ensemble_weights: Optional[EnsembleWeights] = None,
        sku_map: Optional[Dict[str, float]] = None,
        global_mean: float = 64.0,
    ) -> None:
        self.rf_model = rf_model
        self.xgb_model = xgb_model
        self.ann_model = ann_model
        self.preprocessor = preprocessor
        self.ensemble_weights = ensemble_weights
        self.sku_map = sku_map or {}
        self.global_mean = global_mean
        self.ensemble_predictor = HybridEnsemblePredictor(weights=ensemble_weights)

    @classmethod
    def from_registry(cls) -> "SalesDemandPredictor":
        """Factory method loading cached artifacts from ModelRegistry."""
        from app.ml.registry import ModelRegistry
        registry = ModelRegistry.get_instance()
        art = registry.sales_artifacts
        if not art:
            raise RuntimeError("Sales ML artifacts are not loaded in registry.")
        return cls(
            rf_model=art["rf_model"],
            xgb_model=art["xgb_model"],
            ann_model=art["ann_model"],
            preprocessor=art["preprocessor"],
            ensemble_weights=art["ensemble_weights"],
            sku_map=art["sku_map"],
            global_mean=art["global_mean"],
        )

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforms raw input dataframe to match trained feature structure."""
        df_feat = df.copy()

        # Fill defaults if missing
        if "discount_rate" not in df_feat:
            df_feat["discount_rate"] = 0.0
        if "promotional_flag" not in df_feat:
            df_feat["promotional_flag"] = 0
        if "day_of_week" not in df_feat:
            df_feat["day_of_week"] = 2
        if "month" not in df_feat:
            df_feat["month"] = 6
        if "product_category" not in df_feat:
            df_feat["product_category"] = "Hardware"
        if "rolling_avg_30" not in df_feat:
            df_feat["rolling_avg_30"] = df_feat["sales_lag_1"] if "sales_lag_1" in df_feat else 50.0

        # Feature transformations
        df_feat["effective_price"] = df_feat["unit_price"] * (1.0 - df_feat["discount_rate"])
        df_feat["promo_intensity"] = df_feat["promotional_flag"] * df_feat["discount_rate"]
        df_feat["lag1_to_rolling_ratio"] = df_feat["sales_lag_1"] / (df_feat["rolling_avg_30"] + 1e-4)
        df_feat["lag7_to_rolling_ratio"] = df_feat["sales_lag_7"] / (df_feat["rolling_avg_30"] + 1e-4)
        df_feat["lag30_to_rolling_ratio"] = df_feat["sales_lag_30"] / (df_feat["rolling_avg_30"] + 1e-4)

        df_feat["sin_dow"] = np.sin(2.0 * np.pi * df_feat["day_of_week"] / 7.0)
        df_feat["cos_dow"] = np.cos(2.0 * np.pi * df_feat["day_of_week"] / 7.0)
        df_feat["sin_month"] = np.sin(2.0 * np.pi * df_feat["month"] / 12.0)
        df_feat["cos_month"] = np.cos(2.0 * np.pi * df_feat["month"] / 12.0)

        # SKU target encoding
        if "sku_id" in df_feat:
            df_feat["sku_demand_velocity"] = df_feat["sku_id"].map(self.sku_map).fillna(self.global_mean)
        else:
            df_feat["sku_demand_velocity"] = self.global_mean

        feature_cols = [
            "sales_lag_1",
            "sales_lag_7",
            "sales_lag_30",
            "rolling_avg_30",
            "discount_rate",
            "promotional_flag",
            "unit_price",
            "effective_price",
            "promo_intensity",
            "lag1_to_rolling_ratio",
            "lag7_to_rolling_ratio",
            "lag30_to_rolling_ratio",
            "sin_dow",
            "cos_dow",
            "sin_month",
            "cos_month",
            "sku_demand_velocity",
            "product_category",
        ]
        return df_feat[feature_cols]

    def predict_next_period_demand(
        self,
        features: pd.DataFrame,
        target_period: str = "next_30_days",
        sku_id: Optional[str] = None,
    ) -> SalesPredictionResult:
        """Runs base models on log target space, inverts to natural scale, and aggregates."""
        if not (self.rf_model and self.xgb_model and self.ann_model and self.preprocessor and self.ensemble_weights):
            raise NotImplementedError("Trained models and preprocessor must be loaded.")

        # 1. Feature Engineering
        engineered_df = self.engineer_features(features)

        # 2. ColumnTransformer preprocessing
        X_processed = self.preprocessor.transform(engineered_df)

        # 3. Base model inference in log space
        z_rf = float(self.rf_model.predict(X_processed)[0])
        z_xgb = float(self.xgb_model.predict(X_processed)[0])
        z_ann = float(self.ann_model.predict(X_processed)[0])

        # 4. Inverse exponential transformation: y = max(0, exp(z) - 1)
        pred_rf = float(max(0.0, np.expm1(z_rf)))
        pred_xgb = float(max(0.0, np.expm1(z_xgb)))
        pred_ann = float(max(0.0, np.expm1(z_ann)))

        # 5. Hybrid Ensemble Aggregation
        final_demand = float(self.ensemble_predictor.predict(
            pred_rf=pred_rf,
            pred_xgb=pred_xgb,
            pred_ann=pred_ann,
        ))

        return SalesPredictionResult(
            predicted_demand=round(final_demand, 2),
            base_predictions={
                "rf": round(pred_rf, 2),
                "xgb": round(pred_xgb, 2),
                "ann": round(pred_ann, 2),
            },
            ensemble_weights=self.ensemble_weights.to_dict(),
            target_period=target_period,
            sku_id=sku_id or (str(features["sku_id"].iloc[0]) if "sku_id" in features else None),
        )
