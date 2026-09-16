"""Decision Insights & Procurement Restocking Triggers API Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.recommendations.engine import RecommendationEngine, ActionableRecommendation, RestockTrigger

router = APIRouter(prefix="/insights", tags=["Decision Insights & Alerts"])


class RestockCheckRequest(BaseModel):
    """Payload for evaluating procurement restocking triggers."""

    sku_id: str
    product_name: str
    current_stock: float
    reorder_point: Optional[float] = None
    safety_stock: float = 0.0
    lead_time_days: int = 7
    daily_demand: float = 0.0


class RestockCheckResponse(BaseModel):
    """Result of restocking trigger evaluation."""

    sku_id: str
    product_name: str
    current_stock: float
    reorder_point: float
    suggested_order_quantity: float
    is_triggered: bool


class RecommendationsRequest(BaseModel):
    """Payload for generating prioritized business recommendations."""

    scores: Dict[str, Optional[float]]
    predictions: Dict[str, Optional[float]] = {}


@router.post("/procurement/restock-check", response_model=RestockCheckResponse, status_code=status.HTTP_200_OK)
def check_restock(
    payload: RestockCheckRequest,
    db: Session = Depends(get_db),
) -> RestockCheckResponse:
    """Evaluates deterministic restocking-trigger logic for procurement."""
    engine = RecommendationEngine()
    result = engine.evaluate_procurement_restock(
        sku_id=payload.sku_id,
        product_name=payload.product_name,
        current_stock=payload.current_stock,
        reorder_point=payload.reorder_point or 0.0,
        safety_stock=payload.safety_stock,
        lead_time_days=payload.lead_time_days,
        daily_demand=payload.daily_demand,
    )
    return RestockCheckResponse(
        sku_id=result.sku_id,
        product_name=result.product_name,
        current_stock=result.current_stock,
        reorder_point=result.reorder_point,
        suggested_order_quantity=result.suggested_order_quantity,
        is_triggered=result.is_triggered,
    )


@router.post("/recommendations", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
def get_recommendations(
    payload: RecommendationsRequest,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Synthesizes domain scores and predictions into actionable SME recommendations."""
    engine = RecommendationEngine()
    recs = engine.generate_recommendations(
        scores=payload.scores,
        predictions=payload.predictions,
    )
    return [
        {
            "domain": r.domain,
            "title": r.title,
            "description": r.description,
            "urgency": r.urgency.value,
            "trigger_reason": r.trigger_reason,
            "suggested_action": r.suggested_action,
        }
        for r in recs
    ]
