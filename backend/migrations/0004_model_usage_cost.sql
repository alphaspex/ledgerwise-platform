-- Inputs: an existing Ledgerwise D1 database with model_usage records from migration 0002.
-- Outputs: nullable per-call USD cost and pricing-version columns for transparent model spend accounting.
-- Explanation: Adds optional cost metadata without changing historical token records or inventing prices for unpriced calls.
ALTER TABLE model_usage ADD COLUMN cost_usd REAL;
ALTER TABLE model_usage ADD COLUMN pricing_version TEXT;
CREATE INDEX IF NOT EXISTS idx_model_usage_pricing_version ON model_usage(pricing_version, created_at);
