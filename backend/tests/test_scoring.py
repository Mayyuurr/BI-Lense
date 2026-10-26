import pytest
from typing import Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.scoring.bp_score import (
    BPScoreCalculator,
    ALERT_TIER_OPTIMAL,
    ALERT_TIER_STABLE,
    ALERT_TIER_WATCHLIST,
    ALERT_TIER_CRITICAL,
)
from app.scoring.employee_score import EmployeeScoreCalculator
from app.scoring.finance_score import FinanceScoreCalculator
from app.scoring.inventory_score import InventoryScoreCalculator
from app.scoring.sales_score import SalesScoreCalculator
from app.services.scoring_service import ScoringService


@pytest.fixture
def db_session():
    """In-memory SQLite session for testing database persistence without external PostgreSQL."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Any) -> TestClient:
    """TestClient with get_db overridden by the SQLite in-memory session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_sales_score_calculator() -> None:
    """Verifies Sales Score (S) calculation and sub-metrics."""
    calc = SalesScoreCalculator()
    result = calc.calculate({
        "actual_sales": 120.0,
        "target_sales": 100.0,
        "sales_growth_rate": 15.0,
        "discount_rate": 0.05,
        "return_rate": 1.5,
    })
    assert 0.0 <= result.sales_score <= 100.0
    assert result.sales_score >= 80.0  # Above target with good growth and low return
    breakdown = result.metrics_breakdown
    assert "target_achievement_score" in breakdown
    assert "growth_momentum_score" in breakdown
    assert "discount_discipline_score" in breakdown
    assert "order_quality_score" in breakdown


def test_inventory_score_calculator() -> None:
    """Verifies Inventory Score (I) calculation with stockout resilience."""
    calc = InventoryScoreCalculator()

    # Case 1: Healthy inventory
    healthy = calc.calculate({
        "stockout_probability": 0.05,
        "inventory_turnover_ratio": 8.0,
        "current_stock": 100.0,
        "safety_stock": 50.0,
    })
    assert healthy.inventory_score >= 85.0

    # Case 2: High stockout risk
    risky = calc.calculate({
        "stockout_probability": 0.85,
        "inventory_turnover_ratio": 2.0,
        "current_stock": 10.0,
        "safety_stock": 50.0,
    })
    assert risky.inventory_score < 40.0


def test_finance_score_calculator() -> None:
    """Verifies Finance Score (F) calculation with margin and liquidity."""
    calc = FinanceScoreCalculator()
    result = calc.calculate({
        "gross_margin_pct": 35.0,
        "quick_ratio": 1.8,
        "expense_to_revenue_ratio": 0.60,
    })
    assert 0.0 <= result.finance_score <= 100.0
    assert result.finance_score >= 80.0


def test_employee_score_calculator() -> None:
    """Verifies Employee Score (E) calculation with productivity and retention."""
    calc = EmployeeScoreCalculator()
    result = calc.calculate({
        "productivity_score": 90.0,
        "retention_rate": 95.0,
        "attendance_rate": 96.0,
    })
    assert 0.0 <= result.employee_score <= 100.0
    assert result.employee_score >= 90.0


def test_bp_score_four_domains_and_alert_tiers() -> None:
    """Verifies Bp weighted average, alert tier, and bottleneck detection."""
    calc = BPScoreCalculator()

    # Optimal test
    optimal_res = calc.calculate_bp(
        sales_score=90.0,
        inventory_score=88.0,
        finance_score=85.0,
        employee_score=87.0,
    )
    assert optimal_res.bp_score >= 85.0
    assert optimal_res.alert_tier == ALERT_TIER_OPTIMAL
    assert optimal_res.metadata["components_evaluated"] == 4

    # Watchlist with bottleneck test
    watchlist_res = calc.calculate_bp(
        sales_score=75.0,
        inventory_score=40.0,  # Critical bottleneck
        finance_score=70.0,
        employee_score=65.0,
    )
    assert 50.0 <= watchlist_res.bp_score < 70.0
    assert watchlist_res.alert_tier == ALERT_TIER_WATCHLIST
    assert watchlist_res.metadata["primary_bottleneck"] == "inventory"
    assert watchlist_res.metadata["key_strength"] == "sales"


def test_bp_score_dynamic_weight_redistribution() -> None:
    """Verifies that missing domains reweight remaining active domains to sum to 1.0."""
    calc = BPScoreCalculator()

    # Only Sales (90.0) and Inventory (70.0) available
    result = calc.calculate_bp(
        sales_score=90.0,
        inventory_score=70.0,
        finance_score=None,
        employee_score=None,
    )
    # Equal 50/50 split of remaining weights -> (90 + 70) / 2 = 80.0
    assert result.bp_score == 80.0
    assert result.metadata["components_evaluated"] == 2
    assert result.metadata["weights_applied"]["sales"] == 0.5
    assert result.metadata["weights_applied"]["inventory"] == 0.5


def test_scores_compute_api_endpoint(client: TestClient) -> None:
    """Verifies POST /api/v1/scores/compute endpoint."""
    payload = {
        "sales_data": {
            "actual_sales": 150.0,
            "target_sales": 130.0,
            "sales_growth_rate": 10.0,
        },
        "inventory_data": {
            "stockout_probability": 0.10,
            "inventory_turnover_ratio": 7.5,
        },
        "finance_data": {
            "gross_margin_pct": 32.0,
            "quick_ratio": 1.4,
        },
        "hr_data": {
            "productivity_score": 88.0,
            "retention_rate": 93.0,
        },
    }
    response = client.post("/api/v1/scores/compute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "bp_score" in data
    assert 0.0 <= data["bp_score"] <= 100.0
    assert data["sales_score"] is not None
    assert data["inventory_score"] is not None
    assert data["alert_tier"] in [ALERT_TIER_OPTIMAL, ALERT_TIER_STABLE, ALERT_TIER_WATCHLIST, ALERT_TIER_CRITICAL]


def test_scores_latest_and_history_api_endpoints(client: TestClient) -> None:
    """Verifies GET /api/v1/scores/latest and GET /api/v1/scores/history."""
    # First compute a score so database has at least one record
    client.post("/api/v1/scores/compute", json={
        "sales_data": {"actual_sales": 100.0},
        "inventory_data": {"stockout_probability": 0.20},
    })

    # Test /latest
    latest_resp = client.get("/api/v1/scores/latest")
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()
    assert "bp_score" in latest_data or latest_data.get("status") == "empty"

    # Test /history
    history_resp = client.get("/api/v1/scores/history?limit=10")
    assert history_resp.status_code == 200
    history_data = history_resp.json()
    assert isinstance(history_data, list)
