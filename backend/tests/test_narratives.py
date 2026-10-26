"""Test Suite for LLaMA Decision Narrative Synthesis & Rule-Based Fallback."""

import pytest
from typing import Any
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.llm.explanation import BusinessNarrative, ExplanationSynthesizer
from app.llm.llama_client import BaseLLMClient, LocalLLaMAClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class MockLLMClient(BaseLLMClient):
    """Mock LLM client returning predefined text for prompt testing."""

    def __init__(self, response_text: str = "") -> None:
        self.response_text = response_text

    async def generate_text(self, prompt: str, system_prompt: str = None, **kwargs: Any) -> str:
        return self.response_text

    async def is_available(self) -> bool:
        return True

    async def check_health(self) -> dict:
        return {"status": "connected", "latency_ms": 12.5}


class OfflineLLMClient(BaseLLMClient):
    """Simulates an offline remote Tailscale / AWS host (returns None)."""

    async def generate_text(self, prompt: str, system_prompt: str = None, **kwargs: Any):
        return None

    async def is_available(self) -> bool:
        return False

    async def check_health(self) -> dict:
        return {"status": "offline", "message": "Connection refused"}


@pytest.mark.asyncio
async def test_sales_narrative_deterministic_fallback() -> None:
    """Verifies that sales narrative falls back cleanly to executive copy when LLM is offline."""
    synthesizer = ExplanationSynthesizer(OfflineLLMClient())

    narrative: BusinessNarrative = await synthesizer.explain_prediction(
        domain="sales",
        predicted_value=142.50,
        target_metric="next_period_demand",
        top_positive_drivers=[
            {"human_label": "30-Day Moving Average Demand", "shap_value": 24.2},
            {"human_label": "Short-Term Sales Surge", "shap_value": 8.5},
        ],
        top_negative_drivers=[
            {"human_label": "Net Customer Price", "shap_value": -12.8},
        ],
        business_score=78.5,
        alert_tier="STABLE",
        primary_bottleneck="inventory",
    )

    assert narrative.source == "deterministic_fallback"
    assert "142.50" in narrative.headline
    assert "STABLE" in narrative.headline
    assert "30-Day Moving Average Demand" in narrative.summary
    assert len(narrative.key_drivers) >= 2
    assert len(narrative.suggested_actions) >= 2
    assert narrative.alert_tier == "STABLE"


@pytest.mark.asyncio
async def test_inventory_high_risk_fallback_trigger() -> None:
    """Verifies critical restock trigger copy when stockout risk exceeds 50%."""
    synthesizer = ExplanationSynthesizer(OfflineLLMClient())

    narrative: BusinessNarrative = await synthesizer.explain_prediction(
        domain="inventory",
        predicted_value=0.78,  # 78% risk
        target_metric="stockout_probability",
        top_positive_drivers=[],
        top_negative_drivers=[
            {"human_label": "Supplier Lead Time Delay", "shap_value": -0.35},
        ],
        business_score=44.0,
        alert_tier="CRITICAL",
        primary_bottleneck="inventory",
    )

    assert narrative.source == "deterministic_fallback"
    assert "CRITICAL RESTOCK TRIGGER" in narrative.headline
    assert "78.0%" in narrative.headline
    assert "Supplier Lead Time Delay" in narrative.summary
    assert narrative.alert_tier == "CRITICAL"


@pytest.mark.asyncio
async def test_parsed_llm_response() -> None:
    """Verifies parsing of sections when remote LLaMA responds."""
    mock_llm_output = (
        "HEADLINE: Sales Surge Expected for SKU-001 with High Probability\n"
        "SUMMARY: The model forecasts demand of 150 units driven by promotional campaigns. Overall operations are stable.\n"
        "KEY DRIVERS:\n"
        "- Promotional Discount Intensity (+18.40)\n"
        "- 30-Day Baseline Demand (+12.10)\n"
        "- Supplier Delivery Delay (-5.20)\n"
        "RECOMMENDED ACTIONS:\n"
        "- Increase procurement order batch by 20%.\n"
        "- Monitor warehouse safety stock.\n"
    )

    synthesizer = ExplanationSynthesizer(MockLLMClient(mock_llm_output))

    narrative: BusinessNarrative = await synthesizer.explain_prediction(
        domain="sales",
        predicted_value=150.0,
        target_metric="next_period_demand",
        shap_feature_importance={"promo_intensity": 18.4, "rolling_avg_30": 12.1},
    )

    assert narrative.source == "llm_generated"
    assert "Sales Surge Expected" in narrative.headline
    assert "Promotional campaigns" in narrative.summary or "150 units" in narrative.summary
    assert len(narrative.key_drivers) == 3
    assert len(narrative.suggested_actions) == 2


def test_explanations_generate_api_endpoint(client: TestClient) -> None:
    """Verifies POST /api/v1/explanations/generate endpoint."""
    payload = {
        "domain": "sales",
        "predicted_value": 110.0,
        "target_metric": "next_period_demand",
        "top_positive_drivers": [
            {"human_label": "Historical Demand Surge", "shap_value": 15.0}
        ],
        "top_negative_drivers": [
            {"human_label": "Price Sensitivity", "shap_value": -5.0}
        ],
        "business_score": 75.0,
        "alert_tier": "STABLE",
    }
    response = client.post("/api/v1/explanations/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "sales"
    assert "headline" in data
    assert "summary" in data
    assert len(data["key_drivers"]) >= 1
    assert len(data["suggested_actions"]) >= 1
    assert data["source"] in ["llm_generated", "deterministic_fallback"]


def test_explanations_llm_status_api_endpoint(client: TestClient) -> None:
    """Verifies GET /api/v1/explanations/llm-status endpoint diagnostics."""
    response = client.get("/api/v1/explanations/llm-status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["connected", "offline", "disabled", "timeout", "error"]
