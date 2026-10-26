"""Decision Insights & Procurement Restocking Triggers API Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.recommendations.engine import RecommendationEngine, ActionableRecommendation, RestockTrigger
from app.services.explanation_service import ExplanationService
from app.services.prediction_service import PredictionService
from app.services.scoring_service import ScoringService

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


class DashboardSummaryRequest(BaseModel):
    """Optional payload for tailoring full executive dashboard summary."""

    sales_input: Optional[Dict[str, Any]] = Field(
        None,
        description="Features for sales demand forecast.",
        json_schema_extra={
            "example": {
                "sku_id": "SKU-001",
                "unit_price": 120.0,
                "sales_lag_1": 65.0,
                "sales_lag_7": 60.0,
                "sales_lag_30": 58.0,
                "rolling_avg_30": 62.0,
                "discount_rate": 0.08,
                "promotional_flag": 1,
                "day_of_week": 2,
                "month": 6,
                "product_category": "Hardware",
            }
        },
    )
    inventory_input: Optional[Dict[str, Any]] = Field(
        None,
        description="Features for inventory stockout risk.",
        json_schema_extra={
            "example": {
                "sku_id": "SKU-001",
                "current_stock": 45.0,
                "reorder_level": 80.0,
                "safety_stock": 25.0,
                "lead_time_days": 7.0,
                "historical_delivery_delay_days": 1.5,
                "inventory_turnover_ratio": 7.8,
                "predicted_sales_demand": 70.0,
            }
        },
    )
    finance_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Indicators for finance health.",
        json_schema_extra={
            "example": {
                "gross_margin_pct": 34.0,
                "quick_ratio": 1.6,
                "expense_to_revenue_ratio": 0.68,
            }
        },
    )
    hr_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Indicators for employee performance.",
        json_schema_extra={
            "example": {
                "productivity_score": 88.0,
                "retention_rate": 93.0,
                "attendance_rate": 95.0,
            }
        },
    )


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


@router.post("/dashboard-summary", status_code=status.HTTP_200_OK)
async def get_dashboard_summary(
    payload: Optional[DashboardSummaryRequest] = None,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Unified 'one-shot' endpoint demonstrating full backend intelligence in a single call.

    Combines:
    1. Hybrid ML Sales Forecast + Exact Linear SHAP Driver decomposition.
    2. Hybrid ML Inventory Stockout Risk + Procurement Restock Trigger evaluation.
    3. Composite Business Performance Score (Bp) with alert tier & bottleneck attribution.
    4. Executive LLaMA / Deterministic Natural-Language Business Narrative.
    5. Prioritized operational recommendations.
    """
    try:
        pred_service = PredictionService(db=db)
        score_service = ScoringService(db=db)
        expl_service = ExplanationService(db=db)
        rec_engine = RecommendationEngine()

        # 1. Prepare inputs with resilient SME defaults
        default_sales = {
            "sku_id": "SKU-001",
            "unit_price": 120.0,
            "sales_lag_1": 65.0,
            "sales_lag_7": 60.0,
            "sales_lag_30": 58.0,
            "rolling_avg_30": 62.0,
            "discount_rate": 0.08,
            "promotional_flag": 1,
            "day_of_week": 2,
            "month": 6,
            "product_category": "Hardware",
        }
        user_sales = payload.sales_input if (payload and payload.sales_input) else {}
        clean_sales = {k: v for k, v in user_sales.items() if not k.startswith("additionalProp")}
        sales_data = {**default_sales, **clean_sales}

        default_inv = {
            "sku_id": "SKU-001",
            "current_stock": 45.0,
            "reorder_level": 80.0,
            "safety_stock": 25.0,
            "lead_time_days": 7.0,
            "historical_delivery_delay_days": 1.5,
            "inventory_turnover_ratio": 7.8,
            "predicted_sales_demand": 70.0,
        }
        user_inv = payload.inventory_input if (payload and payload.inventory_input) else {}
        clean_inv = {k: v for k, v in user_inv.items() if not k.startswith("additionalProp")}
        inv_data = {**default_inv, **clean_inv}

        default_fin = {
            "gross_margin_pct": 34.0,
            "quick_ratio": 1.6,
            "expense_to_revenue_ratio": 0.68,
        }
        user_fin = payload.finance_data if (payload and payload.finance_data) else {}
        clean_fin = {k: v for k, v in user_fin.items() if not k.startswith("additionalProp")}
        fin_data = {**default_fin, **clean_fin}

        default_hr = {
            "productivity_score": 88.0,
            "retention_rate": 93.0,
            "attendance_rate": 95.0,
        }
        user_hr = payload.hr_data if (payload and payload.hr_data) else {}
        clean_hr = {k: v for k, v in user_hr.items() if not k.startswith("additionalProp")}
        hr_data = {**default_hr, **clean_hr}

        # 2. Run Hybrid ML Predictions with SHAP
        sales_pred = pred_service.predict_sales_demand(sales_data, include_explanation=True)
        inv_pred = pred_service.predict_inventory_stockout(inv_data, include_explanation=True)

        # 3. Evaluate Procurement Restock Trigger
        restock_res = rec_engine.evaluate_procurement_restock(
            sku_id=inv_data.get("sku_id", "SKU-001"),
            product_name="Primary Catalog SKU",
            current_stock=float(inv_data.get("current_stock", 45.0)),
            reorder_point=float(inv_data.get("reorder_level", 80.0)),
            safety_stock=float(inv_data.get("safety_stock", 25.0)),
            lead_time_days=int(inv_data.get("lead_time_days", 7)),
            daily_demand=float(sales_pred.get("predicted_demand", 65.0)) / 30.0,
        )

        # 4. Compute Composite Bp Business Score
        bp_result = score_service.compute_scores(
            sales_data={"actual_sales": sales_pred.get("predicted_demand", 100.0)},
            inventory_data={"stockout_probability": inv_pred.get("stockout_probability", 0.20)},
            finance_data=fin_data,
            hr_data=hr_data,
        )

        # 5. Generate Executive Narrative
        sales_expl = sales_pred.get("explanation", {})
        top_pos = sales_expl.get("top_positive_drivers", [])
        top_neg = sales_expl.get("top_negative_drivers", [])

        narrative = await expl_service.generate_explanation(
            domain="sales",
            predicted_value=float(sales_pred.get("predicted_demand", 0.0)),
            target_metric="next_period_demand",
            top_positive_drivers=top_pos,
            top_negative_drivers=top_neg,
            business_score=bp_result.bp_score,
            alert_tier=bp_result.alert_tier,
            primary_bottleneck=bp_result.metadata.get("primary_bottleneck"),
        )

        # 6. Prioritized Recommendations
        recs = rec_engine.generate_recommendations(
            scores={
                "sales": bp_result.sales_score,
                "inventory": bp_result.inventory_score,
                "finance": bp_result.finance_score,
                "employee": bp_result.employee_score,
            },
            predictions={
                "sales_demand": sales_pred.get("predicted_demand"),
                "stockout_probability": inv_pred.get("stockout_probability"),
            },
        )

        return {
            "status": "success",
            "business_health": {
                "bp_score": bp_result.bp_score,
                "alert_tier": bp_result.alert_tier,
                "primary_bottleneck": bp_result.metadata.get("primary_bottleneck"),
                "key_strength": bp_result.metadata.get("key_strength"),
                "domain_scores": {
                    "sales": bp_result.sales_score,
                    "inventory": bp_result.inventory_score,
                    "finance": bp_result.finance_score,
                    "employee": bp_result.employee_score,
                },
            },
            "sales_forecast": {
                "sku_id": sales_pred.get("sku_id"),
                "predicted_demand": sales_pred.get("predicted_demand"),
                "model_weights": sales_pred.get("ensemble_weights"),
                "top_positive_driver": top_pos[0] if top_pos else None,
                "top_negative_driver": top_neg[0] if top_neg else None,
            },
            "inventory_risk": {
                "sku_id": inv_pred.get("sku_id"),
                "stockout_probability": inv_pred.get("stockout_probability"),
                "risk_level": inv_pred.get("risk_level"),
                "restock_triggered": restock_res.is_triggered,
                "suggested_order_quantity": restock_res.suggested_order_quantity,
            },
            "executive_narrative": narrative.to_dict(),
            "recommendations": [
                {
                    "domain": r.domain,
                    "title": r.title,
                    "urgency": r.urgency.value,
                    "suggested_action": r.suggested_action,
                }
                for r in recs
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
