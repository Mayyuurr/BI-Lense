"""Domain Predictions API Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["Predictions"])


class PredictionRequest(BaseModel):
    """Payload for domain prediction request."""

    domain: str  # sales, inventory, finance, hr
    features: Dict[str, Any]
    target_metric: Optional[str] = None


class PredictionResponse(BaseModel):
    """Standard response model for prediction requests."""

    domain: str
    status: str
    message: str
    features_received: List[str]


@router.post("/run", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def run_prediction(
    payload: PredictionRequest,
    db: Session = Depends(get_db),
) -> PredictionResponse:
    """Executes hybrid ensemble prediction pipeline for a given domain."""
    try:
        service = PredictionService(db=db)
        result = service.get_domain_prediction(
            domain=payload.domain,
            input_data=payload.features,
        )
        return PredictionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
