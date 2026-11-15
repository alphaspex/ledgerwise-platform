# Inputs: tick state, completed worker results, queue snapshots, and usage events from the orchestrator.
# Outputs: updated tick state, committed queue transitions, refreshed status, and dispatched work.
# Explanation: Implements one bounded phase of the single-writer orchestration cycle.
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any
from .orchestrator_helpers import _now

class TickPlanMixin:
    def _tick_plan_outreach(self, state: dict[str, Any]) -> None:
        apollo_candidates = state["apollo_candidates"]
        draft_candidates = state["draft_candidates"]
        m2_pending = state["m2_pending"]
        write_statements = state["write_statements"]
        reconcile = state["reconcile"]
        stale_m2_rows = state["stale_m2_rows"]
        completion_signals = state["completion_signals"]
        for candidate in apollo_candidates:
            if self.settings.apollo_enabled:
                write_statements.append({
                    "sql": "INSERT INTO module_2_queue(type,company_id,message_id,state) SELECT 'draft',?,NULL,'pending' WHERE NOT EXISTS (SELECT 1 FROM module_2_queue WHERE company_id=? AND type='draft' AND message_id IS NULL)",
                    "params": [int(candidate["id"]), int(candidate["id"])],
                })
        for candidate in draft_candidates:
            write_statements.append({
                "sql": "INSERT INTO module_2_queue(type,company_id,message_id,state) SELECT 'draft',?,NULL,'pending' WHERE NOT EXISTS (SELECT 1 FROM module_2_queue WHERE company_id=? AND type='draft' AND state IN ('pending','processing'))",
                "params": [int(candidate["id"]), int(candidate["id"])],
            })

        m2_claims = []
        for item in m2_pending:
            if item.get("type") == "draft" and (
                bool(item.get("do_not_contact"))
                or item.get("company_status") not in {"approved", "human_approved"}
            ):
                write_statements.append({
                    "sql": "UPDATE module_2_queue SET state='done',claimed_at=NULL WHERE id=? AND state='pending'",
                    "params": [int(item["queue_id"])],
                })
                continue
            statement_index = len(write_statements)
            write_statements.append({
                "sql": "UPDATE module_2_queue SET state='processing',claimed_at=? WHERE id=? AND state='pending'",
                "params": [_now(), int(item["queue_id"])],
            })
            m2_claims.append((statement_index, item))

        if reconcile:
            write_statements.append({
                "sql": "UPDATE module_2_queue SET state=CASE WHEN attempts+1>=? THEN 'failed' ELSE 'pending' END,attempts=attempts+1,claimed_at=NULL WHERE state='processing' AND claimed_at < ?",
                "params": [self.settings.max_attempts, (datetime.now(timezone.utc) - timedelta(seconds=self.settings.lease_seconds)).isoformat()],
            })
            for stale in stale_m2_rows:
                if int(stale.get("attempts", 0)) + 1 < self.settings.max_attempts:
                    continue
                stale_type = stale.get("type")
                stale_company_id = int(stale["company_id"])
                if stale_type == "send":
                    message_id = int(stale.get("message_id") or 0)
                    write_statements.extend([
                        {"sql": "UPDATE thread_messages SET status='failed',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [message_id]},
                        {"sql": "UPDATE companies SET email_status='failed_contact',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [stale_company_id]},
                        {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)", "params": [stale_company_id, "Email delivery worker expired after the allowed retries."]},
                    ])
                    if message_id:
                        completion_signals.append((message_id, "failed"))
                elif stale_type == "draft" and stale.get("contact_email") is not None:
                    write_statements.extend([
                        {"sql": "UPDATE companies SET email_status='failed_contact',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [stale_company_id]},
                        {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)", "params": [stale_company_id, "Email drafting worker expired after the allowed retries."]},
                    ])
                elif stale_type == "reply":
                    write_statements.extend([
                        {"sql": "UPDATE companies SET thread_state='needs_human',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [stale_company_id]},
                        {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'unsure_answer',?)", "params": [stale_company_id, "Automatic reply worker expired after the allowed retries."]},
                    ])
                elif stale_type == "draft":
                    write_statements.append({"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)", "params": [stale_company_id, "Apollo lookup worker expired; enter a contact manually."]})
            write_statements.append({"sql": "DELETE FROM auth_events WHERE created_at < datetime('now', ?)", "params": [f"-{self.settings.auth_events_retention_days} days"]})

        state.update({"write_statements": write_statements, "m2_claims": m2_claims})
