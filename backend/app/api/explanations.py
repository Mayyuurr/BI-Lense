"""SHAP Explainability and LLaMA Narrative Explanations API Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.explanation_service import ExplanationService

router = APIRouter(prefix="/explanations", tags=["Explanations"])


class ExplanationRequest(BaseModel):
    """Payload for requesting LLaMA natural-language explanation of prediction/SHAP."""

    domain: str
    predicted_value: float
    target_metric: str
    shap_feature_importance: Dict[str, float]
    business_score: Optional[float] = None


class ExplanationResponse(BaseModel):
    """Structured executive narrative and key driver response."""

    domain: str
    headline: str
    summary: str
    key_drivers: List[str]
    suggested_actions: List[str]
    raw_response: Optional[str] = None


@router.post("/generate", response_model=ExplanationResponse, status_code=status.HTTP_200_OK)
async def generate_explanation(
    payload: ExplanationRequest,
    db: Session = Depends(get_db),
) -> ExplanationResponse:
    """Generates natural-language business explanation using LLaMA narrative synthesis."""
    try:
        service = ExplanationService(db=db)
        narrative = await service.generate_explanation(
            domain=payload.domain,
            predicted_value=payload.predicted_value,
            target_metric=payload.target_metric,
            shap_feature_importance=payload.shap_feature_importance,
            business_score=payload.business_score,
        )
        return ExplanationResponse(
            domain=narrative.domain,
            headline=narrative.headline,
            summary=narrative.summary,
            key_drivers=narrative.key_drivers,
            suggested_actions=narrative.suggested_actions,
            raw_response=narrative.raw_response,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
