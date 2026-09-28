"""Core liquidity stress-test logic (pure pandas, no database needed)."""
import pandas as pd

NO_STRESS = {"inflow_shock_pct": 0, "outflow_shock_pct": 0,
             "extra_haircut_pct": 0, "collection_delay_days": 0}


def run_scenario(flows, assets, settings, scenario, horizon=90):
    f = flows.copy()
    f["flow_date"] = pd.to_datetime(f["flow_date"])
    f["amount"] = f["amount"].astype(float)
    start = f["flow_date"].min()
    is_in = f["direction"] == "IN"

    # 1. Apply the stress to the cash flows
    f.loc[is_in, "amount"] *= 1 - scenario["inflow_shock_pct"] / 100
    f.loc[~is_in, "amount"] *= 1 + scenario["outflow_shock_pct"] / 100
    f.loc[is_in, "flow_date"] += pd.Timedelta(days=int(scenario["collection_delay_days"]))

    # 2. Build a daily cash ladder
    days = pd.date_range(start, periods=horizon)
    inflows = f[is_in].groupby("flow_date")["amount"].sum().reindex(days, fill_value=0)
    outflows = f[~is_in].groupby("flow_date")["amount"].sum().reindex(days, fill_value=0)
    ladder = pd.DataFrame({"inflows": inflows, "outflows": outflows})
    ladder["net_flow"] = ladder["inflows"] - ladder["outflows"]
    ladder["cash_balance"] = settings["opening_cash"] + ladder["net_flow"].cumsum()

    # 3. Liquidity buffer = assets after haircuts (stressed haircut is capped at 100%)
    haircut = (assets["haircut_pct"] + scenario["extra_haircut_pct"]).clip(0, 100) / 100
    buffer = (assets["market_value"] * (1 - haircut)).sum()
    ladder["total_liquidity"] = ladder["cash_balance"] + buffer

    # 4. Survival horizon: first day liquidity falls below the minimum required
    breach = ladder[ladder["total_liquidity"] < settings["min_liquidity"]]
    survival_day = None if breach.empty else (breach.index[0] - start).days + 1

    # 5. 30-day Liquidity Coverage Ratio (inflows capped, like Basel LCR)
    first30 = ladder.iloc[:30]
    out30 = first30["outflows"].sum()
    in30 = min(first30["inflows"].sum(), out30 * settings["inflow_cap_pct"] / 100)
    net30 = out30 - in30
    lcr = buffer / net30 * 100 if net30 > 0 else None

    return {"ladder": ladder, "buffer": buffer, "survival_day": survival_day,
            "lowest_liquidity": ladder["total_liquidity"].min(), "lcr": lcr}
