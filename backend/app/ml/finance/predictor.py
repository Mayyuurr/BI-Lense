"""Finance ML Predictor.

Forecasts probability of operating cash-flow deficit in the next 30-day cycle.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd

from app.ml.base import BaseMLModel
from app.ml.ensemble.optimizer import EnsembleWeights, HybridEnsemblePredictor


@dataclass
class CashFlowDeficitResult:
    """Encapsulates operating cash-flow deficit prediction outcomes."""

    deficit_probability: float
    base_predictions: Dict[str, float]
    ensemble_weights: Dict[str, float]
    forecast_horizon_days: int = 30


class FinanceDeficitPredictor:
    """Inference orchestrator for 30-day operating cash flow risk."""

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

    def predict_deficit_probability(
        self,
        features: pd.DataFrame,
        forecast_horizon_days: int = 30,
    ) -> CashFlowDeficitResult:
        """Estimates probability of cash deficit over next horizon."""
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
        bounded_prob = max(0.0, min(1.0, prob))

        return CashFlowDeficitResult(
            deficit_probability=bounded_prob,
            base_predictions={"rf": pred_rf, "xgb": pred_xgb, "ann": pred_ann},
            ensemble_weights=self.ensemble_weights.to_dict(),
            forecast_horizon_days=forecast_horizon_days,
        )
