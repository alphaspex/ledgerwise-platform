# Inputs: tick state, completed worker results, queue snapshots, and usage events from the orchestrator.
# Outputs: updated tick state, committed queue transitions, refreshed status, and dispatched work.
# Explanation: Applies one completed worker result without performing D1 I/O.
from __future__ import annotations
from typing import Any
from .integrations import normalize_domain
from .orchestrator_helpers import _json

class TickResearchResultsMixin:
    def _apply_search_result(self, state: dict[str, Any], item: dict[str, Any]) -> None:
        result = item.get("result", {})
        queue_id = item.get("queue_id")
        company_id = item.get("company_id")
        m2_pending = state.get("m2_pending", [])
        search_queue = state["search_queue"]
        system_status = state["system_status"]
        write_statements = state["write_statements"]
        queue_changed = state["queue_changed"]
        for _branch_once in (None,):
            entry = next((q for q in search_queue if q.get("job_id") == queue_id), None)
            if result.get("worker_error"):
                if entry:
                    entry["attempts"] = int(entry.get("attempts", 0)) + 1
                    if entry["attempts"] < self.settings.max_attempts:
                        entry["state"] = "pending"
                        entry["claimed_at"] = None
                    else:
                        search_queue = [q for q in search_queue if q.get("job_id") != queue_id]
                queue_changed = True
                continue
            search_queue = [entry for entry in search_queue if entry.get("job_id") != queue_id]
            queue_changed = True
            for raw_domain in result.get("domains", [])[: self.settings.max_search_batch]:
                try:
                    domain = normalize_domain(str(raw_domain))
                except ValueError:
                    continue
                write_statements.extend([
                    {
                        "sql": "INSERT INTO companies(run_id,domain,status) SELECT ?,?,'pending' WHERE NOT EXISTS (SELECT 1 FROM domain_memory WHERE domain=?) ON CONFLICT(domain) DO NOTHING",
                        "params": [int(result.get("run_id", 0)), domain, domain],
                    },
                    {"sql": "INSERT OR IGNORE INTO domain_memory(domain,status) SELECT domain,'pending' FROM companies WHERE domain=?", "params": [domain]},
                ])
            system_status["searches"] = int(system_status.get("searches", 0)) + 1
        state["search_queue"] = search_queue
        state["system_status"] = system_status
        state["write_statements"] = write_statements
        state["queue_changed"] = queue_changed

    def _apply_enrichment_result(self, state: dict[str, Any], item: dict[str, Any]) -> None:
        result = item.get("result", {})
        queue_id = item.get("queue_id")
        company_id = item.get("company_id")
        m2_pending = state.get("m2_pending", [])
        enrichment_queue = state["enrichment_queue"]
        url_queue = state["url_queue"]
        write_statements = state["write_statements"]
        queue_changed = state["queue_changed"]
        for _branch_once in (None,):
            entry = next((q for q in enrichment_queue if int(q.get("company_id", -1)) == int(company_id)), None)
            if entry:
                enrichment_queue.remove(entry)
            queue_changed = True
            if result.get("worker_error"):
                attempts = int(entry.get("attempts", 0)) + 1 if entry else self.settings.max_attempts
                if attempts < self.settings.max_attempts:
                    enrichment_queue.append({"company_id": int(company_id), "state": "pending", "attempts": attempts, "claimed_at": None})
                else:
                    write_statements.extend([
                        {"sql": "UPDATE companies SET status='failed_enrichment',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                        {"sql": "UPDATE domain_memory SET status='rejected' WHERE domain=(SELECT domain FROM companies WHERE id=?)", "params": [int(company_id)]},
                    ])
            elif result.get("valid"):
                research = {
                    "reasons": result["reasons"],
                    "sources": [{"url": url, "result": "untested", "status": None} for url in result["source_urls"]],
                }
                write_statements.append({
                    "sql": "UPDATE companies SET score=?,research_data=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='pending'",
                    "params": [result["score"], _json(research), int(company_id)],
                })
                url_queue.append({"company_id": int(company_id), "state": "pending", "attempts": 0, "claimed_at": None})
            else:
                attempts = int(entry.get("attempts", 0)) + 1 if entry else 1
                if attempts < self.settings.max_attempts:
                    enrichment_queue.append({"company_id": int(company_id), "state": "pending", "attempts": attempts, "claimed_at": None})
                else:
                    write_statements.extend([
                        {"sql": "UPDATE companies SET status='failed_enrichment',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                        {"sql": "UPDATE domain_memory SET status='rejected' WHERE domain=(SELECT domain FROM companies WHERE id=?)", "params": [int(company_id)]},
                    ])
        state["enrichment_queue"] = enrichment_queue
        state["url_queue"] = url_queue
        state["write_statements"] = write_statements
        state["queue_changed"] = queue_changed
