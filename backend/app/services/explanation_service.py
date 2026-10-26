"""Decision Explanation & Recommendations Service.

Coordinates SHAP explainability, remote/local LLaMA natural-language synthesis,
rule-based fallbacks, and audit logging.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.llm.explanation import BusinessNarrative, ExplanationSynthesizer
from app.llm.llama_client import LocalLLaMAClient
from app.models.database_models import ExplanationLog
from app.recommendations.engine import RecommendationEngine


class ExplanationService:
    """Service boundary for SHAP attributions, LLaMA narratives, and recommendations."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db
        self.llm_client = LocalLLaMAClient()
        self.synthesizer = ExplanationSynthesizer(self.llm_client)
        self.recommendation_engine = RecommendationEngine()

    async def check_llm_status(self) -> Dict[str, Any]:
        """Performs ping and connectivity diagnosis against remote Tailscale/AWS/local LLaMA."""
        return await self.llm_client.check_health()

    async def generate_explanation(
        self,
        domain: str,
        predicted_value: float,
        target_metric: str,
        shap_feature_importance: Optional[Dict[str, float]] = None,
        top_positive_drivers: Optional[List[Dict[str, Any]]] = None,
        top_negative_drivers: Optional[List[Dict[str, Any]]] = None,
        business_score: Optional[float] = None,
        alert_tier: Optional[str] = None,
        primary_bottleneck: Optional[str] = None,
    ) -> BusinessNarrative:
        """Generates natural-language business explanation using LLaMA or deterministic fallback."""
        narrative = await self.synthesizer.explain_prediction(
            domain=domain,
            predicted_value=predicted_value,
            target_metric=target_metric,
            shap_feature_importance=shap_feature_importance,
            top_positive_drivers=top_positive_drivers,
            top_negative_drivers=top_negative_drivers,
            business_score=business_score,
            alert_tier=alert_tier,
            primary_bottleneck=primary_bottleneck,
        )

        # Audit log in database if DB is reachable
        if self.db is not None:
            try:
                log_entry = ExplanationLog(
                    domain=domain,
                    shap_summary={
                        "top_positive": top_positive_drivers or [],
                        "top_negative": top_negative_drivers or [],
                        "importance_dict": shap_feature_importance or {},
                    },
                    natural_language_explanation=narrative.summary,
                )
                self.db.add(log_entry)
                self.db.commit()
            except Exception as exc:
                logger.warning(f"Failed to log explanation in database: {exc}")
                if self.db:
                    self.db.rollback()

        return narrative
