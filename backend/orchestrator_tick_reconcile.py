# Inputs: tick state, completed worker results, queue snapshots, and usage events from the orchestrator.
# Outputs: updated tick state, committed queue transitions, refreshed status, and dispatched work.
# Explanation: Applies one completed worker result without performing D1 I/O.
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import time
from typing import Any
from .orchestrator_helpers import _now

class TickReconcileMixin:
    def _tick_reconcile_state(self, state: dict[str, Any]) -> None:
        reconcile = state["reconcile"]
        run = state["run"]
        search_queue = state["search_queue"]
        enrichment_queue = state["enrichment_queue"]
        url_queue = state["url_queue"]
        human_queue = state["human_queue"]
        system_status = state["system_status"]
        domains = state["domains"]
        pending_companies = state["pending_companies"]
        queue_changed = state["queue_changed"]
        if reconcile:
            processing_cutoff = (datetime.now(timezone.utc) - timedelta(seconds=self.settings.lease_seconds)).isoformat()
            expired = [
                item for item in enrichment_queue + url_queue + search_queue
                if item.get("state") == "processing" and (
                    self.tick_count == 1 or str(item.get("claimed_at") or "") < processing_cutoff
                )
            ]
            for item in expired:
                item["attempts"] = int(item.get("attempts", 0)) + 1
                if item in search_queue:
                    item["state"] = "pending" if item["attempts"] < self.settings.max_attempts else "dropped"
                elif item in enrichment_queue:
                    item["state"] = "pending" if item["attempts"] < self.settings.max_attempts else "dropped"
                else:
                    item["state"] = "pending" if item["attempts"] < self.settings.max_attempts else "dropped"
                item["claimed_at"] = None

        exhausted_enrichment = [item for item in enrichment_queue if item.get("state") == "dropped"]
        exhausted_urls = [item for item in url_queue if item.get("state") == "dropped"]
        if exhausted_enrichment:
            exhausted_ids = {int(item["company_id"]) for item in exhausted_enrichment}
            enrichment_queue = [item for item in enrichment_queue if item.get("state") != "dropped"]
            queue_changed = True
        else:
            exhausted_ids = set()
        if exhausted_urls:
            exhausted_url_ids = {int(item["company_id"]) for item in exhausted_urls}
            url_queue = [item for item in url_queue if item.get("state") != "dropped"]
            queue_changed = True
        else:
            exhausted_url_ids = set()

        for company in pending_companies:
            company_id = int(company["id"])
            if not run or run.get("status") != "running":
                continue
            if company_id in exhausted_ids or company_id in exhausted_url_ids:
                continue
            has_research = bool(company.get("research_data"))
            target_queue = url_queue if has_research else enrichment_queue
            exists = any(int(item.get("company_id", -1)) == company_id for item in target_queue)
            if not exists:
                target_queue.append({"company_id": company_id, "state": "pending", "attempts": 0, "claimed_at": None})
                queue_changed = True

        if run and run.get("status") == "running":
            counts = system_status.get("counts", {})
            approved = int(counts.get("approved", 0)) + int(counts.get("human_approved", 0))
            pending = max(int(counts.get("pending", 0)), len(pending_companies))
            deficit = int(run.get("target_approved") or self.settings.target_approved) - (approved + pending)
            if deficit > 0 and not search_queue and len(enrichment_queue) < 2 * self.settings.llm_concurrency:
                search_queue.append({
                    "job_id": int(time.time_ns() % 2_000_000_000),
                    "run_id": int(run["id"]),
                    "n": min(deficit, self.settings.max_search_batch),
                    "state": "pending",
                    "attempts": 0,
                    "claimed_at": None,
                })
                queue_changed = True

        write_statements: list[dict[str, Any]] = []
        completion_signals: list[tuple[int, str]] = []
        if reconcile and run and run.get("status") == "running":
            current_counts = system_status.get("counts", {})
            approved_total = int(current_counts.get("approved", 0)) + int(current_counts.get("human_approved", 0))
            if approved_total >= int(run.get("target_approved") or self.settings.target_approved):
                write_statements.append({
                    "sql": "UPDATE research_runs SET status='done' WHERE id=? AND status='running'",
                    "params": [int(run["id"])],
                })
                run["status"] = "done"
        for item in exhausted_enrichment:
            company_id = int(item["company_id"])
            write_statements.extend([
                {"sql": "UPDATE companies SET status='failed_enrichment',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='pending'", "params": [company_id]},
                {"sql": "UPDATE domain_memory SET status='rejected' WHERE domain=(SELECT domain FROM companies WHERE id=?)", "params": [company_id]},
            ])
        for item in exhausted_urls:
            company_id = int(item["company_id"])
            write_statements.append({
                "sql": "UPDATE companies SET status='needs_human_review',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='pending'",
                "params": [company_id],
            })
            if not any(int(existing.get("company_id", -1)) == company_id for existing in human_queue):
                human_queue.append({"company_id": company_id, "added_at": _now()})
        state.update({
            "run": run,
            "search_queue": search_queue,
            "enrichment_queue": enrichment_queue,
            "url_queue": url_queue,
            "human_queue": human_queue,
            "system_status": system_status,
            "queue_changed": queue_changed,
            "exhausted_enrichment": exhausted_enrichment,
            "exhausted_urls": exhausted_urls,
            "exhausted_ids": exhausted_ids,
            "exhausted_url_ids": exhausted_url_ids,
            "write_statements": write_statements,
            "completion_signals": completion_signals
        })
