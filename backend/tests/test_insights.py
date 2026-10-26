"""Test Suite for Decision Insights, Procurement Restock Triggers, and Dashboard Summary."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_procurement_restock_check_endpoint(client: TestClient) -> None:
    """Verifies POST /api/v1/insights/procurement/restock-check."""
    # Case 1: Stock is below reorder point -> Should trigger restock
    payload_triggered = {
        "sku_id": "SKU-001",
        "product_name": "Premium Tool",
        "current_stock": 15.0,
        "reorder_point": 50.0,
        "safety_stock": 20.0,
        "lead_time_days": 7,
        "daily_demand": 5.0,
    }
    resp = client.post("/api/v1/insights/procurement/restock-check", json=payload_triggered)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sku_id"] == "SKU-001"
    assert data["is_triggered"] is True
    assert data["suggested_order_quantity"] > 0

    # Case 2: Stock is well above reorder point -> Should NOT trigger
    payload_safe = {
        "sku_id": "SKU-002",
        "product_name": "Standard Tool",
        "current_stock": 150.0,
        "reorder_point": 50.0,
        "safety_stock": 20.0,
        "lead_time_days": 7,
        "daily_demand": 5.0,
    }
    resp_safe = client.post("/api/v1/insights/procurement/restock-check", json=payload_safe)
    assert resp_safe.status_code == 200
    assert resp_safe.json()["is_triggered"] is False


def test_recommendations_endpoint(client: TestClient) -> None:
    """Verifies POST /api/v1/insights/recommendations."""
    payload = {
        "scores": {
            "sales": 85.0,
            "inventory": 35.0,  # Critical inventory bottleneck
            "finance": 75.0,
            "employee": 80.0,
        },
        "predictions": {
            "stockout_probability": 0.72,
        },
    }
    resp = client.post("/api/v1/insights/recommendations", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(r["domain"] == "inventory" for r in data)


def test_unified_dashboard_summary_endpoint(client: TestClient) -> None:
    """Verifies POST /api/v1/insights/dashboard-summary one-shot intelligence endpoint."""
    resp = client.post("/api/v1/insights/dashboard-summary", json={})
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"

    # 1. Verify business health & Bp
    health = data["business_health"]
    assert "bp_score" in health
    assert 0.0 <= health["bp_score"] <= 100.0
    assert health["alert_tier"] in ["OPTIMAL", "STABLE", "WATCHLIST", "CRITICAL"]
    assert "domain_scores" in health
    assert "sales" in health["domain_scores"]
    assert "inventory" in health["domain_scores"]

    # 2. Verify hybrid ML sales forecast & SHAP
    sales = data["sales_forecast"]
    assert sales["sku_id"] == "SKU-001"
    assert sales["predicted_demand"] > 0
    assert "top_positive_driver" in sales
    assert "top_negative_driver" in sales

    # 3. Verify inventory risk & restock
    inv = data["inventory_risk"]
    assert inv["sku_id"] == "SKU-001"
    assert 0.0 <= inv["stockout_probability"] <= 1.0
    assert "restock_triggered" in inv

    # 4. Verify executive narrative
    narrative = data["executive_narrative"]
    assert "headline" in narrative
    assert "summary" in narrative
    assert len(narrative["key_drivers"]) >= 1
    assert len(narrative["suggested_actions"]) >= 1
    assert narrative["source"] in ["llm_generated", "deterministic_fallback"]

    # 5. Verify recommendations
    assert isinstance(data["recommendations"], list)
