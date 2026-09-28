# Liquidity Risk & Cash Flow Stress Testing – Treasury Dashboard

Python + MySQL + Streamlit.

## Files
- `schema.sql`   – MySQL tables
- `seed_data.py` – creates the database and loads sample data
- `stress.py`    – the stress-test maths (pandas)
- `app.py`       – the Streamlit dashboard (with editable tables)
- `db.py`        – MySQL connection

## Run it
1. Install and start MySQL, then:  `pip install -r requirements.txt`
2. Set your MySQL login (or edit the defaults in `db.py`):
   - Windows: `set MYSQL_USER=root` and `set MYSQL_PASSWORD=yourpassword`
   - Mac/Linux: `export MYSQL_USER=root MYSQL_PASSWORD=yourpassword`
3. `python seed_data.py`
4. `streamlit run app.py`

## How it works
- Sidebar sliders apply a stress: fewer inflows, more outflows, bigger asset
  haircuts, late collections.
- Liquidity buffer = asset value x (1 - haircut).
- Total liquidity = cash balance + buffer. Survival horizon = first day it
  drops below `min_liquidity`.
- LCR (30 day) = buffer / (outflows - min(inflows, 75% of outflows)).
- Every number (cash flows, assets, haircuts, scenarios, settings) can be edited
  in the "Edit Data" tab and is saved back to MySQL.
