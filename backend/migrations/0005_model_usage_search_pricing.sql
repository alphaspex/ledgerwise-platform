-- Inputs: existing model_usage rows, the prior optional model_usage_costs side table, and the user-supplied 2026-11-16 token/search rates.
-- Outputs: idempotent model_usage_pricing rows containing the repriced USD cost, actual searches when recorded, and pricing version.
-- Explanation: Adds per-call web-search accounting and backfills historical token costs; known Module 1 search/enrichment calls receive one historical search each.
CREATE TABLE IF NOT EXISTS model_usage_pricing (
  usage_id INTEGER PRIMARY KEY REFERENCES model_usage(id) ON DELETE CASCADE,
  cost_usd REAL NOT NULL CHECK (cost_usd >= 0),
  searches INTEGER NOT NULL DEFAULT 0 CHECK (searches >= 0),
  pricing_version TEXT NOT NULL
);

INSERT OR IGNORE INTO model_usage_pricing(usage_id,cost_usd,searches,pricing_version)
SELECT
  u.id,
  (
    (u.input_tokens * 0.10 + u.output_tokens * 0.50) / 1000000.0
    + CASE
        WHEN u.module='research' AND u.operation IN ('search','enrichment') THEN 0.0025
        ELSE 0
      END
  ),
  CASE
    WHEN u.module='research' AND u.operation IN ('search','enrichment') THEN 1
    ELSE 0
  END,
  'user-supplied-2026-11-16-v1'
FROM model_usage u;
