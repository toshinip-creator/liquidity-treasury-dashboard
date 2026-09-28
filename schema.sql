DROP TABLE IF EXISTS cash_flows;
DROP TABLE IF EXISTS liquid_assets;
DROP TABLE IF EXISTS scenarios;
DROP TABLE IF EXISTS settings;

CREATE TABLE cash_flows (
    flow_date DATE NOT NULL,
    category  VARCHAR(50) NOT NULL,
    direction VARCHAR(3) NOT NULL,      -- 'IN' or 'OUT'
    amount    DOUBLE NOT NULL
);

CREATE TABLE liquid_assets (
    asset_name   VARCHAR(50) NOT NULL,
    market_value DOUBLE NOT NULL,
    haircut_pct  DOUBLE NOT NULL        -- % lost when sold in a crisis
);

CREATE TABLE scenarios (
    scenario_name         VARCHAR(50) NOT NULL,
    inflow_shock_pct      DOUBLE NOT NULL,   -- % of inflows that never arrive
    outflow_shock_pct     DOUBLE NOT NULL,   -- % extra outflows
    extra_haircut_pct     DOUBLE NOT NULL,   -- added to every asset haircut
    collection_delay_days INT NOT NULL       -- inflows arrive this many days late
);

CREATE TABLE settings (
    setting_name  VARCHAR(50) PRIMARY KEY,
    setting_value DOUBLE NOT NULL
);
