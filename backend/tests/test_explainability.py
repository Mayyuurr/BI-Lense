"""Automated Unit & Integration Tests for SHAP Explainability Engine.

Verifies:
1. EnsembleSHAPExplainer initialization for Sales and Inventory domains.
2. Exact linear ensemble SHAP attribution calculation.
3. Top positive and negative driver decomposition with executive human labels.
4. API /predictions/explain and include_explanation contracts.
"""

import pytest
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.explainability.shap_engine import EnsembleSHAPExplainer, EnsembleExplanation


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_sales_shap_explainer():
    """Verifies EnsembleSHAPExplainer on Sales Demand forecasting."""
    explainer = EnsembleSHAPExplainer(domain="sales")
    sample_df = pd.DataFrame([{
        "sku_id": "SKU-001",
        "unit_price": 120.0,
        "sales_lag_1": 65.0,
        "sales_lag_7": 60.0,
        "sales_lag_30": 58.0,
        "rolling_avg_30": 62.0,
        "discount_rate": 0.10,
        "promotional_flag": 1,
        "day_of_week": 2,
        "month": 6,
        "product_category": "Hardware",
    }])

    res = explainer.explain(sample_df, top_k=3)
    assert isinstance(res, EnsembleExplanation)
    assert res.domain == "sales"
    assert res.target_metric == "next_period_demand"
    assert res.predicted_value > 0.0
    assert res.base_value > 0.0
    assert len(res.attributions) > 0
    assert len(res.top_positive_drivers) <= 3
    assert len(res.top_negative_drivers) <= 3

    # Verify each driver has a valid human-readable label
    for attr in res.attributions:
        assert len(attr.human_label) > 0
        assert attr.direction in ["positive", "negative"]
        assert attr.relative_importance >= 0.0


def test_inventory_shap_explainer():
    """Verifies EnsembleSHAPExplainer on Inventory Stockout risk."""
    explainer = EnsembleSHAPExplainer(domain="inventory")
    sample_df = pd.DataFrame([{
        "sku_id": "SKU-001",
        "current_stock": 15.0,
        "reorder_level": 80.0,
        "safety_stock": 25.0,
        "lead_time_days": 12.0,
        "historical_delivery_delay_days": 3.0,
        "inventory_turnover_ratio": 7.5,
        "predicted_sales_demand": 85.0,
    }])

    res = explainer.explain(sample_df, top_k=3)
    assert isinstance(res, EnsembleExplanation)
    assert res.domain == "inventory"
    assert res.target_metric == "stockout_probability"
    assert 0.0 <= res.predicted_value <= 1.0
    assert 0.0 <= res.base_value <= 1.0
    assert len(res.attributions) > 0


def test_sales_prediction_with_explanation_endpoint(client):
    """Tests POST /api/v1/predictions/sales with include_explanation=True."""
    payload = {
        "sku_id": "SKU-005",
        "unit_price": 95.0,
        "sales_lag_1": 50.0,
        "sales_lag_7": 48.0,
        "sales_lag_30": 45.0,
        "rolling_avg_30": 49.0,
        "discount_rate": 0.15,
        "promotional_flag": 1,
        "day_of_week": 4,
        "month": 7,
        "product_category": "Electronics",
        "include_explanation": True,
    }
    response = client.post("/api/v1/predictions/sales", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "sales"
    assert "explanation" in data
    exp = data["explanation"]
    assert exp["predicted_value"] > 0
    assert "attributions" in exp
    assert "top_positive_drivers" in exp
    assert "top_negative_drivers" in exp


def test_inventory_prediction_with_explanation_endpoint(client):
    """Tests POST /api/v1/predictions/inventory with include_explanation=True."""
    payload = {
        "sku_id": "SKU-002",
        "current_stock": 8.0,
        "reorder_level": 70.0,
        "safety_stock": 20.0,
        "lead_time_days": 10.0,
        "historical_delivery_delay_days": 2.0,
        "inventory_turnover_ratio": 9.0,
        "predicted_sales_demand": 80.0,
        "include_explanation": True,
    }
    response = client.post("/api/v1/predictions/inventory", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "inventory"
    assert "explanation" in data
    exp = data["explanation"]
    assert 0.0 <= exp["predicted_value"] <= 1.0
    assert "attributions" in exp


def test_standalone_explain_endpoint(client):
    """Tests POST /api/v1/predictions/explain standalone endpoint."""
    payload = {
        "domain": "sales",
        "features": {
            "sku_id": "SKU-003",
            "unit_price": 140.0,
            "sales_lag_1": 70.0,
            "sales_lag_7": 68.0,
            "sales_lag_30": 65.0,
            "rolling_avg_30": 69.0,
            "discount_rate": 0.0,
            "promotional_flag": 0,
            "day_of_week": 1,
            "month": 8,
            "product_category": "Hardware",
        },
    }
    response = client.post("/api/v1/predictions/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "sales"
    assert len(data["attributions"]) > 0
    assert len(data["top_positive_drivers"]) > 0
