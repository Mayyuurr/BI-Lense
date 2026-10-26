"""Sales Score (S) Calculation Module.

Computes the bounded domain performance score S in [0, 100] across:
1. Target Achievement Ratio (40%)
2. Sales Growth Momentum (30%)
3. Discount & Margin Discipline (15%)
4. Order Quality / Retention (15%)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def _clamp(val: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(val)))


@dataclass
class SalesScoreResult:
    """Encapsulates Sales Domain Score (S) and sub-metrics."""

    sales_score: float  # Bounded [0, 100]
    metrics_breakdown: Dict[str, Any]
    calculation_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseSalesScoreCalculator(ABC):
    """Abstract interface for Sales score calculation."""

    @abstractmethod
    def calculate(self, sales_data: Dict[str, Any]) -> SalesScoreResult:
        """Calculates the S score from raw/aggregated sales indicators."""
        pass


class SalesScoreCalculator(BaseSalesScoreCalculator):
    """Production implementation of Sales Score (S) calculator for SMEs."""

    WEIGHT_TARGET_ACHIEVEMENT: float = 0.40
    WEIGHT_GROWTH_MOMENTUM: float = 0.30
    WEIGHT_DISCOUNT_DISCIPLINE: float = 0.15
    WEIGHT_ORDER_QUALITY: float = 0.15

    def calculate(self, sales_data: Dict[str, Any]) -> SalesScoreResult:
        """Calculates S score bounded between 0 and 100.

        Supported input keys (with resilient fallbacks):
        - actual_sales / total_sales / predicted_demand (default: 100.0)
        - target_sales (default: actual_sales * 1.05)
        - sales_growth_rate / growth_mom (percentage, e.g. 10.0 for +10%, default: 5.0)
        - discount_rate / average_discount (decimal, e.g. 0.08 for 8%, default: 0.05)
        - return_rate / cancellation_rate (percentage, e.g. 2.0 for 2%, default: 2.0)
        """
        # 1. Target Achievement Ratio (40%)
        actual_sales = float(
            sales_data.get("actual_sales")
            or sales_data.get("total_sales")
            or sales_data.get("predicted_demand")
            or 100.0
        )
        target_sales = float(
            sales_data.get("target_sales")
            or (actual_sales * 1.05 if actual_sales > 0 else 100.0)
        )
        target_ratio = (actual_sales / target_sales) if target_sales > 0 else 1.0
        s_target = _clamp(target_ratio * 100.0)

        # 2. Growth Momentum (30%)
        growth_pct = float(
            sales_data.get("sales_growth_rate")
            or sales_data.get("growth_mom")
            or sales_data.get("lag1_to_rolling_ratio", 1.0) * 10.0 - 10.0
            or 5.0
        )
        # 0% growth -> 60 pts; +20% -> 100 pts; -20% -> 20 pts
        s_growth = _clamp(60.0 + (growth_pct * 2.0))

        # 3. Discount Discipline (15%)
        discount_rate = float(
            sales_data.get("discount_rate")
            or sales_data.get("average_discount")
            or 0.05
        )
        # Moderate discount <= 5% -> 100 pts. Deep discounting > 25% penalizes down.
        if discount_rate <= 0.05:
            s_discount = 100.0
        else:
            s_discount = _clamp(100.0 - ((discount_rate - 0.05) * 250.0))

        # 4. Order Quality / Low Return Rate (15%)
        return_rate_pct = float(
            sales_data.get("return_rate")
            or sales_data.get("cancellation_rate")
            or 2.0
        )
        s_quality = _clamp(100.0 - (return_rate_pct * 5.0))

        # Weighted aggregate
        composite_s = round(
            (self.WEIGHT_TARGET_ACHIEVEMENT * s_target)
            + (self.WEIGHT_GROWTH_MOMENTUM * s_growth)
            + (self.WEIGHT_DISCOUNT_DISCIPLINE * s_discount)
            + (self.WEIGHT_ORDER_QUALITY * s_quality),
            2,
        )

        breakdown = {
            "target_achievement_score": round(s_target, 2),
            "growth_momentum_score": round(s_growth, 2),
            "discount_discipline_score": round(s_discount, 2),
            "order_quality_score": round(s_quality, 2),
            "raw_inputs": {
                "actual_sales": actual_sales,
                "target_sales": target_sales,
                "growth_pct": growth_pct,
                "discount_rate": discount_rate,
                "return_rate_pct": return_rate_pct,
            },
        }

        return SalesScoreResult(
            sales_score=composite_s,
            metrics_breakdown=breakdown,
            calculation_metadata={"status": "calculated", "formula": "4-component weighted linear"},
        )
