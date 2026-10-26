"""Domain Predictions & Explainability API Router."""

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
    include_explanation: bool = Field(False, description="Whether to include exact linear ensemble SHAP attributions")


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
    include_explanation: bool = Field(False, json_schema_extra={"example": True})


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
    include_explanation: bool = Field(False, json_schema_extra={"example": True})


class PredictionExplainRequest(BaseModel):
    """Payload for requesting standalone SHAP explanation."""

    domain: str = Field(..., description="Target SME domain: sales, inventory")
    features: Dict[str, Any] = Field(..., description="Feature input payload")


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
            include_explanation=payload.include_explanation,
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
        input_data = payload.model_dump()
        include_explanation = input_data.pop("include_explanation", False)
        return service.predict_sales_demand(
            input_data=input_data,
            include_explanation=include_explanation,
        )
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
        input_data = payload.model_dump()
        include_explanation = input_data.pop("include_explanation", False)
        return service.predict_inventory_stockout(
            input_data=input_data,
            include_explanation=include_explanation,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/explain", status_code=status.HTTP_200_OK)
def explain_prediction(
    payload: PredictionExplainRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Computes exact linear ensemble SHAP attributions and ranked business drivers."""
    try:
        service = PredictionService(db=db)
        return service.explain_domain_prediction(
            domain=payload.domain,
            input_data=payload.features,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
