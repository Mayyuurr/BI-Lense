"""Composite Business Performance Score (Bp) Module.

Implements the multi-criteria SME executive health formulation:
    Bp = w_S * S + w_I * I + w_F * F + w_E * E
where:
- S: Sales & Demand Performance Score [0, 100]
- I: Inventory & Supply Chain Resilience Score [0, 100]
- F: Financial Health & Liquidity Score [0, 100]
- E: Workforce Productivity & Stability Score [0, 100]

Key Features:
- Dynamic Missing Domain Weight Redistribution: Proportional normalization ensures partial data
  does not penalize the business health score.
- Executive Health Tiers: OPTIMAL (>=85), STABLE (70-85), WATCHLIST (50-70), CRITICAL (<50).
- Automatic Bottleneck & Driver Attribution: Identifies primary risk domain and primary strength.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


ALERT_TIER_OPTIMAL = "OPTIMAL"
ALERT_TIER_STABLE = "STABLE"
ALERT_TIER_WATCHLIST = "WATCHLIST"
ALERT_TIER_CRITICAL = "CRITICAL"


@dataclass
class BusinessPerformanceResult:
    """Encapsulates the aggregate Business Performance Score (Bp) and domain components."""

    bp_score: float  # Bounded [0, 100]
    sales_score: Optional[float]
    inventory_score: Optional[float]
    finance_score: Optional[float]
    employee_score: Optional[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def alert_tier(self) -> str:
        """Returns the executive health alert tier."""
        return self.metadata.get("alert_tier", ALERT_TIER_CRITICAL)

    def to_dict(self) -> Dict[str, Any]:
        """Converts result into a clean API response dictionary."""
        return {
            "bp_score": round(self.bp_score, 2),
            "sales_score": round(self.sales_score, 2) if self.sales_score is not None else None,
            "inventory_score": round(self.inventory_score, 2) if self.inventory_score is not None else None,
            "finance_score": round(self.finance_score, 2) if self.finance_score is not None else None,
            "employee_score": round(self.employee_score, 2) if self.employee_score is not None else None,
            "alert_tier": self.alert_tier,
            "metadata": self.metadata,
        }


class BPScoreCalculator:
    """Calculates overall Business Performance Score (Bp) across the 4 SME domains."""

    DEFAULT_WEIGHTS: Dict[str, float] = {
        "sales": 0.25,
        "inventory": 0.25,
        "finance": 0.25,
        "employee": 0.25,
    }

    def __init__(self, domain_weights: Optional[Dict[str, float]] = None) -> None:
        self.domain_weights = domain_weights or dict(self.DEFAULT_WEIGHTS)

    @staticmethod
    def get_alert_tier(bp_score: float) -> str:
        """Categorizes Bp score into four executive operating tiers."""
        if bp_score >= 85.0:
            return ALERT_TIER_OPTIMAL
        elif bp_score >= 70.0:
            return ALERT_TIER_STABLE
        elif bp_score >= 50.0:
            return ALERT_TIER_WATCHLIST
        else:
            return ALERT_TIER_CRITICAL

    def calculate_bp(
        self,
        sales_score: Optional[float] = None,
        inventory_score: Optional[float] = None,
        finance_score: Optional[float] = None,
        employee_score: Optional[float] = None,
    ) -> BusinessPerformanceResult:
        """Calculates Bp with dynamic weight redistribution for missing domains.

        If a domain has not been integrated or data is temporarily missing,
        the remaining available domains scale proportionally to maintain a 100% total weight:
            w_i' = w_i / sum_{k in Available} w_k
        """
        score_map: Dict[str, Optional[float]] = {
            "sales": sales_score,
            "inventory": inventory_score,
            "finance": finance_score,
            "employee": employee_score,
        }

        # Filter active domains
        active_domains: Dict[str, float] = {
            domain: float(score)
            for domain, score in score_map.items()
            if score is not None
        }

        if not active_domains:
            return BusinessPerformanceResult(
                bp_score=0.0,
                sales_score=None,
                inventory_score=None,
                finance_score=None,
                employee_score=None,
                metadata={
                    "components_evaluated": 0,
                    "alert_tier": ALERT_TIER_CRITICAL,
                    "message": "No domain scores provided",
                    "weights_applied": {},
                },
            )

        # Calculate sum of baseline weights for available domains
        active_weight_sum = sum(self.domain_weights.get(d, 0.25) for d in active_domains)
        if active_weight_sum <= 0:
            active_weight_sum = len(active_domains) * 0.25

        # Normalize weights so sum(w_i') == 1.0
        normalized_weights: Dict[str, float] = {
            domain: (self.domain_weights.get(domain, 0.25) / active_weight_sum)
            for domain in active_domains
        }

        # Compute weighted aggregate Bp
        composite_bp = sum(
            normalized_weights[d] * active_domains[d]
            for d in active_domains
        )
        composite_bp = round(max(0.0, min(100.0, composite_bp)), 2)

        # Identify key bottleneck and primary strength
        sorted_domains = sorted(active_domains.items(), key=lambda item: item[1])
        primary_bottleneck = sorted_domains[0][0] if sorted_domains else None
        key_strength = sorted_domains[-1][0] if sorted_domains else None

        alert_tier = self.get_alert_tier(composite_bp)

        metadata: Dict[str, Any] = {
            "components_evaluated": len(active_domains),
            "alert_tier": alert_tier,
            "primary_bottleneck": primary_bottleneck,
            "bottleneck_score": active_domains[primary_bottleneck] if primary_bottleneck else None,
            "key_strength": key_strength,
            "strength_score": active_domains[key_strength] if key_strength else None,
            "weights_applied": {d: round(w, 4) for d, w in normalized_weights.items()},
        }

        return BusinessPerformanceResult(
            bp_score=composite_bp,
            sales_score=sales_score,
            inventory_score=inventory_score,
            finance_score=finance_score,
            employee_score=employee_score,
            metadata=metadata,
        )
