-- Inputs: an existing Ledgerwise D1 database with model_usage records from migration 0002.
-- Outputs: an idempotent side table containing optional per-call USD cost and pricing version.
-- Explanation: Adds versioned cost metadata without altering historical token rows; safe to replay on every application startup.
CREATE TABLE IF NOT EXISTS model_usage_costs (
  usage_id INTEGER PRIMARY KEY REFERENCES model_usage(id) ON DELETE CASCADE,
  cost_usd REAL NOT NULL CHECK (cost_usd >= 0),
  pricing_version TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_model_usage_cost_pricing_version
  ON model_usage_costs(pricing_version);
