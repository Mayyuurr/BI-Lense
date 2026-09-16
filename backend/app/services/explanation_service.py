"""Decision Explanation & Recommendations Service.

Coordinates SHAP explainability and LLaMA natural-language synthesis.
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.explainability.shap_engine import ModelAgnosticSHAPEngine
from app.llm.llama_client import LocalLLaMAClient
from app.llm.explanation import ExplanationSynthesizer, BusinessNarrative
from app.recommendations.engine import RecommendationEngine, ActionableRecommendation
from app.models.database_models import ExplanationLog
from app.core.logging_config import logger


class ExplanationService:
    """Service boundary for SHAP attributions, LLaMA narratives, and recommendations."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db
        self.llm_client = LocalLLaMAClient()
        self.synthesizer = ExplanationSynthesizer(self.llm_client)
        self.recommendation_engine = RecommendationEngine()

    async def generate_explanation(
        self,
        domain: str,
        predicted_value: float,
        target_metric: str,
        shap_feature_importance: Dict[str, float],
        business_score: Optional[float] = None,
    ) -> BusinessNarrative:
        """Generates natural-language business explanation using LLaMA."""
        narrative = await self.synthesizer.explain_prediction(
            domain=domain,
            predicted_value=predicted_value,
            target_metric=target_metric,
            shap_feature_importance=shap_feature_importance,
            business_score=business_score,
        )

        if self.db:
            try:
                log_entry = ExplanationLog(
                    domain=domain,
                    shap_summary=shap_feature_importance,
                    natural_language_explanation=narrative.summary,
                )
                self.db.add(log_entry)
                self.db.commit()
            except Exception as exc:
                logger.warning(f"Failed to log explanation: {exc}")
                if self.db:
                    self.db.rollback()

        return narrative
