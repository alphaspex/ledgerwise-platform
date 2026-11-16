-- Inputs: an existing Ledgerwise D1 database with the initial schema and successful Muse Responses API usage events.
-- Outputs: model_usage table and indexes for per-call model, module, operation, company, run, and token accounting.
-- Explanation: Adds durable Muse token accounting without changing an already-applied initial migration.
CREATE TABLE IF NOT EXISTS model_usage (
  id INTEGER PRIMARY KEY,
  model TEXT NOT NULL,
  module TEXT NOT NULL,
  operation TEXT NOT NULL,
  company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
  run_id INTEGER REFERENCES research_runs(id) ON DELETE SET NULL,
  input_tokens INTEGER NOT NULL DEFAULT 0 CHECK (input_tokens >= 0),
  output_tokens INTEGER NOT NULL DEFAULT 0 CHECK (output_tokens >= 0),
  reasoning_tokens INTEGER NOT NULL DEFAULT 0 CHECK (reasoning_tokens >= 0 AND reasoning_tokens <= output_tokens),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_model_usage_run ON model_usage(run_id, created_at);
CREATE INDEX IF NOT EXISTS idx_model_usage_company ON model_usage(company_id, created_at);
CREATE INDEX IF NOT EXISTS idx_model_usage_module ON model_usage(module, created_at);
