# Inputs: tick state, completed worker results, queue snapshots, and usage events from the orchestrator.
# Outputs: updated tick state, committed queue transitions, refreshed status, and dispatched work.
# Explanation: Applies one completed worker result without performing D1 I/O.
from __future__ import annotations
from typing import Any
from .orchestrator_helpers import _json

class TickReplyResultsMixin:
    def _apply_reply_result(self, state: dict[str, Any], item: dict[str, Any]) -> None:
        result = item.get("result", {})
        queue_id = item.get("queue_id")
        company_id = item.get("company_id")
        m2_pending = state.get("m2_pending", [])
        write_statements = state["write_statements"]
        completion_signals = state["completion_signals"]
        for _branch_once in (None,):
            if result.get("worker_error"):
                attempts = int(next((q.get("attempts", 0) for q in m2_pending if int(q["queue_id"]) == int(queue_id)), 0)) + 1
                state = "pending" if attempts < self.settings.max_attempts else "failed"
                write_statements.append({"sql": "UPDATE module_2_queue SET state=?,attempts=?,claimed_at=NULL WHERE id=?", "params": [state, attempts, int(queue_id)]})
                if state == "failed":
                    write_statements.extend([
                        {"sql": "UPDATE companies SET thread_state='needs_human',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                        {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'unsure_answer',?)", "params": [int(company_id), "Automatic reply failed after the allowed retries. Human review is required."]},
                    ])
                continue
            write_statements.append({"sql": "UPDATE module_2_queue SET state='done',claimed_at=NULL WHERE id=?", "params": [int(queue_id)]})
            if result.get("stop"):
                write_statements.extend([
                    {"sql": "UPDATE companies SET do_not_contact=1,thread_state='needs_human',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                    {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'do_not_contact',?)", "params": [int(company_id), "Prospect requested no further contact."]},
                ])
            elif result.get("body"):
                inbound_message_id = int(next((q.get("message_id") for q in m2_pending if int(q["queue_id"]) == int(queue_id)), 0) or 0)
                write_statements.extend([
                    {"sql": "INSERT INTO thread_messages(company_id,sender_type,body,status,tool_calls,in_reply_to_message_id) VALUES (?,'agent',?,'approved',?,?)", "params": [int(company_id), result["body"], _json(result.get("tool_calls", [])), inbound_message_id or None]},
                ])
                write_statements.append({
                    "sql": "INSERT INTO module_2_queue(type,company_id,message_id,state) VALUES ('send',?,last_insert_rowid(),'pending')",
                    "params": [int(company_id)],
                })
                booking = result.get("booking")
                if booking:
                    write_statements.append({
                        "sql": "INSERT INTO bookings(company_id,cal_booking_uid,scheduled_at,status,source) VALUES (?,?,?,'booked','agent') ON CONFLICT(cal_booking_uid) DO NOTHING",
                        "params": [int(company_id), booking["uid"], booking["scheduled_at"]],
                    })
                if result.get("needs_human"):
                    write_statements.extend([
                        {"sql": "UPDATE companies SET thread_state='needs_human',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                        {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'unsure_answer',?)", "params": [int(company_id), result.get("human_reason") or "The agent escalated this conversation for human review."]},
                    ])

        state["write_statements"] = write_statements
        state["completion_signals"] = completion_signals
