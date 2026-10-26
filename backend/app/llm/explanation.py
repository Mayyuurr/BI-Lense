"""LLaMA Decision Support Explanation Layer.

Synthesizes deterministic hybrid ML predictions, exact linear ensemble SHAP attributions,
and composite Business Performance (Bp) scores into actionable executive narratives.
Includes instant rule-based fallback if the remote LLM host (Tailscale / AWS) is unreachable.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional, Tuple
import re

from app.core.logging_config import logger
from app.llm.llama_client import BaseLLMClient


@dataclass
class BusinessNarrative:
    """Natural-language explanation of predictive models, SHAP drivers, and Bp health."""

    domain: str
    headline: str
    summary: str
    key_drivers: List[str]
    suggested_actions: List[str]
    alert_tier: str  # OPTIMAL | STABLE | WATCHLIST | CRITICAL
    source: str  # "llm_generated" | "deterministic_fallback"
    latency_ms: Optional[float] = None
    raw_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts narrative into API response dictionary."""
        return {
            "domain": self.domain,
            "headline": self.headline,
            "summary": self.summary,
            "key_drivers": self.key_drivers,
            "suggested_actions": self.suggested_actions,
            "alert_tier": self.alert_tier,
            "source": self.source,
            "latency_ms": self.latency_ms,
            "raw_response": self.raw_response,
        }


class ExplanationSynthesizer:
    """Translates analytical outputs into executive-level decision narratives."""

    def __init__(self, llm_client: BaseLLMClient) -> None:
        self.llm_client = llm_client

    async def explain_prediction(
        self,
        domain: str,
        predicted_value: float,
        target_metric: str,
        shap_feature_importance: Optional[Dict[str, float]] = None,
        top_positive_drivers: Optional[List[Dict[str, Any]]] = None,
        top_negative_drivers: Optional[List[Dict[str, Any]]] = None,
        business_score: Optional[float] = None,
        alert_tier: Optional[str] = None,
        primary_bottleneck: Optional[str] = None,
    ) -> BusinessNarrative:
        """Generates natural-language business narrative strictly based on prediction metrics,

        exact SHAP drivers, and Bp performance scores.
        """
        start_time = time.perf_counter()
        domain_clean = domain.lower().strip()
        alert_tier_resolved = alert_tier or self._infer_alert_tier(domain_clean, predicted_value, business_score)

        # Standardize driver lists
        pos_drivers, neg_drivers = self._extract_driver_lists(
            shap_feature_importance=shap_feature_importance,
            top_positive_drivers=top_positive_drivers,
            top_negative_drivers=top_negative_drivers,
        )

        # Build prompt
        system_prompt = (
            "You are an executive AI decision intelligence copilot for small-to-medium enterprise (SME) leaders. "
            "Explain the ML prediction, the exact primary drivers from SHAP attributions, and the Business Performance (Bp) health status. "
            "Guidelines:\n"
            "1. Be concise, highly professional, and direct.\n"
            "2. Do NOT invent new numbers or contradict the provided predictions and scores.\n"
            "3. Format your response into four clearly marked sections:\n"
            "   HEADLINE: <one clear sentence summarizing the forecast and urgency>\n"
            "   SUMMARY: <2-3 sentences explaining the forecast and overall business health>\n"
            "   KEY DRIVERS: <bullet points explaining top positive and negative drivers>\n"
            "   RECOMMENDED ACTIONS: <2 concrete operational steps the SME owner should take>"
        )

        user_prompt = self._build_user_prompt(
            domain=domain_clean,
            metric=target_metric,
            predicted_value=predicted_value,
            business_score=business_score,
            alert_tier=alert_tier_resolved,
            primary_bottleneck=primary_bottleneck,
            pos_drivers=pos_drivers,
            neg_drivers=neg_drivers,
        )

        # Request generation from remote/local LLaMA
        raw_response = await self.llm_client.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if raw_response:
            # Parse sections from structured LLM response
            parsed = self._parse_llm_response(
                domain=domain_clean,
                raw_response=raw_response,
                predicted_value=predicted_value,
                target_metric=target_metric,
                alert_tier=alert_tier_resolved,
                pos_drivers=pos_drivers,
                neg_drivers=neg_drivers,
                latency_ms=elapsed_ms,
            )
            return parsed

        # Remote LLM unreachable, offline, or disabled -> trigger instant deterministic fallback
        return self._generate_deterministic_fallback(
            domain=domain_clean,
            predicted_value=predicted_value,
            target_metric=target_metric,
            alert_tier=alert_tier_resolved,
            business_score=business_score,
            primary_bottleneck=primary_bottleneck,
            pos_drivers=pos_drivers,
            neg_drivers=neg_drivers,
            latency_ms=elapsed_ms,
        )

    def _build_user_prompt(
        self,
        domain: str,
        metric: str,
        predicted_value: float,
        business_score: Optional[float],
        alert_tier: str,
        primary_bottleneck: Optional[str],
        pos_drivers: List[str],
        neg_drivers: List[str],
    ) -> str:
        prompt_lines = [
            f"Domain: {domain.upper()}",
            f"Target Forecast Metric: {metric} = {predicted_value:.2f}",
            f"Business Health Tier: {alert_tier} (Composite Bp: {business_score:.1f}/100)" if business_score else f"Alert Tier: {alert_tier}",
        ]
        if primary_bottleneck:
            prompt_lines.append(f"Primary Operational Bottleneck: {primary_bottleneck.title()}")

        prompt_lines.append("\nTop Positive SHAP Drivers (Increasing Forecast):")
        for d in pos_drivers[:3]:
            prompt_lines.append(f"  + {d}")

        prompt_lines.append("\nTop Negative SHAP Drivers (Decreasing Forecast / Increasing Risk):")
        for d in neg_drivers[:3]:
            prompt_lines.append(f"  - {d}")

        prompt_lines.append("\nTask: Provide the executive HEADLINE, SUMMARY, KEY DRIVERS, and RECOMMENDED ACTIONS.")
        return "\n".join(prompt_lines)

    def _extract_driver_lists(
        self,
        shap_feature_importance: Optional[Dict[str, float]],
        top_positive_drivers: Optional[List[Dict[str, Any]]],
        top_negative_drivers: Optional[List[Dict[str, Any]]],
    ) -> Tuple[List[str], List[str]]:
        pos: List[str] = []
        neg: List[str] = []

        if top_positive_drivers:
            pos = [
                f"{d.get('human_label', d.get('feature_name'))} (+{abs(float(d.get('shap_value', 0))):.2f})"
                for d in top_positive_drivers
            ]
        if top_negative_drivers:
            neg = [
                f"{d.get('human_label', d.get('feature_name'))} (-{abs(float(d.get('shap_value', 0))):.2f})"
                for d in top_negative_drivers
            ]

        # If only flat dict provided
        if not pos and not neg and shap_feature_importance:
            for feat, val in shap_feature_importance.items():
                if val >= 0:
                    pos.append(f"{feat.replace('_', ' ').title()} (+{abs(float(val)):.2f})")
                else:
                    neg.append(f"{feat.replace('_', ' ').title()} (-{abs(float(val)):.2f})")

        return pos or ["Baseline Historical Momentum (+0.00)"], neg or ["Standard Operational Resistance (-0.00)"]

    def _infer_alert_tier(self, domain: str, predicted_value: float, business_score: Optional[float]) -> str:
        if business_score is not None:
            if business_score >= 85.0:
                return "OPTIMAL"
            elif business_score >= 70.0:
                return "STABLE"
            elif business_score >= 50.0:
                return "WATCHLIST"
            else:
                return "CRITICAL"

        # Domain heuristic fallback
        if domain == "inventory" and predicted_value > 0.60:
            return "CRITICAL"
        elif domain == "inventory" and predicted_value > 0.30:
            return "WATCHLIST"
        return "STABLE"

    def _parse_llm_response(
        self,
        domain: str,
        raw_response: str,
        predicted_value: float,
        target_metric: str,
        alert_tier: str,
        pos_drivers: List[str],
        neg_drivers: List[str],
        latency_ms: float,
    ) -> BusinessNarrative:
        headline = ""
        summary = ""
        key_drivers: List[str] = []
        actions: List[str] = []

        # Simple section extraction regex
        h_match = re.search(r"HEADLINE:\s*(.*?)(?=\n[A-Z\s]+:|$)", raw_response, re.DOTALL | re.IGNORECASE)
        s_match = re.search(r"SUMMARY:\s*(.*?)(?=\n[A-Z\s]+:|$)", raw_response, re.DOTALL | re.IGNORECASE)
        d_match = re.search(r"KEY DRIVERS:\s*(.*?)(?=\n[A-Z\s]+:|$)", raw_response, re.DOTALL | re.IGNORECASE)
        a_match = re.search(r"RECOMMENDED ACTIONS:\s*(.*?)(?=\n[A-Z\s]+:|$)", raw_response, re.DOTALL | re.IGNORECASE)

        if h_match:
            headline = h_match.group(1).strip()
        if s_match:
            summary = s_match.group(1).strip()
        if d_match:
            lines = [line.strip().lstrip("-*•0123456789. ") for line in d_match.group(1).splitlines() if line.strip()]
            key_drivers = lines[:4]
        if a_match:
            lines = [line.strip().lstrip("-*•0123456789. ") for line in a_match.group(1).splitlines() if line.strip()]
            actions = lines[:3]

        # Resilient fallbacks for any unparsed section
        if not headline:
            headline = f"{domain.title()} Forecast: {predicted_value:.2f} ({target_metric.replace('_', ' ').title()})"
        if not summary:
            summary = raw_response[:300].strip()
        if not key_drivers:
            key_drivers = (pos_drivers + neg_drivers)[:3]
        if not actions:
            actions = ["Monitor current order pipeline", "Re-evaluate stock buffers with suppliers"]

        return BusinessNarrative(
            domain=domain,
            headline=headline,
            summary=summary,
            key_drivers=key_drivers,
            suggested_actions=actions,
            alert_tier=alert_tier,
            source="llm_generated",
            latency_ms=latency_ms,
            raw_response=raw_response,
        )

    def _generate_deterministic_fallback(
        self,
        domain: str,
        predicted_value: float,
        target_metric: str,
        alert_tier: str,
        business_score: Optional[float],
        primary_bottleneck: Optional[str],
        pos_drivers: List[str],
        neg_drivers: List[str],
        latency_ms: float,
    ) -> BusinessNarrative:
        """Deterministic executive narrative used when remote LLM host is unavailable."""
        top_pos = pos_drivers[0] if pos_drivers else "Baseline Demand"
        top_neg = neg_drivers[0] if neg_drivers else "Market Resistance"

        if domain == "sales":
            headline = f"Sales Forecast: {predicted_value:.2f} Units Expected (Health: {alert_tier})"
            summary = (
                f"The hybrid ensemble projects next-period demand of {predicted_value:.2f} units. "
                f"Demand momentum is predominantly accelerated by {top_pos}, while being constrained by {top_neg}."
            )
            actions = [
                "Align procurement replenishment batch sizes to accommodate projected demand surges.",
                "Review promotional discount intensity to protect operating margin.",
            ]
        elif domain == "inventory":
            prob_pct = predicted_value * 100.0
            if prob_pct >= 50.0:
                headline = f"CRITICAL RESTOCK TRIGGER: {prob_pct:.1f}% Stockout Risk"
                summary = (
                    f"Warehouse inventory indicates an elevated stockout probability of {prob_pct:.1f}%. "
                    f"The primary risk driver is {top_neg}, requiring immediate replenishment order placement."
                )
                actions = [
                    "Trigger emergency purchase order to supplier immediately to avoid stockout.",
                    "Audit current safety stock buffers and supplier lead-time delay variance.",
                ]
            else:
                headline = f"Stable Inventory Resilience ({prob_pct:.1f}% Stockout Risk)"
                summary = (
                    f"Stock levels indicate healthy coverage with low stockout probability of {prob_pct:.1f}%. "
                    f"Stability is maintained primarily by {top_pos}."
                )
                actions = [
                    "Maintain standard procurement replenishment reorder thresholds.",
                    "Monitor 30-day demand baseline changes to prevent surplus overstocking.",
                ]
        else:
            headline = f"{domain.title()} Performance Analysis ({alert_tier})"
            summary = f"Predicted {target_metric} stands at {predicted_value:.2f}. Key contributing factor is {top_pos}."
            actions = ["Maintain weekly cross-domain review and monitor key metric variances."]

        all_drivers = (pos_drivers + neg_drivers)[:4]

        return BusinessNarrative(
            domain=domain,
            headline=headline,
            summary=summary,
            key_drivers=all_drivers,
            suggested_actions=actions,
            alert_tier=alert_tier,
            source="deterministic_fallback",
            latency_ms=latency_ms,
            raw_response=None,
        )
