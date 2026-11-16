-- Inputs: an existing Ledgerwise D1 database with thread_messages and Resend inbound email webhook events.
-- Outputs: deduplicated inbound email event records and a unique index for Resend provider message IDs.
-- Explanation: Makes inbound-email webhook retries idempotent and records the exact message linked to each received email.
CREATE TABLE IF NOT EXISTS inbound_email_events (
  id INTEGER PRIMARY KEY,
  event_id TEXT NOT NULL UNIQUE,
  email_id TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'ignored')),
  company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
  message_id INTEGER REFERENCES thread_messages(id) ON DELETE SET NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_inbound_email_status ON inbound_email_events(status, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_thread_provider_message_id ON thread_messages(provider_message_id);
