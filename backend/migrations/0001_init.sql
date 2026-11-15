-- Inputs: a new Cloudflare D1 SQLite database and the Ledgerwise Module 1, 2, and 3 data model.
-- Outputs: auth, research, company, contact, queue, thread, booking, and notification tables with required indexes.
-- Explanation: Creates the complete initial schema; all D1 flags are stored as integers and serialized as JSON booleans by the API.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash TEXT NOT NULL,
  is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS password_codes (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  code_hash TEXT NOT NULL,
  purpose TEXT NOT NULL CHECK (purpose IN ('change', 'reset', 'invite')),
  attempts INTEGER NOT NULL DEFAULT 0,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_codes_user ON password_codes(user_id, purpose, created_at DESC);

CREATE TABLE IF NOT EXISTS auth_events (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  event TEXT NOT NULL,
  ip TEXT,
  user_agent TEXT,
  detail TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_auth_events_time ON auth_events(created_at);

CREATE TABLE IF NOT EXISTS research_runs (
  id INTEGER PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'paused', 'done')),
  selection TEXT NOT NULL,
  target_approved INTEGER NOT NULL DEFAULT 30,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS module_1_queues (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  version INTEGER NOT NULL DEFAULT 0,
  search_queue TEXT NOT NULL DEFAULT '[]',
  enrichment_queue TEXT NOT NULL DEFAULT '[]',
  url_check_queue TEXT NOT NULL DEFAULT '[]',
  human_review_queue TEXT NOT NULL DEFAULT '[]',
  system_status TEXT NOT NULL DEFAULT '{}',
  db_health TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY,
  run_id INTEGER NOT NULL REFERENCES research_runs(id),
  domain TEXT NOT NULL UNIQUE,
  score INTEGER CHECK (score IS NULL OR score BETWEEN 0 AND 10),
  status TEXT NOT NULL DEFAULT 'pending',
  research_data TEXT,
  contact_email TEXT,
  contact_name TEXT,
  contact_role TEXT CHECK (contact_role IS NULL OR contact_role IN ('founder', 'coo', 'finance', 'unknown')),
  contact_source TEXT CHECK (contact_source IS NULL OR contact_source IN ('manual', 'apollo')),
  memory TEXT,
  email_status TEXT NOT NULL DEFAULT 'not_started',
  thread_state TEXT NOT NULL DEFAULT 'inactive',
  do_not_contact INTEGER NOT NULL DEFAULT 0 CHECK (do_not_contact IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_companies_run_status ON companies(run_id, status);
CREATE INDEX IF NOT EXISTS idx_companies_email_status ON companies(status, email_status);
CREATE INDEX IF NOT EXISTS idx_companies_dnc ON companies(do_not_contact);

CREATE TABLE IF NOT EXISTS domain_memory (
  domain TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS thread_messages (
  id INTEGER PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  sender_type TEXT NOT NULL CHECK (sender_type IN ('agent', 'prospect', 'human')),
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'sent',
  tool_calls TEXT,
  subject TEXT,
  in_reply_to_message_id INTEGER REFERENCES thread_messages(id),
  provider_message_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_thread_company ON thread_messages(company_id, id);
CREATE INDEX IF NOT EXISTS idx_thread_status ON thread_messages(status);

CREATE TABLE IF NOT EXISTS module_2_queue (
  id INTEGER PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('draft', 'reply', 'send')),
  company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  message_id INTEGER REFERENCES thread_messages(id) ON DELETE CASCADE,
  state TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending', 'processing', 'done', 'failed')),
  attempts INTEGER NOT NULL DEFAULT 0,
  claimed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_m2_state_type ON module_2_queue(state, type, id);
CREATE INDEX IF NOT EXISTS idx_m2_company_type ON module_2_queue(company_id, type, message_id);

CREATE TABLE IF NOT EXISTS bookings (
  id INTEGER PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  cal_booking_uid TEXT NOT NULL UNIQUE,
  scheduled_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'booked' CHECK (status IN ('booked', 'cancelled', 'rescheduled', 'completed')),
  source TEXT NOT NULL CHECK (source IN ('agent', 'prospect_link')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_bookings_scheduled ON bookings(scheduled_at, status);

CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  reason TEXT NOT NULL CHECK (reason IN ('unsure_answer', 'do_not_contact', 'booking_conflict', 'contact_missing')),
  body TEXT,
  read INTEGER NOT NULL DEFAULT 0 CHECK (read IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notif_unread ON notifications(read) WHERE read = 0;
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);
