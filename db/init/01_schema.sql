-- ============================================================
-- ETF Monitor — Database Schema
-- TimescaleDB (PostgreSQL extension)
-- docker-entrypoint-initdb.d — idempotent via IF NOT EXISTS
-- ============================================================

-- TimesaleDB extention enable
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;


CREATE TABLE IF NOT EXISTS prices (
	date          DATE            NOT NULL,
	stock_name    TEXT            NOT NULL,  
	close_price   NUMERIC(12, 4)  NOT NULL,
	PRIMARY KEY (date, stock_name)
);

SELECT create_hypertable(
	'prices',
	'date',
	if_not_exists => TRUE,
	migrate_date => TRUE
);

CREATE INDEX IF NOT EXISTS idx_prices_stock_name_date
	ON prices (stock_name, date DESC);

-- session_id is a migration bridge — swap for user_id FK when auth lands
CREATE TABLE IF NOT EXISTS etfs (
	id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
	session_id  UUID        NOT NULL,
	name    TEXT        NOT NULL,
	uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now() --FUTURE FEATURE, add uploaded time to each ETF
);

CREATE INDEX IF NOT EXISTS idx_etfs_session_id
  	ON etfs(session_id);

CREATE TABLE IF NOT EXISTS etf_constituents (
	etf_id      UUID          NOT NULL REFERENCES etfs(id) on DELETE CASCADE,
	stock_name  TEXT          NOT NULL,
	weight      NUMERIC(8, 6) NOT NULL,
	PRIMARY KEY (etf_id, stock_name)
);

CREATE INDEX IF NOT EXISTS idx_etf_constituents_etf_id
	ON etf_constituents (etf_id);
