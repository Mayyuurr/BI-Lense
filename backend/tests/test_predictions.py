"""Automated Integration & Unit Tests for Backend ML Prediction Pipeline.

Verifies:
1. In-memory ModelRegistry artifact caching.
2. Live Sales & Demand hybrid ensemble inference.
3. Live Inventory stockout risk hybrid ensemble inference.
4. API endpoint response schemas and status codes.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.registry import ModelRegistry
from app.ml.sales import SalesDemandPredictor
from app.ml.inventory import InventoryStockoutPredictor


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_model_registry_loaded():
    """Verifies that ModelRegistry loads and caches all domain artifacts."""
    registry = ModelRegistry.get_instance()
    assert registry.sales_artifacts is not None
    assert "rf_model" in registry.sales_artifacts
    assert "xgb_model" in registry.sales_artifacts
    assert "ann_model" in registry.sales_artifacts
    assert "preprocessor" in registry.sales_artifacts
    assert "ensemble_weights" in registry.sales_artifacts

    assert registry.inventory_artifacts is not None
    assert "rf_model" in registry.inventory_artifacts
    assert "xgb_model" in registry.inventory_artifacts
    assert "ann_model" in registry.inventory_artifacts
    assert "preprocessor" in registry.inventory_artifacts
    assert "ensemble_weights" in registry.inventory_artifacts


def test_sales_predictor_live_inference():
    """Verifies SalesDemandPredictor inference logic and positive output."""
    import pandas as pd
    predictor = SalesDemandPredictor.from_registry()
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

    result = predictor.predict_next_period_demand(features=sample_df, sku_id="SKU-001")
    assert result.predicted_demand > 0.0
    assert "rf" in result.base_predictions
    assert "xgb" in result.base_predictions
    assert "ann" in result.base_predictions
    assert sum(result.ensemble_weights.values()) == pytest.approx(1.0, abs=1e-3)


def test_inventory_predictor_live_inference():
    """Verifies InventoryStockoutPredictor probability bounds [0, 1] and risk tier."""
    import pandas as pd
    predictor = InventoryStockoutPredictor.from_registry()
    sample_df = pd.DataFrame([{
        "sku_id": "SKU-001",
        "current_stock": 20.0,
        "reorder_level": 80.0,
        "safety_stock": 25.0,
        "lead_time_days": 12.0,
        "historical_delivery_delay_days": 3.0,
        "inventory_turnover_ratio": 7.5,
        "predicted_sales_demand": 85.0,
    }])

    result = predictor.predict_stockout_probability(features=sample_df, sku_id="SKU-001")
    assert 0.0 <= result.stockout_probability <= 1.0
    assert result.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "rf" in result.base_predictions
    assert "xgb" in result.base_predictions
    assert "ann" in result.base_predictions


def test_sales_prediction_endpoint(client):
    """Tests POST /api/v1/predictions/sales HTTP contract."""
    payload = {
        "sku_id": "SKU-005",
        "unit_price": 85.0,
        "sales_lag_1": 45.0,
        "sales_lag_7": 42.0,
        "sales_lag_30": 40.0,
        "rolling_avg_30": 44.0,
        "discount_rate": 0.05,
        "promotional_flag": 0,
        "day_of_week": 3,
        "month": 5,
        "product_category": "Electronics",
    }
    response = client.post("/api/v1/predictions/sales", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "sales"
    assert data["sku_id"] == "SKU-005"
    assert data["predicted_demand"] > 0
    assert data["status"] == "success"


def test_inventory_prediction_endpoint(client):
    """Tests POST /api/v1/predictions/inventory HTTP contract."""
    payload = {
        "sku_id": "SKU-010",
        "current_stock": 10.0,
        "reorder_level": 90.0,
        "safety_stock": 30.0,
        "lead_time_days": 14.0,
        "historical_delivery_delay_days": 2.0,
        "inventory_turnover_ratio": 6.5,
        "predicted_sales_demand": 95.0,
    }
    response = client.post("/api/v1/predictions/inventory", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "inventory"
    assert data["sku_id"] == "SKU-010"
    assert 0.0 <= data["stockout_probability"] <= 1.0
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert data["status"] == "success"


def test_generic_prediction_run_endpoint(client):
    """Tests POST /api/v1/predictions/run generic router."""
    payload = {
        "domain": "sales",
        "features": {
            "sku_id": "SKU-002",
            "unit_price": 150.0,
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
    response = client.post("/api/v1/predictions/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "sales"
    assert data["predicted_demand"] > 0
