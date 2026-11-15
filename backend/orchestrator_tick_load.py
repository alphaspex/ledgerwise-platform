# Inputs: tick state, completed worker results, queue snapshots, and usage events from the orchestrator.
# Outputs: updated tick state, committed queue transitions, refreshed status, and dispatched work.
# Explanation: Implements one bounded phase of the single-writer orchestration cycle.
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any
from .db import rows
from .orchestrator_helpers import _load, _now

class TickLoadMixin:
    async def _tick_load_state(self) -> dict[str, Any]:
        self.tick_count += 1
        reconcile = self.tick_count == 1 or self.tick_count % self.settings.reconcile_every_ticks == 0
        read_statements = [
            {"sql": "INSERT OR IGNORE INTO module_1_queues(id) VALUES (1)"},
            {"sql": "SELECT * FROM module_1_queues WHERE id = 1"},
            {"sql": "SELECT * FROM research_runs WHERE status IN ('running','paused') ORDER BY id DESC LIMIT 1"},
            {"sql": "SELECT domain FROM domain_memory ORDER BY created_at DESC LIMIT ?", "params": [self.settings.exclusion_prompt_limit]},
            {"sql": "SELECT * FROM companies WHERE status = 'pending' AND run_id=(SELECT id FROM research_runs WHERE status IN ('running','paused') ORDER BY id DESC LIMIT 1) ORDER BY id LIMIT 100"},
            {"sql": "SELECT q.id AS queue_id,q.type,q.company_id,q.message_id,q.state,q.attempts,q.claimed_at,c.domain,c.run_id,c.status AS company_status,c.contact_email,c.contact_name,c.contact_role,c.contact_source,c.memory,c.research_data,c.email_status,c.thread_state,c.do_not_contact,tm.body AS message_body,tm.sender_type,tm.status AS message_status,tm.subject,tm.in_reply_to_message_id,(SELECT MAX(prospect.id) FROM thread_messages prospect WHERE prospect.company_id=c.id AND prospect.sender_type='prospect') AS latest_prospect_message_id FROM module_2_queue q JOIN companies c ON c.id=q.company_id LEFT JOIN thread_messages tm ON tm.id=q.message_id WHERE q.state='pending' ORDER BY q.id LIMIT 10"},
            {"sql": "SELECT * FROM (SELECT tm.*, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY id DESC) AS row_num FROM thread_messages tm WHERE company_id IN (SELECT DISTINCT company_id FROM module_2_queue WHERE state='pending' AND type='reply' ORDER BY company_id LIMIT 10)) WHERE row_num <= ? ORDER BY company_id,id", "params": [self.settings.reply_context_window]},
            {"sql": "SELECT c.id,c.domain FROM companies c WHERE c.status IN ('approved','human_approved') AND c.contact_email IS NULL AND c.do_not_contact=0 AND c.email_status='not_started' AND NOT EXISTS (SELECT 1 FROM module_2_queue q WHERE q.company_id=c.id AND q.type='draft' AND q.message_id IS NULL) ORDER BY c.id LIMIT 10"},
            {"sql": "SELECT c.id,c.domain,c.contact_email FROM companies c WHERE c.status IN ('approved','human_approved') AND c.contact_email IS NOT NULL AND c.do_not_contact=0 AND c.email_status='not_started' AND NOT EXISTS (SELECT 1 FROM module_2_queue q WHERE q.company_id=c.id AND q.type='draft' AND q.state IN ('pending','processing')) ORDER BY c.id LIMIT 10"},
            {"sql": "SELECT q.id AS queue_id,q.type,q.company_id,q.message_id,q.attempts,c.domain,c.contact_email FROM module_2_queue q JOIN companies c ON c.id=q.company_id WHERE q.state='processing' AND q.claimed_at < ? ORDER BY q.id", "params": [(datetime.now(timezone.utc) - timedelta(seconds=self.settings.lease_seconds)).isoformat()]},
        ]
        if reconcile:
            read_statements.append({
                "sql": "SELECT status,COUNT(*) AS total FROM companies WHERE run_id=(SELECT id FROM research_runs WHERE status IN ('running','paused') ORDER BY id DESC LIMIT 1) GROUP BY status"
            })
        read_results = await self.db.batch(read_statements)
        queue_row = rows(read_results[1])[0]
        run_rows = rows(read_results[2])
        run = run_rows[0] if run_rows else None
        search_queue = _load(queue_row.get("search_queue"), [])
        enrichment_queue = _load(queue_row.get("enrichment_queue"), [])
        url_queue = _load(queue_row.get("url_check_queue"), [])
        human_queue = _load(queue_row.get("human_review_queue"), [])
        system_status = _load(queue_row.get("system_status"), {})
        domains = [str(row["domain"]) for row in rows(read_results[3])]
        queue_changed = False
        if reconcile and len(read_results) > 10:
            system_status["counts"] = {str(row["status"]): int(row["total"]) for row in rows(read_results[10])}
        if run and system_status.get("run_id") != int(run["id"]):
            current_counts = system_status.get("counts", {})
            system_status = {
                "run_id": int(run["id"]),
                "counts": current_counts,
                "progress": {"search_jobs": 0},
                "tokens": {"in": 0, "out": 0},
                "searches": 0,
            }
            queue_changed = True
        pending_companies = rows(read_results[4])
        m2_pending = rows(read_results[5])
        thread_rows = rows(read_results[6])
        apollo_candidates = rows(read_results[7])
        draft_candidates = rows(read_results[8])
        stale_m2_rows = rows(read_results[9])

        return locals()
