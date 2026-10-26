"""SHAP Explainability and LLaMA Narrative Explanations API Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.explanation_service import ExplanationService

router = APIRouter(prefix="/explanations", tags=["Explanations"])


class ExplanationRequest(BaseModel):
    """Payload for requesting LLaMA natural-language explanation of prediction/SHAP."""

    domain: str = Field(..., description="Target SME domain: sales, inventory, finance, hr")
    predicted_value: float = Field(..., description="Predicted numerical value (e.g. demand units or stockout probability)")
    target_metric: str = Field(..., description="Name of the forecast metric (e.g. next_period_demand, stockout_probability)")
    top_positive_drivers: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Top positive SHAP driver objects (from /predictions/explain)",
    )
    top_negative_drivers: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Top negative SHAP driver objects (from /predictions/explain)",
    )
    shap_feature_importance: Optional[Dict[str, float]] = Field(
        None,
        description="Flat feature-to-SHAP attribution dictionary",
    )
    business_score: Optional[float] = Field(
        None,
        description="Composite Bp or domain score (0 - 100)",
    )
    alert_tier: Optional[str] = Field(
        None,
        description="Alert tier: OPTIMAL, STABLE, WATCHLIST, CRITICAL",
    )
    primary_bottleneck: Optional[str] = Field(
        None,
        description="Identified operational bottleneck domain (e.g. inventory)",
    )


class ExplanationResponse(BaseModel):
    """Structured executive narrative and key driver response."""

    domain: str
    headline: str
    summary: str
    key_drivers: List[str]
    suggested_actions: List[str]
    alert_tier: str
    source: str = Field(..., description="'llm_generated' or 'deterministic_fallback'")
    latency_ms: Optional[float] = None
    raw_response: Optional[str] = None


@router.post("/generate", response_model=ExplanationResponse, status_code=status.HTTP_200_OK)
async def generate_explanation(
    payload: ExplanationRequest,
    db: Session = Depends(get_db),
) -> ExplanationResponse:
    """Generates natural-language business explanation using LLaMA narrative synthesis or fallback."""
    try:
        service = ExplanationService(db=db)
        narrative = await service.generate_explanation(
            domain=payload.domain,
            predicted_value=payload.predicted_value,
            target_metric=payload.target_metric,
            shap_feature_importance=payload.shap_feature_importance,
            top_positive_drivers=payload.top_positive_drivers,
            top_negative_drivers=payload.top_negative_drivers,
            business_score=payload.business_score,
            alert_tier=payload.alert_tier,
            primary_bottleneck=payload.primary_bottleneck,
        )
        return ExplanationResponse(
            domain=narrative.domain,
            headline=narrative.headline,
            summary=narrative.summary,
            key_drivers=narrative.key_drivers,
            suggested_actions=narrative.suggested_actions,
            alert_tier=narrative.alert_tier,
            source=narrative.source,
            latency_ms=narrative.latency_ms,
            raw_response=narrative.raw_response,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/llm-status", status_code=status.HTTP_200_OK)
async def get_llm_status(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Checks remote Tailscale / AWS / local LLaMA connectivity, latency, and available models."""
    try:
        service = ExplanationService(db=db)
        return await service.check_llm_status()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
