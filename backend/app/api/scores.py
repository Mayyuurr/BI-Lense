"""Business Scores and Composite Bp API Router."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/scores", tags=["Business Scores"])


class ScoreComputeRequest(BaseModel):
    """Payload for domain performance score calculation."""

    sales_data: Optional[Dict[str, Any]] = None
    inventory_data: Optional[Dict[str, Any]] = None
    finance_data: Optional[Dict[str, Any]] = None
    hr_data: Optional[Dict[str, Any]] = None


class ScoreResponse(BaseModel):
    """Response containing individual domain scores and aggregate Bp."""

    bp_score: float
    sales_score: Optional[float] = None
    inventory_score: Optional[float] = None
    finance_score: Optional[float] = None
    employee_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/compute", response_model=ScoreResponse, status_code=status.HTTP_200_OK)
def compute_scores(
    payload: ScoreComputeRequest,
    db: Session = Depends(get_db),
) -> ScoreResponse:
    """Calculates domain scores (S, I, F, E) and composite Business Performance Score (Bp)."""
    try:
        service = ScoringService(db=db)
        result = service.compute_scores(
            sales_data=payload.sales_data,
            inventory_data=payload.inventory_data,
            finance_data=payload.finance_data,
            hr_data=payload.hr_data,
        )
        return ScoreResponse(
            bp_score=result.bp_score,
            sales_score=result.sales_score,
            inventory_score=result.inventory_score,
            finance_score=result.finance_score,
            employee_score=result.employee_score,
            metadata=result.metadata,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
