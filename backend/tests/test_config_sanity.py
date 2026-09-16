"""Configuration and Module Import Sanity Tests."""

from app.core.config import settings
from app.data.ingestion.connectors import CSVConnector
from app.data.preprocessing.cleaner import DeterministicDataCleaner
from app.ml.ensemble.optimizer import EnsembleOptimizer, EnsembleWeights
from app.scoring.bp_score import BPScoreCalculator
from app.recommendations.engine import RecommendationEngine


def test_settings_sanity() -> None:
    """Verify default configuration attributes are loaded properly."""
    assert settings.APP_NAME != ""
    assert settings.API_V1_STR == "/api/v1"
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
    assert settings.LLAMA_ENABLED is False or settings.LLAMA_ENABLED is True


def test_ensemble_weights_validation() -> None:
    """Verify ensemble weights validation logic."""
    valid_weights = EnsembleWeights(w_rf=0.4, w_xgb=0.4, w_ann=0.2)
    assert valid_weights.validate() is True

    invalid_sum = EnsembleWeights(w_rf=0.5, w_xgb=0.5, w_ann=0.5)
    assert invalid_sum.validate() is False

    invalid_negative = EnsembleWeights(w_rf=1.2, w_xgb=-0.2, w_ann=0.0)
    assert invalid_negative.validate() is False


def test_bp_score_calculator_sanity() -> None:
    """Verify BP score aggregator calculates mean of available domain scores."""
    calc = BPScoreCalculator()
    result = calc.calculate_bp(
        sales_score=80.0,
        inventory_score=70.0,
        finance_score=90.0,
        employee_score=80.0,
    )
    assert result.bp_score == 80.0
    assert result.metadata["components_evaluated"] == 4


def test_procurement_restock_trigger_sanity() -> None:
    """Verify restocking trigger evaluates accurately."""
    engine = RecommendationEngine()
    trigger = engine.evaluate_procurement_restock(
        current_stock=10.0,
        reorder_point=50.0,
        safety_stock=10.0,
        lead_time_days=5,
        daily_demand=10.0,
        sku_id="SKU-001",
    )
    assert trigger.is_triggered is True
    assert trigger.suggested_order_quantity > 0
