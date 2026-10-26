"""Finance Score (F) Calculation Module.

Computes the bounded domain performance score F in [0, 100] across:
1. Gross & Operating Margin Health (35%)
2. Liquidity / Current Ratio (35%)
3. Expense-to-Revenue Efficiency (30%)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def _clamp(val: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(val)))


@dataclass
class FinanceScoreResult:
    """Encapsulates Financial Domain Score (F) and sub-metrics."""

    finance_score: float  # Bounded [0, 100]
    metrics_breakdown: Dict[str, Any]
    calculation_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseFinanceScoreCalculator(ABC):
    """Abstract interface for Finance score calculation."""

    @abstractmethod
    def calculate(self, finance_data: Dict[str, Any]) -> FinanceScoreResult:
        """Calculates the F score from financial indicators."""
        pass


class FinanceScoreCalculator(BaseFinanceScoreCalculator):
    """Production implementation of Finance Score (F) calculator for SMEs."""

    WEIGHT_MARGIN_HEALTH: float = 0.35
    WEIGHT_LIQUIDITY_RATIO: float = 0.35
    WEIGHT_EXPENSE_EFFICIENCY: float = 0.30

    def calculate(self, finance_data: Dict[str, Any]) -> FinanceScoreResult:
        """Calculates F score bounded between 0 and 100.

        Supported input keys:
        - gross_margin_pct / margin_pct (percentage, e.g. 35.0 for 35%, default: 30.0)
        - quick_ratio / current_ratio (float, benchmark: 1.5, default: 1.5)
        - expense_to_revenue_ratio / operating_expense_ratio (float [0, 1], default: 0.70)
        - net_profit_margin (percentage, default: 12.0)
        """
        # 1. Margin Health (35%)
        # Benchmark: >= 40% margin -> 100 pts. 20% margin -> 60 pts. < 5% -> 20 pts.
        margin_pct = float(
            finance_data.get("gross_margin_pct")
            or finance_data.get("margin_pct")
            or 30.0
        )
        f_margin = _clamp(margin_pct * 2.5, low=15.0, high=100.0)

        # 2. Liquidity Ratio (35%)
        # Benchmark: Quick ratio 1.5 is healthy SME benchmark.
        # Ratio >= 1.5 -> 100 pts. Ratio 1.0 -> 70 pts. Ratio < 0.8 -> high liquidity risk (< 50 pts).
        quick_ratio = float(
            finance_data.get("quick_ratio")
            or finance_data.get("current_ratio")
            or 1.5
        )
        if quick_ratio >= 1.5:
            f_liquidity = 100.0
        else:
            f_liquidity = _clamp(quick_ratio * 66.67, low=10.0, high=100.0)

        # 3. Expense Efficiency (30%)
        # Operating Expense to Revenue ratio: ideal <= 0.65 -> 100 pts. 0.85 -> 50 pts. >= 1.0 -> insolvent.
        exp_ratio = float(
            finance_data.get("expense_to_revenue_ratio")
            or finance_data.get("operating_expense_ratio")
            or 0.70
        )
        if exp_ratio <= 0.65:
            f_efficiency = 100.0
        else:
            # Drop from 100 at 0.65 to 0 at 1.15
            f_efficiency = _clamp(100.0 - ((exp_ratio - 0.65) * 200.0), low=10.0, high=100.0)

        composite_f = round(
            (self.WEIGHT_MARGIN_HEALTH * f_margin)
            + (self.WEIGHT_LIQUIDITY_RATIO * f_liquidity)
            + (self.WEIGHT_EXPENSE_EFFICIENCY * f_efficiency),
            2,
        )

        breakdown = {
            "margin_health_score": round(f_margin, 2),
            "liquidity_ratio_score": round(f_liquidity, 2),
            "expense_efficiency_score": round(f_efficiency, 2),
            "raw_inputs": {
                "gross_margin_pct": margin_pct,
                "quick_ratio": quick_ratio,
                "expense_to_revenue_ratio": exp_ratio,
            },
        }

        return FinanceScoreResult(
            finance_score=composite_f,
            metrics_breakdown=breakdown,
            calculation_metadata={"status": "calculated", "formula": "margin-liquidity-efficiency weighted"},
        )
