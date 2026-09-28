import pandas as pd
import streamlit as st
from sqlalchemy import text
from db import get_engine
from stress import run_scenario, NO_STRESS

st.set_page_config(page_title="Treasury Liquidity Dashboard", layout="wide")
engine = get_engine()


def load(table):
    return pd.read_sql(f"SELECT * FROM {table}", engine)


def save(df, table):
    """Replace the table contents with the edited data."""
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {table}"))
        df.dropna().to_sql(table, conn, if_exists="append", index=False)
    st.success(f"Saved to MySQL table '{table}'")


flows = load("cash_flows")
flows["flow_date"] = pd.to_datetime(flows["flow_date"]).dt.date
assets = load("liquid_assets")
scenarios = load("scenarios")
settings_df = load("settings")
settings = dict(zip(settings_df["setting_name"], settings_df["setting_value"]))

st.title("💧 Treasury Liquidity Risk & Cash Flow Stress Testing")
dash_tab, data_tab = st.tabs(["📊 Dashboard", "✏️ Edit Data (saved to MySQL)"])

# ---------------- Sidebar: scenario controls ----------------
st.sidebar.header("Stress scenario")
name = st.sidebar.selectbox("Start from preset", scenarios["scenario_name"])
row = scenarios[scenarios["scenario_name"] == name].iloc[0]
scenario = {
    "inflow_shock_pct": st.sidebar.slider("Inflow shortfall (%)", 0, 100, int(row["inflow_shock_pct"]), key=f"a{name}"),
    "outflow_shock_pct": st.sidebar.slider("Extra outflows (%)", 0, 100, int(row["outflow_shock_pct"]), key=f"b{name}"),
    "extra_haircut_pct": st.sidebar.slider("Extra asset haircut (%)", 0, 50, int(row["extra_haircut_pct"]), key=f"c{name}"),
    "collection_delay_days": st.sidebar.slider("Collection delay (days)", 0, 30, int(row["collection_delay_days"]), key=f"d{name}"),
}
st.sidebar.caption("Move the sliders to try your own what-if. Preset numbers can be edited in the Edit Data tab.")

# ---------------- Dashboard ----------------
with dash_tab:
    base = run_scenario(flows, assets, settings, NO_STRESS)
    stress = run_scenario(flows, assets, settings, scenario)

    if stress["survival_day"] is None:
        st.success("✅ Liquidity stays above the minimum for the full 90 days.")
    else:
        st.error(f"🚨 Liquidity falls below the minimum on day {stress['survival_day']}.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Survival horizon", "90+ days" if stress["survival_day"] is None else f"{stress['survival_day']} days")
    lcr = stress["lcr"]
    c2.metric("30-day LCR", "n/a" if lcr is None else f"{lcr:,.0f}%",
              None if base["lcr"] is None or lcr is None else f"{lcr - base['lcr']:,.0f} pts vs baseline")
    c3.metric("Liquidity buffer (after haircuts)", f"{stress['buffer']:,.0f}",
              f"{stress['buffer'] - base['buffer']:,.0f} vs baseline")
    c4.metric("Lowest total liquidity", f"{stress['lowest_liquidity']:,.0f}",
              f"{stress['lowest_liquidity'] - base['lowest_liquidity']:,.0f} vs baseline")

    st.subheader("Total liquidity over 90 days")
    chart = pd.DataFrame({
        "Baseline": base["ladder"]["total_liquidity"],
        "Stressed": stress["ladder"]["total_liquidity"],
        "Minimum required": settings["min_liquidity"]})
    st.line_chart(chart)

    left, right = st.columns(2)
    with left:
        st.subheader("Stressed daily net cash flow")
        st.bar_chart(stress["ladder"]["net_flow"])
    with right:
        st.subheader("All scenarios compared")
        results = []
        for _, r in scenarios.iterrows():
            res = run_scenario(flows, assets, settings, r.to_dict())
            results.append({
                "Scenario": r["scenario_name"],
                "Survival (days)": "90+" if res["survival_day"] is None else res["survival_day"],
                "LCR %": None if res["lcr"] is None else round(res["lcr"]),
                "Lowest liquidity": round(res["lowest_liquidity"])})
        st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)

    st.subheader("Cash ladder (stressed)")
    st.dataframe(stress["ladder"].round(0), use_container_width=True)

# ---------------- Editable data ----------------
with data_tab:
    st.info("Edit any number, add or delete rows, then click Save. The dashboard updates immediately.")

    st.subheader("Settings")
    edited = st.data_editor(settings_df, hide_index=True, key="settings")
    if st.button("Save settings"):
        save(edited, "settings"); st.rerun()

    st.subheader("Liquid assets & haircuts")
    edited = st.data_editor(assets, num_rows="dynamic", hide_index=True, key="assets")
    if st.button("Save assets"):
        save(edited, "liquid_assets"); st.rerun()

    st.subheader("Stress scenarios")
    edited = st.data_editor(scenarios, num_rows="dynamic", hide_index=True, key="scenarios")
    if st.button("Save scenarios"):
        save(edited, "scenarios"); st.rerun()

    st.subheader("Expected cash flows (IN = inflow, OUT = outflow)")
    edited = st.data_editor(
        flows, num_rows="dynamic", hide_index=True, key="flows",
        column_config={"direction": st.column_config.SelectboxColumn(options=["IN", "OUT"])})
    if st.button("Save cash flows"):
        save(edited, "cash_flows"); st.rerun()
