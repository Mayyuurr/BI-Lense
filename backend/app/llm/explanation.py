"""LLaMA Decision Support Explanation Layer.

Synthesizes deterministic ML predictions, SHAP feature attributions, and
business scores into plain-language actionable business explanations for SME owners.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from app.llm.llama_client import BaseLLMClient


@dataclass
class BusinessNarrative:
    """Natural-language explanation of predictive models and score drivers."""

    domain: str
    headline: str
    summary: str
    key_drivers: List[str]
    suggested_actions: List[str]
    raw_response: Optional[str] = None


class ExplanationSynthesizer:
    """Translates analytical outputs into executive-level decision narratives."""

    def __init__(self, llm_client: BaseLLMClient) -> None:
        self.llm_client = llm_client

    async def explain_prediction(
        self,
        domain: str,
        predicted_value: float,
        target_metric: str,
        shap_feature_importance: Dict[str, float],
        business_score: Optional[float] = None,
    ) -> BusinessNarrative:
        """Generates a natural-language narrative strictly based on the provided

        prediction values, SHAP attributions, and business scores.
        """
        system_prompt = (
            "You are an AI decision intelligence explainer for SME executives. "
            "Explain the model's prediction and the primary contributing factors "
            "based strictly on the provided SHAP values and business score. "
            "Do NOT fabricate new numbers or alter the prediction."
        )

        user_prompt = (
            f"Domain: {domain}\n"
            f"Metric: {target_metric}\n"
            f"Predicted Value: {predicted_value}\n"
            f"Domain Business Score: {business_score}\n"
            f"Key SHAP Feature Drivers (Feature -> Contribution): {shap_feature_importance}\n"
            "Task: Provide a concise executive summary, explain the top 3 drivers, and highlight actionable next steps."
        )

        raw_response = await self.llm_client.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        # Extract top feature drivers from SHAP inputs
        sorted_drivers = sorted(
            shap_feature_importance.items(),
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        driver_strings = [
            f"{feat} (impact: {val:+.2f})" for feat, val in sorted_drivers[:3]
        ]

        return BusinessNarrative(
            domain=domain,
            headline=f"Analysis for {domain.title()} ({target_metric})",
            summary=f"Predicted {target_metric}: {predicted_value:.2f}.",
            key_drivers=driver_strings,
            suggested_actions=["Review key drivers and evaluate operational buffers."],
            raw_response=raw_response,
        )
