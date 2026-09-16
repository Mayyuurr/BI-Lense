"""Hybrid ML Ensemble Optimization and Aggregation.

Implements the constrained optimization formulation:
    Y_hat = w_RF * Y_hat_RF + w_XGB * Y_hat_XGB + w_ANN * Y_hat_ANN
Subject to:
    w_RF + w_XGB + w_ANN = 1
    w_i >= 0  for all i in {RF, XGB, ANN}
"""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
from scipy.optimize import minimize


@dataclass
class EnsembleWeights:
    """Represents the optimal weights for the hybrid base models."""

    w_rf: float
    w_xgb: float
    w_ann: float

    def validate(self) -> bool:
        """Ensures weights sum to 1.0 within numerical precision and are non-negative."""
        is_non_negative = self.w_rf >= 0 and self.w_xgb >= 0 and self.w_ann >= 0
        sums_to_one = np.isclose(self.w_rf + self.w_xgb + self.w_ann, 1.0, atol=1e-3)
        return bool(is_non_negative and sums_to_one)

    def to_dict(self) -> Dict[str, float]:
        return {
            "w_rf": self.w_rf,
            "w_xgb": self.w_xgb,
            "w_ann": self.w_ann,
        }


class EnsembleOptimizer:
    """Optimizes ensemble weights via constrained validation-loss minimization."""

    def optimize_weights(
        self,
        y_true: np.ndarray,
        y_pred_rf: np.ndarray,
        y_pred_xgb: np.ndarray,
        y_pred_ann: np.ndarray,
    ) -> EnsembleWeights:
        """Finds optimal weights [w_rf, w_xgb, w_ann] minimizing Mean Squared Error (MSE)

        on a validation dataset, subject to sum(w) = 1 and w_i >= 0.
        """
        predictions_matrix = np.column_stack([y_pred_rf, y_pred_xgb, y_pred_ann])

        def objective(weights: np.ndarray) -> float:
            y_ensemble = np.dot(predictions_matrix, weights)
            return float(np.mean((y_true - y_ensemble) ** 2))

        # Initial equal weights
        init_weights = np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])

        # Bounds: 0 <= w_i <= 1
        bounds = [(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)]

        # Constraint: sum(w_i) - 1 = 0
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

        result = minimize(
            objective,
            init_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        if not result.success:
            # Fallback to equal weights if solver fails
            return EnsembleWeights(w_rf=1/3, w_xgb=1/3, w_ann=1/3)

        optimal_w = result.x
        return EnsembleWeights(
            w_rf=float(optimal_w[0]),
            w_xgb=float(optimal_w[1]),
            w_ann=float(optimal_w[2]),
        )


class HybridEnsemblePredictor:
    """Applies optimized ensemble weights to combine base model predictions."""

    def __init__(self, weights: Optional[EnsembleWeights] = None) -> None:
        self.weights = weights

    def predict(
        self,
        pred_rf: float,
        pred_xgb: float,
        pred_ann: float,
        weights: Optional[EnsembleWeights] = None,
    ) -> float:
        """Calculates Y_hat = w_RF * Y_RF + w_XGB * Y_XGB + w_ANN * Y_ANN."""
        active_weights = weights or self.weights
        if not active_weights:
            raise ValueError("Ensemble weights must be configured before prediction.")

        return (
            active_weights.w_rf * pred_rf
            + active_weights.w_xgb * pred_xgb
            + active_weights.w_ann * pred_ann
        )
