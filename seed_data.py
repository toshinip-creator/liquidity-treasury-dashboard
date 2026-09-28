"""Creates the MySQL database + tables and fills them with sample data.
Run once:  python seed_data.py     (re-running resets everything)"""
from datetime import date, timedelta
import numpy as np
import pandas as pd
from sqlalchemy import text
from db import get_engine


def make_cash_flows(days=90):
    np.random.seed(42)
    start = date.today()
    rows = []
    for i in range(days):
        d = start + timedelta(days=i)
        if d.weekday() < 5:  # weekdays only
            rows.append((d, "Customer Receipts", "IN", round(np.random.normal(120000, 15000), -2)))
            rows.append((d, "Supplier Payments", "OUT", round(np.random.normal(70000, 10000), -2)))
        if i % 7 == 3:
            rows.append((d, "Other Inflows", "IN", 40000))
        if i % 14 == 10:
            rows.append((d, "Payroll", "OUT", 450000))
        if i % 30 == 5:
            rows.append((d, "Investment Income", "IN", 250000))
        if i % 30 == 1:
            rows.append((d, "Rent & Utilities", "OUT", 180000))
        if i % 30 == 20:
            rows.append((d, "Debt Service", "OUT", 350000))
        if i == 60:
            rows.append((d, "Tax Payment", "OUT", 400000))
    return pd.DataFrame(rows, columns=["flow_date", "category", "direction", "amount"])


def make_assets():
    return pd.DataFrame({
        "asset_name": ["Government Bonds", "Corporate Bonds", "Money Market Funds", "Equities"],
        "market_value": [2500000, 1800000, 1000000, 800000],
        "haircut_pct": [5, 20, 2, 40]})


def make_scenarios():
    return pd.DataFrame({
        "scenario_name": ["Baseline", "Mild Stress", "Moderate Stress", "Severe Stress", "Bank Run"],
        "inflow_shock_pct": [0, 10, 25, 40, 20],
        "outflow_shock_pct": [0, 5, 10, 20, 35],
        "extra_haircut_pct": [0, 5, 10, 15, 10],
        "collection_delay_days": [0, 2, 5, 7, 0]})


def make_settings():
    return pd.DataFrame({
        "setting_name": ["opening_cash", "min_liquidity", "inflow_cap_pct"],
        "setting_value": [1500000, 1000000, 75]})


if __name__ == "__main__":
    admin = get_engine(with_database=False)
    with admin.begin() as conn:
        conn.execute(text("CREATE DATABASE IF NOT EXISTS treasury"))

    engine = get_engine()
    with engine.begin() as conn:
        for statement in open("schema.sql").read().split(";"):
            if statement.strip():
                conn.execute(text(statement))
        make_cash_flows().to_sql("cash_flows", conn, if_exists="append", index=False)
        make_assets().to_sql("liquid_assets", conn, if_exists="append", index=False)
        make_scenarios().to_sql("scenarios", conn, if_exists="append", index=False)
        make_settings().to_sql("settings", conn, if_exists="append", index=False)
    print("Database ready. Now run:  streamlit run app.py")
