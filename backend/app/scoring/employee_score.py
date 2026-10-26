"""Employee Performance Score (E) Calculation Module.

Computes the bounded domain performance score E in [0, 100] across:
1. Productivity & Task Completion Rate (40%)
2. Staff Retention & Stability (30%)
3. Operational Utilization & Attendance (30%)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def _clamp(val: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(val)))


@dataclass
class EmployeeScoreResult:
    """Encapsulates Employee Performance Domain Score (E) and sub-metrics."""

    employee_score: float  # Bounded [0, 100]
    metrics_breakdown: Dict[str, Any]
    calculation_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseEmployeeScoreCalculator(ABC):
    """Abstract interface for Employee score calculation."""

    @abstractmethod
    def calculate(self, hr_data: Dict[str, Any]) -> EmployeeScoreResult:
        """Calculates the E score from productivity/HR indicators."""
        pass


class EmployeeScoreCalculator(BaseEmployeeScoreCalculator):
    """Production implementation of Employee Performance Score (E) calculator for SMEs."""

    WEIGHT_PRODUCTIVITY: float = 0.40
    WEIGHT_RETENTION: float = 0.30
    WEIGHT_UTILIZATION: float = 0.30

    def calculate(self, hr_data: Dict[str, Any]) -> EmployeeScoreResult:
        """Calculates E score bounded between 0 and 100.

        Supported input keys:
        - productivity_score / task_completion_rate (percentage, default: 85.0)
        - retention_rate / (100 - attrition_rate) (percentage, default: 92.0)
        - attendance_rate / utilization_rate (percentage, default: 94.0)
        """
        # 1. Productivity & Task Completion (40%)
        productivity = float(
            hr_data.get("productivity_score")
            or hr_data.get("task_completion_rate")
            or 85.0
        )
        e_productivity = _clamp(productivity)

        # 2. Staff Retention (30%)
        if "retention_rate" in hr_data:
            retention = float(hr_data["retention_rate"])
        elif "attrition_rate" in hr_data:
            retention = 100.0 - float(hr_data["attrition_rate"])
        else:
            retention = 92.0
        # Retention >= 90% -> 100 pts. Retention 70% -> 50 pts.
        if retention >= 95.0:
            e_retention = 100.0
        else:
            e_retention = _clamp(100.0 - ((95.0 - retention) * 2.5), low=20.0, high=100.0)

        # 3. Operational Utilization & Attendance (30%)
        utilization = float(
            hr_data.get("attendance_rate")
            or hr_data.get("utilization_rate")
            or 94.0
        )
        # 95%+ -> 100 pts. 80% -> 60 pts.
        if utilization >= 95.0:
            e_utilization = 100.0
        else:
            e_utilization = _clamp(utilization * 1.05, low=10.0, high=100.0)

        composite_e = round(
            (self.WEIGHT_PRODUCTIVITY * e_productivity)
            + (self.WEIGHT_RETENTION * e_retention)
            + (self.WEIGHT_UTILIZATION * e_utilization),
            2,
        )

        breakdown = {
            "productivity_score": round(e_productivity, 2),
            "retention_score": round(e_retention, 2),
            "utilization_score": round(e_utilization, 2),
            "raw_inputs": {
                "productivity": productivity,
                "retention": retention,
                "utilization": utilization,
            },
        }

        return EmployeeScoreResult(
            employee_score=composite_e,
            metrics_breakdown=breakdown,
            calculation_metadata={"status": "calculated", "formula": "productivity-retention-utilization weighted"},
        )
