"""Composite Business Performance Score (Bp) Module.

Implements the high-level formulation:
    Bp = (S + I + F + E) / 4

NOTE: Specific component weightings and normalization/out-of-range rules are
currently under research finalization.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class BusinessPerformanceResult:
    """Encapsulates the aggregate Business Performance Score (Bp) and domain components."""

    bp_score: float
    sales_score: Optional[float]
    inventory_score: Optional[float]
    finance_score: Optional[float]
    employee_score: Optional[float]
    metadata: Optional[Dict[str, Any]] = None


class BPScoreCalculator:
    """Calculates overall Business Performance Score (Bp) across the 4 core domains."""

    def calculate_bp(
        self,
        sales_score: Optional[float] = None,
        inventory_score: Optional[float] = None,
        finance_score: Optional[float] = None,
        employee_score: Optional[float] = None,
    ) -> BusinessPerformanceResult:
        """Calculates Bp = (S + I + F + E) / 4.

        Handles missing component scores gracefully during partial data availability.
        """
        available_scores = [
            s for s in (sales_score, inventory_score, finance_score, employee_score)
            if s is not None
        ]

        if not available_scores:
            bp = 0.0
        else:
            # Baseline mean of available domain scores
            bp = sum(available_scores) / len(available_scores)

        return BusinessPerformanceResult(
            bp_score=bp,
            sales_score=sales_score,
            inventory_score=inventory_score,
            finance_score=finance_score,
            employee_score=employee_score,
            metadata={"components_evaluated": len(available_scores)},
        )
