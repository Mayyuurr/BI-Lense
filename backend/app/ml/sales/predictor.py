"""Sales & Demand ML Predictor.

Forecasts next-period demand using the hybrid ensemble (RF, XGBoost, ANN).
"""

from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd

from app.ml.base import BaseMLModel
from app.ml.ensemble.optimizer import EnsembleWeights, HybridEnsemblePredictor


@dataclass
class SalesPredictionResult:
    """Encapsulates sales and demand prediction outcomes."""

    predicted_demand: float
    base_predictions: Dict[str, float]
    ensemble_weights: Dict[str, float]
    target_period: str


class SalesDemandPredictor:
    """Inference orchestrator for next-period sales demand forecasting."""

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

    def predict_next_period_demand(
        self,
        features: pd.DataFrame,
        target_period: str = "next_30_days",
    ) -> SalesPredictionResult:
        """Runs base models and combines outputs using optimized ensemble weights."""
        if not (self.rf_model and self.xgb_model and self.ann_model and self.ensemble_weights):
            raise NotImplementedError(
                "Trained models and ensemble weights must be loaded from artifacts."
            )

        pred_rf = float(self.rf_model.predict(features)[0])
        pred_xgb = float(self.xgb_model.predict(features)[0])
        pred_ann = float(self.ann_model.predict(features)[0])

        final_demand = self.ensemble_predictor.predict(
            pred_rf=pred_rf,
            pred_xgb=pred_xgb,
            pred_ann=pred_ann,
        )

        return SalesPredictionResult(
            predicted_demand=final_demand,
            base_predictions={"rf": pred_rf, "xgb": pred_xgb, "ann": pred_ann},
            ensemble_weights=self.ensemble_weights.to_dict(),
            target_period=target_period,
        )
