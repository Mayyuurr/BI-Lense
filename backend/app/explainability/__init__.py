"""Model Explainability Package.

Provides exact linear ensemble SHAP attributions, driver decomposition,
and human-readable explanations.
"""

from app.explainability.shap_engine import (
    EnsembleExplanation,
    EnsembleSHAPExplainer,
    FeatureAttribution,
    FEATURE_HUMAN_LABELS,
    SHAPExplanationResult,
    BaseSHAPEngine,
    TreeSHAPEngine,
    ModelAgnosticSHAPEngine,
)

__all__ = [
    "EnsembleExplanation",
    "EnsembleSHAPExplainer",
    "FeatureAttribution",
    "FEATURE_HUMAN_LABELS",
    "SHAPExplanationResult",
    "BaseSHAPEngine",
    "TreeSHAPEngine",
    "ModelAgnosticSHAPEngine",
]
