"""HR & Productivity ML Predictor.

Forecasts projected task delay OR backlog probability using the hybrid ensemble.
NOTE: The exact HR target metric is pending research finalization.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd

from app.ml.base import BaseMLModel
from app.ml.ensemble.optimizer import EnsembleWeights, HybridEnsemblePredictor


@dataclass
class HRPredictionResult:
    """Encapsulates HR/Productivity prediction outcomes."""

    predicted_value: float
    target_metric: str  # e.g., "task_delay_days" or "backlog_probability"
    base_predictions: Dict[str, float]
    ensemble_weights: Dict[str, float]


class HRPredictor:
    """Inference orchestrator for HR and team productivity metrics."""

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

    def predict(
        self,
        features: pd.DataFrame,
        target_metric: str = "task_delay_or_backlog",
    ) -> HRPredictionResult:
        """Predicts HR productivity risk metric."""
        if not (self.rf_model and self.xgb_model and self.ann_model and self.ensemble_weights):
            raise NotImplementedError(
                "Trained models and ensemble weights must be loaded from artifacts."
            )

        pred_rf = float(self.rf_model.predict(features)[0])
        pred_xgb = float(self.xgb_model.predict(features)[0])
        pred_ann = float(self.ann_model.predict(features)[0])

        val = self.ensemble_predictor.predict(
            pred_rf=pred_rf,
            pred_xgb=pred_xgb,
            pred_ann=pred_ann,
        )

        return HRPredictionResult(
            predicted_value=val,
            target_metric=target_metric,
            base_predictions={"rf": pred_rf, "xgb": pred_xgb, "ann": pred_ann},
            ensemble_weights=self.ensemble_weights.to_dict(),
        )
