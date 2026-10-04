"""Synthetic SME Dataset Generator for BI-Lense Platform.

Generates realistic, mathematically correlated benchmark datasets for:
1. Sales & Demand (`sales.csv`)
2. CRM & Customer Data (`customers.csv`)
3. Inventory Health & Stockout Risk (`inventory.csv`)
4. Finance & Liquidity Risk (`finance.csv`)
5. HR & Operational Productivity (`hr.csv`)

Conforms strictly to docs/DATA_DICTIONARY.md.
"""

import os
import random
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

# Set deterministic random seed for research reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Output directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ML_DATASETS_DIR = BASE_DIR / "ML-experiments" / "datasets"
APP_STORAGE_DIR = BASE_DIR / "data" / "storage"

ML_DATASETS_DIR.mkdir(parents=True, exist_ok=True)
APP_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def generate_customers(num_customers: int = 500) -> pd.DataFrame:
    """Generates CRM customer accounts."""
    print(f"[*] Generating {num_customers} customer accounts...")
    segments = ["Enterprise", "Mid-Market", "Small Biz"]
    segment_weights = [0.20, 0.35, 0.45]

    data = []
    for i in range(1, num_customers + 1):
        cust_id = f"CUST-{i:04d}"
        segment = random.choices(segments, weights=segment_weights)[0]

        if segment == "Enterprise":
            freq_index = round(random.uniform(6.0, 9.8), 2)
            avg_order = round(random.uniform(5000, 25000), 2)
            recency_days = random.randint(1, 14)
            ltv = round(avg_order * random.uniform(15, 60), 2)
        elif segment == "Mid-Market":
            freq_index = round(random.uniform(3.5, 7.5), 2)
            avg_order = round(random.uniform(1500, 6000), 2)
            recency_days = random.randint(5, 45)
            ltv = round(avg_order * random.uniform(8, 30), 2)
        else:  # Small Biz
            freq_index = round(random.uniform(1.0, 4.5), 2)
            avg_order = round(random.uniform(300, 1800), 2)
            recency_days = random.randint(10, 90)
            ltv = round(avg_order * random.uniform(3, 15), 2)

        data.append({
            "customer_id": cust_id,
            "customer_segment": segment,
            "purchase_frequency_index": freq_index,
            "avg_order_value": avg_order,
            "days_since_last_purchase": recency_days,
            "total_lifetime_value": ltv,
        })

    return pd.DataFrame(data)


def generate_sales(customers_df: pd.DataFrame, num_skus: int = 100, num_days: int = 730) -> pd.DataFrame:
    """Generates transactional sales records over 2 years (~10,000+ rows)."""
    print(f"[*] Generating sales transactions for {num_skus} SKUs over {num_days} days...")
    categories = ["Hardware", "Raw Materials", "Finished Goods", "Packaging", "Electronics"]
    categories_per_sku = {f"SKU-{i:03d}": random.choice(categories) for i in range(1, num_skus + 1)}
    base_price_per_sku = {f"SKU-{i:03d}": round(random.uniform(25, 450), 2) for i in range(1, num_skus + 1)}
    base_demand_per_sku = {f"SKU-{i:03d}": random.randint(15, 120) for i in range(1, num_skus + 1)}

    start_date = datetime(2024, 1, 1)
    customer_ids = customers_df["customer_id"].tolist()

    records = []
    tx_counter = 1

    # Keep historical demand tracker per SKU for lag calculation
    sku_daily_history = {f"SKU-{i:03d}": [] for i in range(1, num_skus + 1)}

    for day_idx in range(num_days):
        current_date = start_date + timedelta(days=day_idx)
        day_of_week = current_date.weekday()
        month = current_date.month

        # Weekend seasonality multiplier
        weekend_mult = 0.65 if day_of_week in [5, 6] else 1.05
        # Q4 holiday seasonality multiplier
        holiday_mult = 1.25 if month in [11, 12] else 1.0

        for sku_idx in range(1, num_skus + 1):
            sku_id = f"SKU-{sku_idx:03d}"
            base_d = base_demand_per_sku[sku_id]
            price = base_price_per_sku[sku_id]
            category = categories_per_sku[sku_id]

            # Promotion random trigger
            is_promo = 1 if random.random() < 0.12 else 0
            discount = round(random.uniform(0.05, 0.25), 2) if is_promo else 0.0
            discount_mult = 1.0 + (discount * 1.8)

            # Calculate units sold with realistic variance
            noise = random.gauss(1.0, 0.15)
            units = max(0, int(base_d * weekend_mult * holiday_mult * discount_mult * noise))

            sku_daily_history[sku_id].append(units)

            # Lags
            history = sku_daily_history[sku_id]
            lag_1 = history[-2] if len(history) >= 2 else float(units)
            lag_7 = history[-8] if len(history) >= 8 else float(lag_1)
            lag_30 = history[-31] if len(history) >= 31 else float(lag_7)
            rolling_30 = float(np.mean(history[-30:])) if len(history) >= 30 else float(units)

            # Correlated future target (next day demand)
            next_demand = max(0, int(rolling_30 * random.gauss(1.02, 0.12)))

            # Sample customer
            cust = random.choice(customer_ids)

            records.append({
                "transaction_id": f"TX-{tx_counter:07d}",
                "date": current_date.strftime("%Y-%m-%d"),
                "sku_id": sku_id,
                "product_category": category,
                "units_sold": units,
                "unit_price": price,
                "discount_rate": discount,
                "promotional_flag": is_promo,
                "customer_id": cust,
                "sales_lag_1": float(lag_1),
                "sales_lag_7": float(lag_7),
                "sales_lag_30": float(lag_30),
                "rolling_avg_30": round(rolling_30, 2),
                "day_of_week": day_of_week,
                "month": month,
                "next_period_demand": next_demand,
            })
            tx_counter += 1

    # Subsample to a realistic transaction size if total is huge, but keep ~12,000 dense rows
    df = pd.DataFrame(records)
    return df.sample(n=min(len(df), 12000), random_state=SEED).sort_values("date").reset_index(drop=True)


def generate_inventory(sales_df: pd.DataFrame, num_skus: int = 100, num_audits: int = 1500) -> pd.DataFrame:
    """Generates inventory health and stockout audit snapshots."""
    print(f"[*] Generating {num_audits} inventory audit records...")
    suppliers = [f"SUPP-{i:03d}" for i in range(1, 51)]
    supplier_lead_times = {s: random.randint(3, 21) for s in suppliers}
    sku_supplier = {f"SKU-{i:03d}": random.choice(suppliers) for i in range(1, num_skus + 1)}

    records = []
    audit_dates = sorted(sales_df["date"].unique())[-90:]  # last 90 snapshot days

    for i in range(1, num_audits + 1):
        date_str = random.choice(audit_dates)
        sku_id = f"SKU-{random.randint(1, num_skus):03d}"
        supp_id = sku_supplier[sku_id]
        lead_time = supplier_lead_times[supp_id]

        # Delay latency
        delay_days = round(max(0.0, random.gauss(1.2, 1.5)), 1)
        reorder_lvl = random.randint(30, 150)
        safety_stk = int(reorder_lvl * 0.35)

        # Injected demand from sales
        pred_demand = round(random.uniform(15, 130), 1)

        # Current stock with realistic variations
        current_stk = random.randint(0, int(reorder_lvl * 2.2))
        turnover = round(random.uniform(3.5, 14.0), 2)

        # Correlated binary target: stockout occurs if current buffer cannot cover demand across lead time + delay
        expected_demand_during_replenishment = (pred_demand / 7.0) * (lead_time + delay_days)
        stockout_flag = 1 if current_stk < (expected_demand_during_replenishment - safety_stk * 0.5) else 0

        records.append({
            "inventory_record_id": f"INV-{i:06d}",
            "date": date_str,
            "sku_id": sku_id,
            "current_stock": current_stk,
            "reorder_level": reorder_lvl,
            "safety_stock": safety_stk,
            "supplier_id": supp_id,
            "lead_time_days": lead_time,
            "historical_delivery_delay_days": delay_days,
            "inventory_turnover_ratio": turnover,
            "predicted_sales_demand": pred_demand,
            "stockout_before_delivery": stockout_flag,
        })

    return pd.DataFrame(records)


def generate_finance(num_months: int = 36) -> pd.DataFrame:
    """Generates monthly financial balance and cash flow statements."""
    print(f"[*] Generating {num_months} monthly financial statements...")
    start_date = datetime(2023, 1, 1)

    records = []
    base_rev = 185000.0

    for m in range(num_months):
        curr_date = start_date + timedelta(days=m * 30.5)
        period_id = curr_date.strftime("%Y-%m")

        # Revenue with modest annual growth
        growth = (1.0 + (m * 0.008))
        rev = round(base_rev * growth * random.uniform(0.90, 1.15), 2)

        # Margins & OpEx
        gross_margin = round(random.uniform(0.38, 0.52), 4)
        cogs = round(rev * (1.0 - gross_margin), 2)
        fixed_opex = round(rev * random.uniform(0.28, 0.42), 2)
        net_margin = round((rev - cogs - fixed_opex) / rev, 4)

        # Cash & Receivables
        cash_reserves = round(random.uniform(35000, 160000), 2)
        ar_total = round(rev * random.uniform(0.20, 0.45), 2)
        ar_aging_45 = round(ar_total * random.uniform(0.10, 0.38), 2)
        d_to_e = round(random.uniform(0.40, 1.85), 2)
        burn_rate = round(fixed_opex * random.uniform(0.85, 1.15), 2)

        # Correlated deficit target: cash reserves cannot cover next 30-day OpEx obligations
        deficit_flag = 1 if (cash_reserves + (ar_total * 0.4)) < fixed_opex else 0

        records.append({
            "period_id": period_id,
            "date": curr_date.strftime("%Y-%m-%d"),
            "revenue": rev,
            "operating_expenses": fixed_opex,
            "gross_margin_ratio": gross_margin,
            "net_margin_ratio": net_margin,
            "liquid_cash_reserves": cash_reserves,
            "accounts_receivable": ar_total,
            "ar_aging_over_45_days": ar_aging_45,
            "debt_to_equity_ratio": d_to_e,
            "monthly_burn_rate": burn_rate,
            "cash_deficit_30d": deficit_flag,
        })

    return pd.DataFrame(records)


def generate_hr(num_employees: int = 100, num_weeks: int = 15) -> pd.DataFrame:
    """Generates employee productivity and task delivery logs."""
    print(f"[*] Generating {num_employees * num_weeks} employee weekly task logs...")
    departments = ["Engineering", "Operations", "Sales", "Logistics"]
    emp_depts = {f"EMP-{i:03d}": random.choice(departments) for i in range(1, num_employees + 1)}

    records = []
    log_id = 1
    start_date = datetime(2026, 1, 1)

    for w in range(num_weeks):
        week_date = start_date + timedelta(weeks=w)
        for i in range(1, num_employees + 1):
            emp_id = f"EMP-{i:03d}"
            dept = emp_depts[emp_id]

            assigned = random.randint(8, 30)
            absent_rate = round(random.betavariate(1.5, 20.0), 3)  # skewed low

            # Turnaround time
            base_turnaround = 2.4 if dept == "Engineering" else 1.2
            turnaround = round(max(0.5, random.gauss(base_turnaround, 0.6)), 2)

            # Workload density & task completion
            workload_density = round(assigned / (1.0 - min(0.8, absent_rate) + 0.1), 2)
            completion_rate = max(0.4, min(1.0, random.gauss(0.88 - (absent_rate * 0.5), 0.10)))
            completed = int(assigned * completion_rate)

            perf_index = round(max(40.0, min(100.0, (completion_rate * 80) + (100 - absent_rate * 100) * 0.2)), 1)

            # Correlated delay target (days beyond deadline)
            delay = round(max(0.0, (workload_density * 0.08) + (absent_rate * 6.0) - (perf_index * 0.02) + random.gauss(0.5, 0.4)), 2)

            records.append({
                "log_id": f"HRLOG-{log_id:06d}",
                "employee_id": emp_id,
                "department": dept,
                "tasks_assigned": assigned,
                "tasks_completed": completed,
                "avg_completion_time_days": turnaround,
                "absenteeism_rate": absent_rate,
                "workload_density_ratio": workload_density,
                "team_performance_index": perf_index,
                "task_delay_days": delay,
            })
            log_id += 1

    return pd.DataFrame(records)


def main():
    print("=================================================================")
    print("       BI-Lense Synthetic SME Benchmark Dataset Generator        ")
    print("=================================================================")

    # 1. Customers
    customers_df = generate_customers(num_customers=500)
    # 2. Sales
    sales_df = generate_sales(customers_df, num_skus=100, num_days=730)
    # 3. Inventory
    inventory_df = generate_inventory(sales_df, num_skus=100, num_audits=1500)
    # 4. Finance
    finance_df = generate_finance(num_months=36)
    # 5. HR
    hr_df = generate_hr(num_employees=100, num_weeks=15)

    datasets = {
        "customers.csv": customers_df,
        "sales.csv": sales_df,
        "inventory.csv": inventory_df,
        "finance.csv": finance_df,
        "hr.csv": hr_df,
    }

    # Save to both ML-experiments and backend storage
    for filename, df in datasets.items():
        ml_path = ML_DATASETS_DIR / filename
        storage_path = APP_STORAGE_DIR / filename

        df.to_csv(ml_path, index=False)
        df.to_csv(storage_path, index=False)
        print(f"[+] Saved {filename:15s} -> {len(df):6d} rows | {len(df.columns):2d} cols to {ml_path.name}")

    print("=================================================================")
    print("[OK] All 5 synthetic SME datasets generated successfully!")
    print("=================================================================")


if __name__ == "__main__":
    main()
