# Inputs: tick state, completed worker results, queue snapshots, and per-call token/cost usage events.
# Outputs: committed queue transitions, persisted model usage, refreshed status, and dispatched work.
# Explanation: Commits orchestration writes and durable per-call model usage through the single D1 writer.
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any
from .db import changes
from .orchestrator_helpers import _json, _now

class TickCommitMixin:
    async def _tick_commit_state(self, state: dict[str, Any]) -> None:
        reconcile = state["reconcile"]
        run = state["run"]
        search_queue = state["search_queue"]
        enrichment_queue = state["enrichment_queue"]
        url_queue = state["url_queue"]
        human_queue = state["human_queue"]
        system_status = state["system_status"]
        domains = state["domains"]
        pending_companies = state["pending_companies"]
        thread_rows = state["thread_rows"]
        write_statements = state["write_statements"]
        queue_changed = state["queue_changed"]
        m2_claims = state["m2_claims"]
        completion_signals = state["completion_signals"]
        queue_row = state["queue_row"]
        claimed_search = []
        for item in (search_queue if run and run.get("status") == "running" else []):
            if item.get("state") == "pending":
                item["state"] = "processing"
                item["claimed_at"] = _now()
                claimed_search.append(item)
                queue_changed = True
                break

        claimed_enrichment = []
        for item in (enrichment_queue if run and run.get("status") == "running" else []):
            if item.get("state") == "pending" and len(claimed_enrichment) < self.settings.llm_concurrency:
                item["state"] = "processing"
                item["claimed_at"] = _now()
                claimed_enrichment.append(item)
                queue_changed = True

        claimed_urls = []
        for item in (url_queue if run and run.get("status") == "running" else []):
            if item.get("state") == "pending" and len(claimed_urls) < self.settings.http_concurrency:
                item["state"] = "processing"
                item["claimed_at"] = _now()
                claimed_urls.append(item)
                queue_changed = True

        usage_batch = list(self.usage_pending)
        for event in usage_batch:
            write_statements.append({
                "sql": "INSERT INTO model_usage(model,module,operation,company_id,run_id,input_tokens,output_tokens,reasoning_tokens) VALUES (?,?,?,?,?,?,?,?)",
                "params": [
                    event["model"], event["module"], event["operation"],
                    event["company_id"], event["run_id"], event["input_tokens"],
                    event["output_tokens"], event["reasoning_tokens"],
                ],
            })
            if event.get("cost_usd") is not None and event.get("pricing_version"):
                write_statements.append({
                    "sql": "INSERT INTO model_usage_costs(usage_id,cost_usd,pricing_version) VALUES (last_insert_rowid(),?,?)",
                    "params": [event["cost_usd"], event["pricing_version"]],
                })
            if (
                event["module"] == "research"
                and run
                and event.get("run_id") is not None
                and int(event["run_id"]) == int(run["id"])
            ):
                token_counts = system_status.setdefault("tokens", {"in": 0, "out": 0})
                token_counts["in"] = int(token_counts.get("in", 0)) + int(event["input_tokens"])
                token_counts["out"] = int(token_counts.get("out", 0)) + int(event["output_tokens"])
                queue_changed = True

        if queue_changed:
            write_statements.append({
                "sql": "UPDATE module_1_queues SET version=version+1,search_queue=?,enrichment_queue=?,url_check_queue=?,human_review_queue=?,system_status=? WHERE id=1 AND version=?",
                "params": [_json(search_queue), _json(enrichment_queue), _json(url_queue), _json(human_queue), _json(system_status), int(queue_row["version"])],
            })
        write_results = await self.db.batch(write_statements) if write_statements else []
        if usage_batch:
            del self.usage_pending[:len(usage_batch)]
        m1_committed = True
        if queue_changed:
            m1_index = len(write_statements) - 1
            m1_committed = changes(write_results[m1_index]) == 1
        for index, item in m2_claims:
            if changes(write_results[index]) == 1:
                self._dispatch_m2(item, thread_rows)

        if queue_changed and m1_committed:
            for item in claimed_search:
                self._dispatch(self._search_worker(item, run, domains), f"m1-search-{item['job_id']}", {"kind": "search", "queue_id": item["job_id"], "result": {"worker_error": True}})
            company_map = {int(c["id"]): c for c in pending_companies}
            for item in claimed_enrichment:
                company = company_map.get(int(item["company_id"]))
                if company:
                    self._dispatch(self._enrichment_worker(item, company, run), f"m1-enrich-{item['company_id']}", {"kind": "enrichment", "company_id": int(item["company_id"]), "result": {"worker_error": True}})
            for item in claimed_urls:
                company = company_map.get(int(item["company_id"]))
                if company:
                    self._dispatch(self._url_worker(item, company), f"m1-url-{item['company_id']}", {"kind": "url_check", "company_id": int(item["company_id"]), "result": {"worker_error": True}})

        run_snapshot = dict(run) if run else None
        if run_snapshot:
            run_snapshot["created_at"] = _now() if not run_snapshot.get("created_at") else str(run_snapshot["created_at"]).replace(" ", "T") + ("Z" if "+" not in str(run_snapshot["created_at"]) else "")
        self.snapshot = {
            "run": run_snapshot,
            "counts": system_status.get("counts", {}),
            "progress": {"search_jobs": len(search_queue)},
            "tokens": system_status.get("tokens", {"in": 0, "out": 0}),
            "searches": int(system_status.get("searches", 0)),
        }
        await self._resolve_waiters(completion_signals)

