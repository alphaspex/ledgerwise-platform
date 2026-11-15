# Inputs: tick state, completed worker results, queue snapshots, and usage events from the orchestrator.
# Outputs: updated tick state, committed queue transitions, refreshed status, and dispatched work.
# Explanation: Applies one completed worker result without performing D1 I/O.
from __future__ import annotations
from typing import Any
from .orchestrator_helpers import _json, _now

class TickURLResultsMixin:
    def _apply_url_result(self, state: dict[str, Any], item: dict[str, Any]) -> None:
        result = item.get("result", {})
        queue_id = item.get("queue_id")
        company_id = item.get("company_id")
        m2_pending = state.get("m2_pending", [])
        url_queue = state["url_queue"]
        human_queue = state["human_queue"]
        write_statements = state["write_statements"]
        queue_changed = state["queue_changed"]
        for _branch_once in (None,):
            url_queue = [q for q in url_queue if int(q.get("company_id", -1)) != int(company_id)]
            queue_changed = True
            bucket = int(result.get("bucket", 2))
            if result.get("worker_error"):
                bucket = 2
            research = result.get("research_data", {})
            if bucket == 1:
                write_statements.extend([
                    {"sql": "UPDATE companies SET status='failed_404',research_data=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [_json(research), int(company_id)]},
                    {"sql": "UPDATE domain_memory SET status='failed_404' WHERE domain=(SELECT domain FROM companies WHERE id=?)", "params": [int(company_id)]},
                ])
            elif bucket == 2:
                write_statements.append(
                    {"sql": "UPDATE companies SET status='needs_human_review',research_data=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [_json(research), int(company_id)]}
                )
                if not any(int(q.get("company_id", -1)) == int(company_id) for q in human_queue):
                    human_queue.append({"company_id": int(company_id), "added_at": _now()})
            else:
                live = sum(1 for source in research.get("sources", []) if source.get("result") == "live")
                status = "approved" if live >= self.settings.min_live_sources else "rejected_low_evidence"
                domain_status = "approved" if status == "approved" else "rejected"
                write_statements.extend([
                    {"sql": "UPDATE companies SET status=?,research_data=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [status, _json(research), int(company_id)]},
                    {"sql": "UPDATE domain_memory SET status=? WHERE domain=(SELECT domain FROM companies WHERE id=?)", "params": [domain_status, int(company_id)]},
                ])
        state["url_queue"] = url_queue
        state["human_queue"] = human_queue
        state["write_statements"] = write_statements
        state["queue_changed"] = queue_changed
