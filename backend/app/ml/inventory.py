"""Inventory ML Predictor.

Estimates stockout probability before supplier delivery using the hybrid ensemble
(RF, XGBoost, ANN) with domain feature engineering and SLSQP weights.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from app.ml.base import BaseMLModel
from app.ml.ensemble import EnsembleWeights, HybridEnsemblePredictor


@dataclass
class StockoutPredictionResult:
    """Encapsulates stockout probability prediction outcomes."""

    stockout_probability: float
    risk_level: str
    base_predictions: Dict[str, float]
    ensemble_weights: Dict[str, float]
    sku_id: Optional[str] = None


class InventoryStockoutPredictor:
    """Inference orchestrator for stockout risk estimation."""

    def __init__(
        self,
        rf_model: Optional[BaseMLModel] = None,
        xgb_model: Optional[BaseMLModel] = None,
        ann_model: Optional[BaseMLModel] = None,
        preprocessor: Optional[Any] = None,
        ensemble_weights: Optional[EnsembleWeights] = None,
        feature_names: Optional[List[str]] = None,
    ) -> None:
        self.rf_model = rf_model
        self.xgb_model = xgb_model
        self.ann_model = ann_model
        self.preprocessor = preprocessor
        self.ensemble_weights = ensemble_weights
        self.feature_names = feature_names or []
        self.ensemble_predictor = HybridEnsemblePredictor(weights=ensemble_weights)

    @classmethod
    def from_registry(cls) -> "InventoryStockoutPredictor":
        """Factory method loading cached artifacts from ModelRegistry."""
        from app.ml.registry import ModelRegistry
        registry = ModelRegistry.get_instance()
        art = registry.inventory_artifacts
        if not art:
            raise RuntimeError("Inventory ML artifacts are not loaded in registry.")
        return cls(
            rf_model=art["rf_model"],
            xgb_model=art["xgb_model"],
            ann_model=art["ann_model"],
            preprocessor=art["preprocessor"],
            ensemble_weights=art["ensemble_weights"],
            feature_names=art.get("feature_names", []),
        )

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates domain inventory ratios matching trained offline experiments."""
        raw_numeric = [
            "current_stock",
            "reorder_level",
            "safety_stock",
            "lead_time_days",
            "historical_delivery_delay_days",
            "inventory_turnover_ratio",
            "predicted_sales_demand",
        ]
        df_feat = df[raw_numeric].copy()

        # Expected replenishment demand during lead time + delay
        lead_time_demand = (df_feat["predicted_sales_demand"] / 7.0) * (
            df_feat["lead_time_days"] + df_feat["historical_delivery_delay_days"]
        )

        df_feat["buffer_coverage_ratio"] = df_feat["current_stock"] / (lead_time_demand + 1e-4)
        df_feat["safety_stock_ratio"] = df_feat["safety_stock"] / (df_feat["reorder_level"] + 1e-4)

        return df_feat

    def _determine_risk_level(self, prob: float) -> str:
        """Classifies stockout probability into actionable risk tiers."""
        if prob >= 0.85:
            return "CRITICAL"
        elif prob >= 0.60:
            return "HIGH"
        elif prob >= 0.25:
            return "MEDIUM"
        return "LOW"

    def predict_stockout_probability(
        self,
        features: pd.DataFrame,
        sku_id: Optional[str] = None,
    ) -> StockoutPredictionResult:
        """Estimates stockout probability before supplier delivery."""
        if not (self.rf_model and self.xgb_model and self.ann_model and self.preprocessor and self.ensemble_weights):
            raise NotImplementedError("Trained inventory models and preprocessor must be loaded.")

        # 1. Feature Engineering
        engineered_df = self.engineer_features(features)

        # 2. Scaler transformation
        X_scaled = self.preprocessor.transform(engineered_df)

        # 3. Base model probability estimation
        p_rf = float(self.rf_model.predict(X_scaled)[0])
        p_xgb = float(self.xgb_model.predict(X_scaled)[0])
        p_ann = float(self.ann_model.predict(X_scaled)[0])

        # 4. Ensemble weighted combination
        prob = self.ensemble_predictor.predict(
            pred_rf=p_rf,
            pred_xgb=p_xgb,
            pred_ann=p_ann,
        )
        bounded_prob = round(float(max(0.0, min(1.0, prob))), 4)
        risk_level = self._determine_risk_level(bounded_prob)

        return StockoutPredictionResult(
            stockout_probability=bounded_prob,
            risk_level=risk_level,
            base_predictions={
                "rf": round(p_rf, 4),
                "xgb": round(p_xgb, 4),
                "ann": round(p_ann, 4),
            },
            ensemble_weights=self.ensemble_weights.to_dict(),
            sku_id=sku_id or (str(features["sku_id"].iloc[0]) if "sku_id" in features else None),
        )
