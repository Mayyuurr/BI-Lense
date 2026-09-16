"""Inventory ML Predictor.

Estimates stockout probability before supplier delivery using the hybrid ensemble.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd

from app.ml.base import BaseMLModel
from app.ml.ensemble.optimizer import EnsembleWeights, HybridEnsemblePredictor


@dataclass
class StockoutPredictionResult:
    """Encapsulates stockout probability prediction outcomes."""

    stockout_probability: float
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
        ensemble_weights: Optional[EnsembleWeights] = None,
    ) -> None:
        self.rf_model = rf_model
        self.xgb_model = xgb_model
        self.ann_model = ann_model
        self.ensemble_weights = ensemble_weights
        self.ensemble_predictor = HybridEnsemblePredictor(weights=ensemble_weights)

    def predict_stockout_probability(
        self,
        features: pd.DataFrame,
        sku_id: Optional[str] = None,
    ) -> StockoutPredictionResult:
        """Estimates stockout probability before supplier delivery."""
        if not (self.rf_model and self.xgb_model and self.ann_model and self.ensemble_weights):
            raise NotImplementedError(
                "Trained models and ensemble weights must be loaded from artifacts."
            )

        pred_rf = float(self.rf_model.predict(features)[0])
        pred_xgb = float(self.xgb_model.predict(features)[0])
        pred_ann = float(self.ann_model.predict(features)[0])

        prob = self.ensemble_predictor.predict(
            pred_rf=pred_rf,
            pred_xgb=pred_xgb,
            pred_ann=pred_ann,
        )
        # Ensure probability bounds [0.0, 1.0]
        bounded_prob = max(0.0, min(1.0, prob))

        return StockoutPredictionResult(
            stockout_probability=bounded_prob,
            base_predictions={"rf": pred_rf, "xgb": pred_xgb, "ann": pred_ann},
            ensemble_weights=self.ensemble_weights.to_dict(),
            sku_id=sku_id,
        )
