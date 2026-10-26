"""Business Scores and Composite Bp API Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/scores", tags=["Business Scores"])


class ScoreComputeRequest(BaseModel):
    """Payload for domain performance score calculation."""

    sales_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Sales domain indicators (e.g. actual_sales, target_sales, discount_rate, growth_mom)",
    )
    inventory_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Inventory domain indicators (e.g. stockout_probability, inventory_turnover_ratio, current_stock)",
    )
    finance_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Finance domain indicators (e.g. gross_margin_pct, quick_ratio, expense_to_revenue_ratio)",
    )
    hr_data: Optional[Dict[str, Any]] = Field(
        None,
        description="HR domain indicators (e.g. productivity_score, retention_rate, attendance_rate)",
    )


class ScoreResponse(BaseModel):
    """Response containing individual domain scores and aggregate Bp."""

    bp_score: float
    sales_score: Optional[float] = None
    inventory_score: Optional[float] = None
    finance_score: Optional[float] = None
    employee_score: Optional[float] = None
    alert_tier: Optional[str] = None
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
            alert_tier=result.alert_tier,
            metadata=result.metadata,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/latest", status_code=status.HTTP_200_OK)
def get_latest_score(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieves the most recent business score record from the database."""
    try:
        service = ScoringService(db=db)
        record = service.get_latest_score()
        if not record:
            return {"message": "No score records available yet", "status": "empty"}
        return record
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/history", status_code=status.HTTP_200_OK)
def get_score_history(
    limit: int = Query(30, ge=1, le=100, description="Max number of historical records"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Retrieves historical score records for time-series trend analysis."""
    try:
        service = ScoringService(db=db)
        return service.get_score_history(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
