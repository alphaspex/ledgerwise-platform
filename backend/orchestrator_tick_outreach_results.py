# Inputs: tick state, completed worker results, queue snapshots, and usage events from the orchestrator.
# Outputs: updated tick state, committed queue transitions, refreshed status, and dispatched work.
# Explanation: Applies one completed worker result without performing D1 I/O.
from __future__ import annotations
from typing import Any
from .orchestrator_helpers import _json

class TickOutreachResultsMixin:
    def _apply_apollo_result(self, state: dict[str, Any], item: dict[str, Any]) -> None:
        result = item.get("result", {})
        queue_id = item.get("queue_id")
        company_id = item.get("company_id")
        m2_pending = state.get("m2_pending", [])
        write_statements = state["write_statements"]
        for _branch_once in (None,):
            if result.get("worker_error"):
                attempts = int(next((q.get("attempts", 0) for q in m2_pending if int(q["queue_id"]) == int(queue_id)), 0)) + 1
                state = "pending" if attempts < self.settings.max_attempts else "failed"
                write_statements.append({"sql": "UPDATE module_2_queue SET state=?,attempts=?,claimed_at=NULL WHERE id=?", "params": [state, attempts, int(queue_id)]})
                if state == "failed":
                    write_statements.append({"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)", "params": [int(company_id), "Apollo contact lookup failed repeatedly. Enter a contact manually."]})
                continue
            if result.get("outcome") == "found":
                write_statements.append({
                    "sql": "UPDATE companies SET contact_email=?,contact_name=?,contact_role=?,contact_source='apollo',updated_at=CURRENT_TIMESTAMP WHERE id=? AND contact_source IS NULL",
                    "params": [result["email"], result.get("name"), result.get("role", "unknown"), int(company_id)],
                })
            else:
                detail = "Apollo found multiple matching people; select one and enter the chosen email manually." if result.get("outcome") == "multiple" else "No verified named contact was found; enter a contact manually."
                candidates_text = _json(result.get("candidates", []))[:3000]
                write_statements.append({
                    "sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)",
                    "params": [int(company_id), detail + (" Candidates: " + candidates_text if candidates_text else "")],
                })
            write_statements.append({"sql": "UPDATE module_2_queue SET state='done',claimed_at=NULL WHERE id=?", "params": [int(queue_id)]})
        state["write_statements"] = write_statements

    def _apply_draft_result(self, state: dict[str, Any], item: dict[str, Any]) -> None:
        result = item.get("result", {})
        queue_id = item.get("queue_id")
        company_id = item.get("company_id")
        m2_pending = state.get("m2_pending", [])
        write_statements = state["write_statements"]
        for _branch_once in (None,):
            if result.get("worker_error"):
                attempts = int(next((q.get("attempts", 0) for q in m2_pending if int(q["queue_id"]) == int(queue_id)), 0)) + 1
                state = "pending" if attempts < self.settings.max_attempts else "failed"
                write_statements.append({"sql": "UPDATE module_2_queue SET state=?,attempts=?,claimed_at=NULL WHERE id=?", "params": [state, attempts, int(queue_id)]})
                if state == "failed":
                    write_statements.extend([
                        {"sql": "UPDATE companies SET email_status='failed_contact',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                        {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)", "params": [int(company_id), "Email drafting failed after the allowed retries."]},
                    ])
                continue
            if result.get("memory_missing"):
                write_statements.extend([
                    {"sql": "UPDATE companies SET memory=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [_json(result.get("memory", {"facts": [], "audit": {}})), int(company_id)]},
                    {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)", "params": [int(company_id), "Fewer than three verified company facts were available; first email is not ready."]},
                    {"sql": "UPDATE module_2_queue SET state='done',claimed_at=NULL WHERE id=?", "params": [int(queue_id)]},
                ])
            elif result.get("body"):
                write_statements.extend([
                    {"sql": "UPDATE companies SET memory=?,email_status='pending_review',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [_json(result["memory"]), int(company_id)]},
                    {"sql": "INSERT INTO thread_messages(company_id,sender_type,body,status,subject) VALUES (?,'agent',?,'pending_review',?)", "params": [int(company_id), result["body"], "A quick question about " + str(result.get("domain", ""))]},
                    {"sql": "UPDATE module_2_queue SET state='done',claimed_at=NULL WHERE id=?", "params": [int(queue_id)]},
                ])
            else:
                write_statements.extend([
                    {"sql": "UPDATE companies SET email_status='failed_contact',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                    {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)", "params": [int(company_id), "The first email draft could not satisfy the required content rules."]},
                    {"sql": "UPDATE module_2_queue SET state='failed',claimed_at=NULL WHERE id=?", "params": [int(queue_id)]},
                ])
        state["write_statements"] = write_statements

    def _apply_send_result(self, state: dict[str, Any], item: dict[str, Any]) -> None:
        result = item.get("result", {})
        queue_id = item.get("queue_id")
        company_id = item.get("company_id")
        m2_pending = state.get("m2_pending", [])
        write_statements = state["write_statements"]
        completion_signals = state["completion_signals"]
        for _branch_once in (None,):
            status = result.get("status", "failed")
            if status == "retry":
                attempts = int(next((q.get("attempts", 0) for q in m2_pending if int(q["queue_id"]) == int(queue_id)), 0)) + 1
                if attempts < self.settings.max_attempts:
                    write_statements.append({
                        "sql": "UPDATE module_2_queue SET state='pending',attempts=?,claimed_at=NULL WHERE id=?",
                        "params": [attempts, int(queue_id)],
                    })
                else:
                    write_statements.extend([
                        {"sql": "UPDATE thread_messages SET status='failed',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(result.get("message_id") or 0)]},
                        {"sql": "UPDATE companies SET email_status='failed_contact',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                        {"sql": "UPDATE module_2_queue SET state='failed',attempts=?,claimed_at=NULL WHERE id=?", "params": [attempts, int(queue_id)]},
                        {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)", "params": [int(company_id), "Email delivery failed after the allowed retries."]},
                    ])
                    if result.get("message_id"):
                        completion_signals.append((int(result["message_id"]), "failed"))
            else:
                write_statements.extend([
                    {"sql": "UPDATE thread_messages SET status=?,provider_message_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [status, result.get("provider_message_id"), int(result.get("message_id") or 0)]},
                    {"sql": "UPDATE companies SET email_status=CASE WHEN ?='sent' AND email_status IN ('approved','drafting','pending_review') THEN 'sent' WHEN ?='failed' AND email_status IN ('approved','drafting','pending_review') THEN 'failed_contact' ELSE email_status END,thread_state=CASE WHEN ?='sent' AND thread_state='inactive' THEN 'auto' ELSE thread_state END,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [status, status, status, int(company_id)]},
                    {"sql": "UPDATE module_2_queue SET state=?,claimed_at=NULL WHERE id=?", "params": ["done" if status in ("sent", "blocked_by_do_not_contact") else "failed", int(queue_id)]},
                ])
                if status == "failed":
                    write_statements.append({"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)", "params": [int(company_id), "Email delivery failed after the allowed retries."]})
                if result.get("message_id"):
                    completion_signals.append((int(result["message_id"]), status))
        state["write_statements"] = write_statements
        state["completion_signals"] = completion_signals
