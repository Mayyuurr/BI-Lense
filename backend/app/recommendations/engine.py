"""Recommendation Engine & Procurement Restocking Triggers.

Generates actionable business interventions based on domain scores, prediction
thresholds, and procurement restocking rules.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class UrgencyLevel(str, Enum):
    """Urgency severity for recommendations and alerts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ActionableRecommendation:
    """Standardized decision support recommendation."""

    domain: str
    title: str
    description: str
    urgency: UrgencyLevel
    trigger_reason: str
    suggested_action: str


@dataclass
class RestockTrigger:
    """Procurement restocking trigger event."""

    sku_id: str
    product_name: str
    current_stock: float
    reorder_point: float
    suggested_order_quantity: float
    is_triggered: bool


class RecommendationEngine:
    """Rule and threshold evaluation engine for cross-domain decision support."""

    def evaluate_procurement_restock(
        self,
        current_stock: float,
        reorder_point: float,
        safety_stock: float,
        lead_time_days: int,
        daily_demand: float,
        sku_id: str = "SKU-UNKNOWN",
        product_name: str = "Product",
    ) -> RestockTrigger:
        """Evaluates deterministic restocking-trigger logic for procurement."""
        reorder_threshold = reorder_point or (daily_demand * lead_time_days + safety_stock)
        is_triggered = current_stock <= reorder_threshold
        suggested_qty = max(0.0, (reorder_threshold * 2) - current_stock) if is_triggered else 0.0

        return RestockTrigger(
            sku_id=sku_id,
            product_name=product_name,
            current_stock=current_stock,
            reorder_point=reorder_threshold,
            suggested_order_quantity=suggested_qty,
            is_triggered=is_triggered,
        )

    def generate_recommendations(
        self,
        scores: Dict[str, Optional[float]],
        predictions: Dict[str, Optional[float]],
    ) -> List[ActionableRecommendation]:
        """Synthesizes domain metrics into a prioritized list of recommendations."""
        recommendations: List[ActionableRecommendation] = []

        # Placeholder interface for scoring threshold evaluations
        if scores.get("inventory") is not None and (scores["inventory"] or 0) < 50.0:
            recommendations.append(
                ActionableRecommendation(
                    domain="inventory",
                    title="Low Inventory Health Score",
                    description="Inventory turnover or stockout risk indicates supply chain pressure.",
                    urgency=UrgencyLevel.HIGH,
                    trigger_reason="Inventory Score below baseline threshold.",
                    suggested_action="Review procurement replenishment schedules and buffer stock levels.",
                )
            )

        return recommendations
