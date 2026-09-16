"""SHAP (SHapley Additive exPlanations) Engine.

Computes feature contributions for base models and ensemble components
to ensure model transparency and explainability.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


@dataclass
class SHAPExplanationResult:
    """Encapsulates SHAP feature importance and baseline values."""

    domain: str
    base_value: float
    feature_names: List[str]
    shap_values: Dict[str, float]
    top_positive_drivers: List[str]
    top_negative_drivers: List[str]


class BaseSHAPEngine(ABC):
    """Abstract interface for SHAP explainability engines."""

    @abstractmethod
    def explain_instance(
        self,
        features: pd.DataFrame,
        domain: str = "general",
    ) -> SHAPExplanationResult:
        """Computes SHAP values for a single sample instance."""
        pass


class TreeSHAPEngine(BaseSHAPEngine):
    """Computes TreeSHAP for tree-based ensemble members (RF, XGBoost)."""

    def __init__(self, tree_model: Optional[Any] = None) -> None:
        self.tree_model = tree_model

    def explain_instance(
        self,
        features: pd.DataFrame,
        domain: str = "general",
    ) -> SHAPExplanationResult:
        """Computes TreeSHAP feature attributions."""
        if not self.tree_model:
            raise NotImplementedError("Tree model must be provided for TreeSHAP.")

        # Placeholder contract returning standard schema
        feature_names = list(features.columns)
        dummy_shap = {feat: 0.0 for feat in feature_names}

        return SHAPExplanationResult(
            domain=domain,
            base_value=0.0,
            feature_names=feature_names,
            shap_values=dummy_shap,
            top_positive_drivers=[],
            top_negative_drivers=[],
        )


class ModelAgnosticSHAPEngine(BaseSHAPEngine):
    """Computes KernelSHAP or permutation-based feature attribution for any model."""

    def __init__(self, predict_fn: Optional[Any] = None) -> None:
        self.predict_fn = predict_fn

    def explain_instance(
        self,
        features: pd.DataFrame,
        domain: str = "general",
    ) -> SHAPExplanationResult:
        """Computes KernelSHAP feature attributions."""
        if not self.predict_fn:
            raise NotImplementedError("Prediction function required for ModelAgnosticSHAP.")

        feature_names = list(features.columns)
        dummy_shap = {feat: 0.0 for feat in feature_names}

        return SHAPExplanationResult(
            domain=domain,
            base_value=0.0,
            feature_names=feature_names,
            shap_values=dummy_shap,
            top_positive_drivers=[],
            top_negative_drivers=[],
        )
