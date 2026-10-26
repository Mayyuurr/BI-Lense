"""Business Scoring Service.

Coordinates calculation of domain scores (S, I, F, E), dynamic composite Bp scoring,
alert tier classification, and database persistence.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.logging_config import logger
from app.models.database_models import BusinessScoreRecord
from app.scoring.bp_score import (
    BPScoreCalculator,
    BusinessPerformanceResult,
    ALERT_TIER_OPTIMAL,
    ALERT_TIER_STABLE,
    ALERT_TIER_WATCHLIST,
    ALERT_TIER_CRITICAL,
)
from app.scoring.employee_score import EmployeeScoreCalculator
from app.scoring.finance_score import FinanceScoreCalculator
from app.scoring.inventory_score import InventoryScoreCalculator
from app.scoring.sales_score import SalesScoreCalculator


class ScoringService:
    """Service boundary for domain performance and overall Bp scoring."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db
        self.sales_calc = SalesScoreCalculator()
        self.inventory_calc = InventoryScoreCalculator()
        self.finance_calc = FinanceScoreCalculator()
        self.employee_calc = EmployeeScoreCalculator()
        self.bp_calc = BPScoreCalculator()

    def compute_scores(
        self,
        sales_data: Optional[Dict[str, Any]] = None,
        inventory_data: Optional[Dict[str, Any]] = None,
        finance_data: Optional[Dict[str, Any]] = None,
        hr_data: Optional[Dict[str, Any]] = None,
    ) -> BusinessPerformanceResult:
        """Calculates domain scores and composite Business Performance Score Bp."""
        sales_res = self.sales_calc.calculate(sales_data) if sales_data is not None else None
        inv_res = self.inventory_calc.calculate(inventory_data) if inventory_data is not None else None
        fin_res = self.finance_calc.calculate(finance_data) if finance_data is not None else None
        emp_res = self.employee_calc.calculate(hr_data) if hr_data is not None else None

        s_score = sales_res.sales_score if sales_res else None
        i_score = inv_res.inventory_score if inv_res else None
        f_score = fin_res.finance_score if fin_res else None
        e_score = emp_res.employee_score if emp_res else None

        bp_result = self.bp_calc.calculate_bp(
            sales_score=s_score,
            inventory_score=i_score,
            finance_score=f_score,
            employee_score=e_score,
        )

        # Enrich metadata with sub-metric breakdowns
        if bp_result.metadata is not None:
            breakdowns: Dict[str, Any] = {}
            if sales_res:
                breakdowns["sales"] = sales_res.metrics_breakdown
            if inv_res:
                breakdowns["inventory"] = inv_res.metrics_breakdown
            if fin_res:
                breakdowns["finance"] = fin_res.metrics_breakdown
            if emp_res:
                breakdowns["employee"] = emp_res.metrics_breakdown
            bp_result.metadata["domain_breakdowns"] = breakdowns

        # Persist record in database
        if self.db is not None:
            try:
                record = BusinessScoreRecord(
                    sales_score=s_score,
                    inventory_score=i_score,
                    finance_score=f_score,
                    employee_score=e_score,
                    bp_score=bp_result.bp_score,
                    score_metadata=bp_result.metadata,
                )
                self.db.add(record)
                self.db.commit()
                self.db.refresh(record)
                if bp_result.metadata:
                    bp_result.metadata["record_id"] = record.id
            except Exception as exc:
                logger.warning(f"Failed to persist business score record: {exc}")
                if self.db:
                    self.db.rollback()

        return bp_result

    def compute_from_predictions(
        self,
        predicted_sales: Optional[float] = None,
        target_sales: Optional[float] = None,
        stockout_probability: Optional[float] = None,
        inventory_turnover: Optional[float] = None,
        finance_data: Optional[Dict[str, Any]] = None,
        hr_data: Optional[Dict[str, Any]] = None,
    ) -> BusinessPerformanceResult:
        """Utility method to compute Bp directly from hybrid ML model prediction results."""
        sales_data = None
        if predicted_sales is not None:
            sales_data = {
                "predicted_demand": predicted_sales,
                "target_sales": target_sales or (predicted_sales * 1.05),
            }

        inventory_data = None
        if stockout_probability is not None:
            inventory_data = {
                "stockout_probability": stockout_probability,
                "inventory_turnover_ratio": inventory_turnover or 8.0,
            }

        return self.compute_scores(
            sales_data=sales_data,
            inventory_data=inventory_data,
            finance_data=finance_data,
            hr_data=hr_data,
        )

    def get_latest_score(self) -> Optional[Dict[str, Any]]:
        """Retrieves the most recently calculated business score record from the database."""
        if not self.db:
            return None
        try:
            record = (
                self.db.query(BusinessScoreRecord)
                .order_by(desc(BusinessScoreRecord.calculated_at))
                .first()
            )
            if not record:
                return None
            return {
                "id": record.id,
                "bp_score": record.bp_score,
                "sales_score": record.sales_score,
                "inventory_score": record.inventory_score,
                "finance_score": record.finance_score,
                "employee_score": record.employee_score,
                "metadata": record.score_metadata,
                "calculated_at": record.calculated_at.isoformat() if record.calculated_at else None,
            }
        except Exception as exc:
            logger.warning(f"Database query failed for latest score: {exc}")
            return None

    def get_score_history(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Retrieves chronological score history for time-series trend analysis."""
        if not self.db:
            return []
        try:
            records = (
                self.db.query(BusinessScoreRecord)
                .order_by(desc(BusinessScoreRecord.calculated_at))
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "bp_score": r.bp_score,
                    "sales_score": r.sales_score,
                    "inventory_score": r.inventory_score,
                    "finance_score": r.finance_score,
                    "employee_score": r.employee_score,
                    "calculated_at": r.calculated_at.isoformat() if r.calculated_at else None,
                }
                for r in reversed(records)
            ]
        except Exception as exc:
            logger.warning(f"Database query failed for score history: {exc}")
            return []
