"""Business Scoring Service.

Coordinates calculation of domain scores (S, I, F, E) and composite Bp score.
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.scoring.sales_score import SalesScoreCalculator
from app.scoring.inventory_score import InventoryScoreCalculator
from app.scoring.finance_score import FinanceScoreCalculator
from app.scoring.employee_score import EmployeeScoreCalculator
from app.scoring.bp_score import BPScoreCalculator, BusinessPerformanceResult
from app.models.database_models import BusinessScoreRecord
from app.core.logging_config import logger


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
        """Calculates domain scores and the composite Business Performance score Bp."""
        s_score = self.sales_calc.calculate(sales_data or {}).sales_score if sales_data else None
        i_score = self.inventory_calc.calculate(inventory_data or {}).inventory_score if inventory_data else None
        f_score = self.finance_calc.calculate(finance_data or {}).finance_score if finance_data else None
        e_score = self.employee_calc.calculate(hr_data or {}).employee_score if hr_data else None

        bp_result = self.bp_calc.calculate_bp(
            sales_score=s_score,
            inventory_score=i_score,
            finance_score=f_score,
            employee_score=e_score,
        )

        if self.db:
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
            except Exception as exc:
                logger.warning(f"Failed to persist score record: {exc}")
                if self.db:
                    self.db.rollback()

        return bp_result
