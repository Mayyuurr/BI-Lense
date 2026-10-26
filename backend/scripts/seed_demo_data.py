"""Database Seeding Script for Demo & Milestone Evaluations.

Seeds realistic SME business performance histories, hybrid predictions,
and explanation logs so that API endpoints (/scores/history, /scores/latest)
return realistic historical time-series data for demonstration.

Usage:
    cd backend
    .venv\\Scripts\\python scripts/seed_demo_data.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import random

# Ensure app package is importable
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, Base, engine, check_db_connection
from app.models.database_models import (
    BusinessScoreRecord,
    PredictionRecord,
    ExplanationLog,
)
from app.core.logging_config import logger


def seed_demo_data() -> None:
    """Populates database with 30-day realistic historical business intelligence data."""
    print("=" * 60)
    print("BI-Lense SME Decision Intelligence — Demo Data Seeder")
    print("=" * 60)

    # 1. Check connection
    if not check_db_connection():
        print("[WARNING] PostgreSQL is not currently running on localhost:5432.")
        print("          If you are running in production/staging, start PostgreSQL.")
        print("          Skipping seed insertion gracefully.")
        return

    # 2. Create tables if they do not exist
    print("[1/3] Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        # Check existing count
        existing_scores = session.query(BusinessScoreRecord).count()
        if existing_scores >= 30:
            print(f"[INFO] Database already contains {existing_scores} score records. Clearing old demo records...")
            session.query(BusinessScoreRecord).delete()
            session.query(PredictionRecord).delete()
            session.query(ExplanationLog).delete()
            session.commit()

        print("[2/3] Generating 30-day historical Business Performance (Bp) records...")
        now = datetime.now(timezone.utc)

        # Baseline scores with realistic SME operational trend
        base_s = 82.0
        base_i = 74.0
        base_f = 79.0
        base_e = 85.0

        for day in range(30, 0, -1):
            calc_time = now - timedelta(days=day)

            # Realistic random walk for trend visualization
            s_val = round(max(50.0, min(100.0, base_s + random.uniform(-4.0, 4.0))), 2)
            i_val = round(max(40.0, min(100.0, base_i + random.uniform(-6.0, 5.0))), 2)
            f_val = round(max(50.0, min(100.0, base_f + random.uniform(-3.0, 3.0))), 2)
            e_val = round(max(60.0, min(100.0, base_e + random.uniform(-2.0, 3.0))), 2)

            # Bp = (S + I + F + E) / 4
            bp_val = round((s_val + i_val + f_val + e_val) / 4.0, 2)
            tier = "OPTIMAL" if bp_val >= 85.0 else "STABLE" if bp_val >= 70.0 else "WATCHLIST" if bp_val >= 50.0 else "CRITICAL"

            record = BusinessScoreRecord(
                sales_score=s_val,
                inventory_score=i_val,
                finance_score=f_val,
                employee_score=e_val,
                bp_score=bp_val,
                score_metadata={
                    "components_evaluated": 4,
                    "alert_tier": tier,
                    "primary_bottleneck": "inventory" if i_val < min(s_val, f_val, e_val) else "finance",
                    "key_strength": "employee" if e_val > max(s_val, i_val, f_val) else "sales",
                },
                calculated_at=calc_time,
            )
            session.add(record)

        print("[3/3] Generating sample hybrid prediction records and explanation logs...")
        # Add sample prediction runs
        sales_pred = PredictionRecord(
            domain="sales",
            target_metric="next_period_demand",
            predicted_value=138.45,
            model_weights={"w_rf": 0.1812, "w_xgb": 0.3143, "w_ann": 0.5046},
            raw_predictions={"RF": 125.0, "XGB": 139.2, "ANN": 142.8},
            prediction_timestamp=now - timedelta(hours=2),
        )
        inv_pred = PredictionRecord(
            domain="inventory",
            target_metric="stockout_probability",
            predicted_value=0.22,
            model_weights={"w_rf": 0.0000, "w_xgb": 0.8749, "w_ann": 0.1251},
            raw_predictions={"RF": 0.18, "XGB": 0.21, "ANN": 0.29},
            prediction_timestamp=now - timedelta(hours=2),
        )
        session.add(sales_pred)
        session.add(inv_pred)

        # Add sample explanation log
        expl_log = ExplanationLog(
            domain="sales",
            shap_summary={
                "top_positive": [{"human_label": "30-Day Moving Average Demand", "shap_value": 24.2}],
                "top_negative": [{"human_label": "Net Customer Price", "shap_value": -12.8}],
            },
            natural_language_explanation=(
                "The hybrid ensemble projects next-period demand of 138.45 units. "
                "Demand momentum is predominantly accelerated by 30-Day Baseline Moving Average Demand (+24.20), "
                "while being constrained by Net Customer Price (-12.80)."
            ),
            created_at=now - timedelta(hours=2),
        )
        session.add(expl_log)

        session.commit()
        print("\n[SUCCESS] Successfully seeded:")
        print("  - 30 Historical BusinessScoreRecord rows")
        print("  - 2 Sample PredictionRecord rows")
        print("  - 1 Sample ExplanationLog row")
        print("=" * 60)
    except Exception as exc:
        session.rollback()
        print(f"[ERROR] Seeding failed: {exc}")
    finally:
        session.close()


if __name__ == "__main__":
    seed_demo_data()
