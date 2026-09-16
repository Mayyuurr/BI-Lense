"""Employee Performance Score (E) Calculation Module.

NOTE: Exact component weights, sub-metrics, and normalization rules are
currently under research finalization.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class EmployeeScoreResult:
    """Encapsulates Employee Performance Domain Score (E) and sub-metrics."""

    employee_score: float  # Scale typically 0 - 100
    metrics_breakdown: Dict[str, Any]
    calculation_metadata: Optional[Dict[str, Any]] = None


class BaseEmployeeScoreCalculator(ABC):
    """Abstract interface for Employee score calculation."""

    @abstractmethod
    def calculate(self, hr_data: Dict[str, Any]) -> EmployeeScoreResult:
        """Calculates the E score from productivity/HR indicators."""
        pass


class EmployeeScoreCalculator(BaseEmployeeScoreCalculator):
    """Configurable implementation of Employee Performance Score (E) calculator."""

    def calculate(self, hr_data: Dict[str, Any]) -> EmployeeScoreResult:
        """Placeholder scoring implementation.

        Formulas and normalization thresholds will be injected via configuration
        once research is finalized.
        """
        return EmployeeScoreResult(
            employee_score=0.0,
            metrics_breakdown=hr_data,
            calculation_metadata={"status": "formula_pending_finalization"},
        )
