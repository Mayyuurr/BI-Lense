"""Domain Predictions API Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["Predictions"])


class GenericPredictionRequest(BaseModel):
    """Payload for generic domain prediction request."""

    domain: str = Field(..., description="Target SME domain: sales, inventory, finance, hr")
    features: Dict[str, Any] = Field(..., description="Dictionary of raw feature values")
    target_period: Optional[str] = Field("next_30_days", description="Forecast timeframe")


class SalesPredictionInput(BaseModel):
    """Structured feature payload for Sales Demand forecasting."""

    sku_id: str = Field(..., json_schema_extra={"example": "SKU-001"})
    unit_price: float = Field(..., json_schema_extra={"example": 120.0})
    sales_lag_1: float = Field(..., json_schema_extra={"example": 65.0})
    sales_lag_7: float = Field(..., json_schema_extra={"example": 60.0})
    sales_lag_30: float = Field(..., json_schema_extra={"example": 58.0})
    rolling_avg_30: float = Field(..., json_schema_extra={"example": 62.0})
    discount_rate: float = Field(0.0, json_schema_extra={"example": 0.10})
    promotional_flag: int = Field(0, json_schema_extra={"example": 1})
    day_of_week: int = Field(2, json_schema_extra={"example": 2})
    month: int = Field(6, json_schema_extra={"example": 6})
    product_category: str = Field("Hardware", json_schema_extra={"example": "Hardware"})


class InventoryPredictionInput(BaseModel):
    """Structured feature payload for Inventory Stockout Risk estimation."""

    sku_id: str = Field(..., json_schema_extra={"example": "SKU-001"})
    current_stock: float = Field(..., json_schema_extra={"example": 45.0})
    reorder_level: float = Field(..., json_schema_extra={"example": 80.0})
    safety_stock: float = Field(..., json_schema_extra={"example": 25.0})
    lead_time_days: float = Field(..., json_schema_extra={"example": 7.0})
    historical_delivery_delay_days: float = Field(..., json_schema_extra={"example": 1.5})
    inventory_turnover_ratio: float = Field(..., json_schema_extra={"example": 8.2})
    predicted_sales_demand: float = Field(..., json_schema_extra={"example": 70.0})


@router.post("/run", status_code=status.HTTP_200_OK)
def run_prediction(
    payload: GenericPredictionRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Executes hybrid ensemble prediction pipeline for a given domain."""
    try:
        service = PredictionService(db=db)
        return service.get_domain_prediction(
            domain=payload.domain,
            input_data=payload.features,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/sales", status_code=status.HTTP_200_OK)
def predict_sales_demand(
    payload: SalesPredictionInput,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Direct endpoint for sales demand hybrid ensemble forecasting."""
    try:
        service = PredictionService(db=db)
        return service.predict_sales_demand(input_data=payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/inventory", status_code=status.HTTP_200_OK)
def predict_inventory_stockout(
    payload: InventoryPredictionInput,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Direct endpoint for inventory stockout probability estimation."""
    try:
        service = PredictionService(db=db)
        return service.predict_inventory_stockout(input_data=payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
