"""Inventory Score (I) Calculation Module.

Computes the bounded domain performance score I in [0, 100] across:
1. Stockout Risk Resilience (45%)
2. Inventory Turnover Efficiency (30%)
3. Buffer Safety & Reorder Coverage (25%)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def _clamp(val: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(val)))


@dataclass
class InventoryScoreResult:
    """Encapsulates Inventory Domain Score (I) and sub-metrics."""

    inventory_score: float  # Bounded [0, 100]
    metrics_breakdown: Dict[str, Any]
    calculation_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseInventoryScoreCalculator(ABC):
    """Abstract interface for Inventory score calculation."""

    @abstractmethod
    def calculate(self, inventory_data: Dict[str, Any]) -> InventoryScoreResult:
        """Calculates the I score from raw/aggregated inventory indicators."""
        pass


class InventoryScoreCalculator(BaseInventoryScoreCalculator):
    """Production implementation of Inventory Score (I) calculator for SMEs."""

    WEIGHT_STOCKOUT_RESILIENCE: float = 0.45
    WEIGHT_TURNOVER_EFFICIENCY: float = 0.30
    WEIGHT_BUFFER_COVERAGE: float = 0.25

    # Benchmark turnover for SMEs (times per year)
    OPTIMAL_TURNOVER_BENCHMARK: float = 8.0

    def calculate(self, inventory_data: Dict[str, Any]) -> InventoryScoreResult:
        """Calculates I score bounded between 0 and 100.

        Supported input keys:
        - stockout_probability (float [0, 1], default: 0.15)
        - inventory_turnover_ratio (float, default: 8.0)
        - buffer_coverage_ratio / (current_stock / safety_stock) (float, default: 1.5)
        - current_stock, reorder_level, safety_stock
        """
        # 1. Stockout Resilience (45%)
        stockout_prob = float(inventory_data.get("stockout_probability", 0.15))
        stockout_prob = max(0.0, min(1.0, stockout_prob))
        i_stockout = (1.0 - stockout_prob) * 100.0

        # 2. Turnover Efficiency (30%)
        # Benchmark = 8.0x. Deviation penalizes tied-up capital or extreme stockouts
        turnover = float(inventory_data.get("inventory_turnover_ratio", self.OPTIMAL_TURNOVER_BENCHMARK))
        turnover_diff = abs(turnover - self.OPTIMAL_TURNOVER_BENCHMARK)
        i_turnover = _clamp(100.0 - (turnover_diff * 7.5), low=20.0, high=100.0)

        # 3. Buffer Coverage Ratio (25%)
        # Ideal buffer ratio is between 1.0 and 2.5
        if "buffer_coverage_ratio" in inventory_data:
            buffer_ratio = float(inventory_data["buffer_coverage_ratio"])
        else:
            stock = float(inventory_data.get("current_stock", 50.0))
            safety = float(inventory_data.get("safety_stock", 20.0))
            buffer_ratio = stock / (safety + 1e-4) if safety > 0 else 1.5

        if 1.0 <= buffer_ratio <= 2.5:
            i_buffer = 100.0
        elif buffer_ratio < 1.0:
            # Dangerously low buffer
            i_buffer = _clamp(buffer_ratio * 100.0)
        else:
            # Overstocked / capital locked up
            i_buffer = _clamp(100.0 - ((buffer_ratio - 2.5) * 20.0), low=30.0)

        # Composite score
        composite_i = round(
            (self.WEIGHT_STOCKOUT_RESILIENCE * i_stockout)
            + (self.WEIGHT_TURNOVER_EFFICIENCY * i_turnover)
            + (self.WEIGHT_BUFFER_COVERAGE * i_buffer),
            2,
        )

        breakdown = {
            "stockout_resilience_score": round(i_stockout, 2),
            "turnover_efficiency_score": round(i_turnover, 2),
            "buffer_coverage_score": round(i_buffer, 2),
            "raw_inputs": {
                "stockout_probability": stockout_prob,
                "inventory_turnover_ratio": turnover,
                "buffer_coverage_ratio": buffer_ratio,
            },
        }

        return InventoryScoreResult(
            inventory_score=composite_i,
            metrics_breakdown=breakdown,
            calculation_metadata={"status": "calculated", "formula": "resilience-turnover-buffer weighted"},
        )
