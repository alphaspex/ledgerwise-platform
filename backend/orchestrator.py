# Inputs: D1 queue snapshots, claimed company/message rows, completed worker outputs, and configured Meta/provider clients.
# Outputs: committed queue transitions, company research/contact/message outcomes, worker dispatches, and the in-memory research-status snapshot.
# Explanation: Runs the 5-second single-writer orchestrator for Module 1 and Module 2; workers return results to RAM and never access D1.
from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from .config import Settings
from .db import D1Client, changes, rows
from .integrations import (
    ApolloClient,
    CalComClient,
    MuseClient,
    ResendClient,
    check_url,
    is_generic_email,
    normalize_domain,
    registrable_domain,
)
from .models import CompanyStatus


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _load(value: Any, fallback: Any):
    if isinstance(value, (dict, list)):
        return value
    try:
        parsed = json.loads(value or "")
        return parsed
    except (TypeError, json.JSONDecodeError):
        return fallback


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json_object(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    raw = re.sub(r"^\u0060\u0060\u0060(?:json)?\s*|\s*\u0060\u0060\u0060$", "", raw, flags=re.I)
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None


class Orchestrator:
    def __init__(
        self,
        db: D1Client,
        settings: Settings,
        muse: MuseClient,
        resend: ResendClient,
        apollo: ApolloClient,
        calcom: CalComClient,
    ):
        self.db = db
        self.settings = settings
        self.muse = muse
        self.resend = resend
        self.apollo = apollo
        self.calcom = calcom
        self.finished: list[dict[str, Any]] = []
        self.inflight: set[asyncio.Task] = set()
        self.message_waiters: dict[int, asyncio.Future] = {}
        self.tick_count = 0
        self.snapshot: dict[str, Any] = {
            "run": None,
            "counts": {},
            "progress": {"search_jobs": 0},
            "tokens": {"in": 0, "out": 0},
            "searches": 0,
        }
        self._llm_sem = asyncio.Semaphore(settings.llm_concurrency)
        self._http_sem = asyncio.Semaphore(settings.http_concurrency)
        self._draft_sem = asyncio.Semaphore(settings.draft_concurrency)
        self._send_sem = asyncio.Semaphore(settings.send_concurrency)
        self._reply_sem = asyncio.Semaphore(settings.reply_concurrency)

    async def run_forever(self) -> None:
        while True:
            started = time.monotonic()
            try:
                await self.tick()
            except Exception:
                await asyncio.sleep(min(2.0, self.settings.tick_seconds))
            delay = max(0.0, self.settings.tick_seconds - (time.monotonic() - started))
            await asyncio.sleep(delay)

    async def tick(self) -> None:
        self.tick_count += 1
        reconcile = self.tick_count == 1 or self.tick_count % self.settings.reconcile_every_ticks == 0
        read_statements = [
            {"sql": "INSERT OR IGNORE INTO module_1_queues(id) VALUES (1)"},
            {"sql": "SELECT * FROM module_1_queues WHERE id = 1"},
            {"sql": "SELECT * FROM research_runs WHERE status IN ('running','paused') ORDER BY id DESC LIMIT 1"},
            {"sql": "SELECT domain FROM domain_memory ORDER BY created_at DESC LIMIT ?", "params": [self.settings.exclusion_prompt_limit]},
            {"sql": "SELECT * FROM companies WHERE status = 'pending' ORDER BY id LIMIT 100"},
            {"sql": "SELECT q.id AS queue_id,q.type,q.company_id,q.message_id,q.state,q.attempts,q.claimed_at,c.domain,c.status AS company_status,c.contact_email,c.contact_name,c.contact_role,c.contact_source,c.memory,c.research_data,c.email_status,c.thread_state,c.do_not_contact,tm.body AS message_body,tm.sender_type,tm.status AS message_status,tm.subject FROM module_2_queue q JOIN companies c ON c.id=q.company_id LEFT JOIN thread_messages tm ON tm.id=q.message_id WHERE q.state='pending' ORDER BY q.id LIMIT 10"},
            {"sql": "SELECT * FROM (SELECT tm.*, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY id DESC) AS row_num FROM thread_messages tm WHERE company_id IN (SELECT DISTINCT company_id FROM module_2_queue WHERE state='pending' AND type='reply' ORDER BY company_id LIMIT 10)) WHERE row_num <= ? ORDER BY company_id,id", "params": [self.settings.reply_context_window]},
            {"sql": "SELECT c.id,c.domain FROM companies c WHERE c.status='approved' AND c.contact_email IS NULL AND c.do_not_contact=0 AND c.email_status='not_started' AND NOT EXISTS (SELECT 1 FROM module_2_queue q WHERE q.company_id=c.id AND q.type='draft' AND q.message_id IS NULL) ORDER BY c.id LIMIT 10"},
            {"sql": "SELECT c.id,c.domain,c.contact_email FROM companies c WHERE c.status='approved' AND c.contact_email IS NOT NULL AND c.do_not_contact=0 AND c.email_status='not_started' AND NOT EXISTS (SELECT 1 FROM module_2_queue q WHERE q.company_id=c.id AND q.type='draft' AND q.state IN ('pending','processing')) ORDER BY c.id LIMIT 10"},
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
        pending_companies = rows(read_results[4])
        m2_pending = rows(read_results[5])
        thread_rows = rows(read_results[6])
        apollo_candidates = rows(read_results[7])
        draft_candidates = rows(read_results[8])

        if reconcile:
            processing_cutoff = (datetime.now(timezone.utc) - timedelta(seconds=self.settings.lease_seconds)).isoformat()
            expired = [
                item for item in enrichment_queue + url_queue + search_queue
                if item.get("state") == "processing" and str(item.get("claimed_at") or "") < processing_cutoff
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

        queue_changed = False
        for company in pending_companies:
            company_id = int(company["id"])
            has_research = bool(company.get("research_data"))
            target_queue = url_queue if has_research else enrichment_queue
            exists = any(int(item.get("company_id", -1)) == company_id for item in target_queue)
            if not exists:
                target_queue.append({"company_id": company_id, "state": "pending", "attempts": 0, "claimed_at": None})
                queue_changed = True

        if run and run.get("status") == "running":
            counts = system_status.get("counts", {})
            approved = int(counts.get("approved", 0)) + int(counts.get("human_approved", 0))
            pending = int(counts.get("pending", 0))
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

        for candidate in apollo_candidates:
            if self.settings.apollo_enabled:
                exists = any(
                    int(row["company_id"]) == int(candidate["id"]) and row["type"] == "draft" and row["message_id"] is None
                    for row in m2_pending
                )
                if not exists:
                    # The existing draft type is deliberately reused for Apollo contact lookup.
                    pass
        write_statements: list[dict[str, Any]] = []
        completion_signals: list[tuple[int, str]] = []
        finished, self.finished = self.finished, []

        for item in finished:
            kind = item.get("kind")
            result = item.get("result", {})
            queue_id = item.get("queue_id")
            company_id = item.get("company_id")
            if kind == "search":
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
                system_status["tokens"] = system_status.get("tokens", {"in": 0, "out": 0})
                system_status["tokens"]["in"] = int(system_status["tokens"].get("in", 0)) + int(result.get("input_tokens", 0))
                system_status["tokens"]["out"] = int(system_status["tokens"].get("out", 0)) + int(result.get("output_tokens", 0))
            elif kind == "enrichment":
                entry = next((q for q in enrichment_queue if int(q.get("company_id", -1)) == int(company_id)), None)
                if entry:
                    enrichment_queue.remove(entry)
                queue_changed = True
                if result.get("valid"):
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
            elif kind == "url_check":
                url_queue = [q for q in url_queue if int(q.get("company_id", -1)) != int(company_id)]
                queue_changed = True
                bucket = int(result.get("bucket", 2))
                research = result.get("research_data", {})
                if bucket == 1:
                    write_statements.extend([
                        {"sql": "UPDATE companies SET status='failed_404',research_data=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [_json(research), int(company_id)]},
                        {"sql": "UPDATE domain_memory SET status='failed_404' WHERE domain=(SELECT domain FROM companies WHERE id=?)", "params": [int(company_id)]},
                    ])
                elif bucket == 2:
                    write_statements.extend([
                        {"sql": "UPDATE companies SET status='needs_human_review',research_data=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [_json(research), int(company_id)]},
                        {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'contact_missing',?)", "params": [int(company_id), "Company domain could not be verified automatically; human review is required."]},
                    ])
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
            elif kind == "apollo":
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
            elif kind == "draft":
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
            elif kind == "send":
                status = result.get("status", "failed")
                if status == "retry":
                    write_statements.append({
                        "sql": "UPDATE module_2_queue SET state='pending',attempts=attempts+1,claimed_at=NULL WHERE id=?",
                        "params": [int(queue_id)],
                    })
                else:
                    write_statements.extend([
                        {"sql": "UPDATE thread_messages SET status=?,provider_message_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [status, result.get("provider_message_id"), int(result.get("message_id") or 0)]},
                        {"sql": "UPDATE companies SET email_status=CASE WHEN email_status IN ('approved','drafting','pending_review') THEN 'sent' ELSE email_status END,thread_state=CASE WHEN thread_state='inactive' THEN 'auto' ELSE thread_state END,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                        {"sql": "UPDATE module_2_queue SET state=?,claimed_at=NULL WHERE id=?", "params": ["done" if status == "sent" else "failed", int(queue_id)]},
                    ])
                    if result.get("message_id"):
                        completion_signals.append((int(result["message_id"]), status))
            elif kind == "reply":
                write_statements.append({"sql": "UPDATE module_2_queue SET state='done',claimed_at=NULL WHERE id=?", "params": [int(queue_id)]})
                if result.get("stop"):
                    write_statements.extend([
                        {"sql": "UPDATE companies SET do_not_contact=1,thread_state='needs_human',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                        {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'do_not_contact',?)", "params": [int(company_id), "Prospect requested no further contact."]},
                    ])
                elif result.get("body"):
                    write_statements.extend([
                        {"sql": "INSERT INTO thread_messages(company_id,sender_type,body,status,tool_calls) VALUES (?,'agent',?,'approved',?)", "params": [int(company_id), result["body"], _json(result.get("tool_calls", []))]},
                    ])
                    write_statements.append({
                        "sql": "INSERT INTO module_2_queue(type,company_id,message_id,state) VALUES ('send',?,last_insert_rowid(),'pending')",
                        "params": [int(company_id)],
                    })
                    if result.get("needs_human"):
                        write_statements.extend([
                            {"sql": "UPDATE companies SET thread_state='needs_human',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [int(company_id)]},
                            {"sql": "INSERT INTO notifications(company_id,reason,body) VALUES (?,'unsure_answer',?)", "params": [int(company_id), "The agent escalated this conversation for human review."]},
                        ])

        for candidate in apollo_candidates:
            if self.settings.apollo_enabled:
                write_statements.append({
                    "sql": "INSERT INTO module_2_queue(type,company_id,message_id,state) SELECT 'draft',?,NULL,'pending' WHERE NOT EXISTS (SELECT 1 FROM module_2_queue WHERE company_id=? AND type='draft' AND message_id IS NULL)",
                    "params": [int(candidate["id"]), int(candidate["id"])],
                })
        for candidate in draft_candidates:
            write_statements.append({
                "sql": "INSERT INTO module_2_queue(type,company_id,message_id,state) SELECT 'draft',?,NULL,'pending' WHERE NOT EXISTS (SELECT 1 FROM module_2_queue WHERE company_id=? AND type='draft' AND state IN ('pending','processing') AND message_id IS NOT NULL)",
                "params": [int(candidate["id"]), int(candidate["id"])],
            })

        m2_claims = []
        for item in m2_pending:
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
            write_statements.append({"sql": "DELETE FROM auth_events WHERE created_at < datetime('now', ?)", "params": [f"-{self.settings.auth_events_retention_days} days"]})

        for item in search_queue:
            if item.get("state") == "pending":
                item["state"] = "processing"
                item["claimed_at"] = _now()
                queue_changed = True
                break
        claimed_search = [item for item in search_queue if item.get("state") == "processing" and item.get("claimed_at") and item.get("claimed_at") == search_queue[-1].get("claimed_at")][-1:] if search_queue else []

        claimed_enrichment = []
        for item in enrichment_queue:
            if item.get("state") == "pending" and len(claimed_enrichment) < self.settings.llm_concurrency:
                item["state"] = "processing"
                item["claimed_at"] = _now()
                claimed_enrichment.append(item)
                queue_changed = True

        claimed_urls = []
        for item in url_queue:
            if item.get("state") == "pending" and len(claimed_urls) < self.settings.http_concurrency:
                item["state"] = "processing"
                item["claimed_at"] = _now()
                claimed_urls.append(item)
                queue_changed = True

        for item in search_queue:
            if item.get("state") == "processing" and item.get("job_id") and item not in claimed_search and not any(t.get_name() == f"m1-search-{item['job_id']}" for t in self.inflight):
                claimed_search = [item]
                break

        if queue_changed:
            write_statements.append({
                "sql": "UPDATE module_1_queues SET version=version+1,search_queue=?,enrichment_queue=?,url_check_queue=?,human_review_queue=?,system_status=? WHERE id=1 AND version=?",
                "params": [_json(search_queue), _json(enrichment_queue), _json(url_queue), _json(human_queue), _json(system_status), int(queue_row["version"])],
            })
        write_results = await self.db.batch(write_statements) if write_statements else []
        m1_committed = True
        if queue_changed:
            m1_index = len(write_statements) - 1
            m1_committed = changes(write_results[m1_index]) == 1
        for index, item in m2_claims:
            if changes(write_results[index]) == 1:
                self._dispatch_m2(item, thread_rows)

        if queue_changed and m1_committed:
            for item in claimed_search:
                self._dispatch(self._search_worker(item), f"m1-search-{item['job_id']}")
            company_map = {int(c["id"]): c for c in pending_companies}
            for item in claimed_enrichment:
                company = company_map.get(int(item["company_id"]))
                if company:
                    self._dispatch(self._enrichment_worker(item, company), f"m1-enrich-{item['company_id']}")
            for item in claimed_urls:
                company = company_map.get(int(item["company_id"]))
                if company:
                    self._dispatch(self._url_worker(item, company), f"m1-url-{item['company_id']}")

        if reconcile and len(read_results) > 9:
            count_map = {str(row["status"]): int(row["total"]) for row in rows(read_results[9])}
            system_status["counts"] = count_map
        self.snapshot = {
            "run": run,
            "counts": system_status.get("counts", {}),
            "progress": {"search_jobs": len(search_queue)},
            "tokens": system_status.get("tokens", {"in": 0, "out": 0}),
            "searches": int(system_status.get("searches", 0)),
        }
        await self._resolve_waiters(completion_signals)

    def _dispatch(self, coroutine, name: str) -> None:
        task = asyncio.create_task(coroutine, name=name)
        self.inflight.add(task)

        def completed(done: asyncio.Task) -> None:
            self.inflight.discard(done)
            try:
                self.finished.append(done.result())
            except Exception as exc:
                self.finished.append({"kind": "worker_error", "error": str(exc)})

        task.add_done_callback(completed)

    async def _search_worker(self, job: dict[str, Any]) -> dict[str, Any]:
        async with self._llm_sem:
            prompt = (
                "Search the live web for organizations matching this ideal-customer selection. "
                f"Return JSON only: {{\"domains\":[\"example.com\"]}}. Find up to {int(job['n'])} "
                "unique company domains. Exclude these already used domains: "
                + _json([]) + ". Selection: " + str(job.get("selection", ""))
            )
            response = await self.muse.generate(prompt, use_search=True)
        data = _parse_json_object(response["text"]) or {}
        domains = []
        for value in data.get("domains", []):
            try:
                domains.append(normalize_domain(str(value)))
            except ValueError:
                continue
        return {
            "kind": "search",
            "queue_id": job["job_id"],
            "result": {
                "run_id": job["run_id"], "domains": list(dict.fromkeys(domains)),
                "input_tokens": response["input_tokens"], "output_tokens": response["output_tokens"],
            },
        }

    async def _enrichment_worker(self, job: dict[str, Any], company: dict[str, Any]) -> dict[str, Any]:
        async with self._llm_sem:
            prompt = (
                "Research this company using live web search. Return JSON only with company_id, domain, "
                "integer score 0..10, reasons (1-5 items each text/source_url/quote), and source_urls (max 5). "
                "Quotes must be verbatim evidence. Never invent facts. "
                f"company_id={company['id']} domain={company['domain']}. Selection={company.get('selection','')}"
            )
            response = await self.muse.generate(prompt, use_search=True)
        data = _parse_json_object(response["text"]) or {}
        try:
            domain = normalize_domain(str(data.get("domain", "")))
            reasons = data.get("reasons")
            urls = data.get("source_urls")
            valid = (
                int(data.get("company_id")) == int(company["id"])
                and domain == normalize_domain(str(company["domain"]))
                and isinstance(data.get("score"), int) and 0 <= data["score"] <= 10
                and isinstance(reasons, list) and 1 <= len(reasons) <= 5
                and all(isinstance(r, dict) and all(str(r.get(k, "")).strip() for k in ("text", "source_url", "quote")) for r in reasons)
                and isinstance(urls, list)
            )
        except (TypeError, ValueError):
            valid = False
            reasons, urls = [], []
        valid_urls = []
        if valid:
            for url in urls[: self.settings.max_source_urls]:
                if isinstance(url, str) and url.startswith(("https://", "http://")):
                    valid_urls.append(url)
        valid = valid and bool(valid_urls)
        return {
            "kind": "enrichment", "company_id": int(company["id"]),
            "result": {
                "valid": valid, "score": data.get("score"), "reasons": reasons or [],
                "source_urls": valid_urls, "input_tokens": response["input_tokens"],
                "output_tokens": response["output_tokens"],
            },
        }

    async def _url_worker(self, job: dict[str, Any], company: dict[str, Any]) -> dict[str, Any]:
        domain_result = await asyncio.to_thread(check_url, f"https://{company['domain']}/", self.settings.url_timeout_seconds, self.settings.max_redirects)
        status = domain_result.get("status")
        error = domain_result.get("error")
        if status in {400, 404, 410} or error == "nxdomain":
            bucket = 1
        elif status == 200:
            bucket = 3
        else:
            bucket = 2
        existing = _load(company.get("research_data"), {})
        domain_check = {
            "bucket": bucket,
            "status": status,
            "redirected_to": None,
        }
        final_url = domain_result.get("final_url")
        if final_url:
            try:
                if registrable_domain(final_url) != registrable_domain(company["domain"]):
                    domain_check["redirected_to"] = normalize_domain(final_url)
            except ValueError:
                pass
        if bucket == 3:
            sem = self._http_sem
            urls = list(dict.fromkeys(
                str(item.get("source_url")) for item in existing.get("reasons", []) if item.get("source_url")
            ))
            urls.extend(str(url) for url in existing.get("sources", []) if isinstance(url, str))
            source_rows = []
            for url in list(dict.fromkeys(urls))[: self.settings.max_source_urls]:
                async with sem:
                    checked = await asyncio.to_thread(check_url, url, self.settings.url_timeout_seconds, self.settings.max_redirects)
                result = checked.get("result", "unverified")
                if checked.get("error") == "nxdomain":
                    result = "dead"
                source_rows.append({"url": url, "result": result, "status": checked.get("status")})
            existing["sources"] = source_rows
        existing["domain_check"] = domain_check
        return {"kind": "url_check", "company_id": int(company["id"]), "result": {"bucket": bucket, "research_data": existing}}

    def _dispatch_m2(self, job: dict[str, Any], thread_rows: list[dict[str, Any]]) -> None:
        if job["type"] == "draft" and not job.get("contact_email"):
            self._dispatch(self._apollo_worker(job), f"m2-apollo-{job['queue_id']}")
        elif job["type"] == "draft":
            self._dispatch(self._draft_worker(job), f"m2-draft-{job['queue_id']}")
        elif job["type"] == "send":
            self._dispatch(self._send_worker(job), f"m2-send-{job['queue_id']}")
        elif job["type"] == "reply":
            history = [row for row in thread_rows if int(row["company_id"]) == int(job["company_id"])]
            self._dispatch(self._reply_worker(job, history), f"m2-reply-{job['queue_id']}")

    async def _apollo_worker(self, job: dict[str, Any]) -> dict[str, Any]:
        result = await self.apollo.lookup(str(job["domain"]))
        return {"kind": "apollo", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": result}

    async def _draft_worker(self, job: dict[str, Any]) -> dict[str, Any]:
        async with self._draft_sem:
            memory = _load(job.get("memory"), None)
            if not isinstance(memory, dict) or len(memory.get("facts", [])) == 0:
                audit: dict[str, Any] = {}
                extract = await self.muse.generate(
                    "Extract up to 20 factual company facts from the domain and research data. "
                    "Return JSON only: {\"facts\":[{\"field\":\"\",\"value\":\"\",\"source_url\":\"https://...\",\"quote\":\"\"}]}. "
                    f"Domain: {job['domain']} Research: {_json(_load(job.get('research_data'), {}))}",
                    use_search=True,
                )
                extracted = _parse_json_object(extract["text"]) or {}
                facts = [
                    f for f in extracted.get("facts", [])
                    if isinstance(f, dict) and all(str(f.get(k, "")).strip() for k in ("field", "value", "source_url", "quote"))
                ][: self.settings.memory_max_facts]
                audit["extract"] = {"raw": extract["text"], "model": self.settings.muse_model}
                verify = await self.muse.generate(
                    "Verify every fact. Return JSON only: {\"checks\":[{\"field\":\"\",\"verified\":true,\"reason\":null}]}. "
                    f"Facts: {_json(facts)}",
                    use_search=True,
                )
                checks_data = _parse_json_object(verify["text"]) or {}
                checks = {str(c.get("field")): bool(c.get("verified")) for c in checks_data.get("checks", []) if isinstance(c, dict)}
                audit["verify"] = {"raw": verify["text"], "checks": checks_data.get("checks", [])}
                verified = [f for f in facts if checks.get(str(f["field"])) is True]
                failed = [f for f in facts if checks.get(str(f["field"])) is not True]
                if failed:
                    repair = await self.muse.generate(
                        "Repair only the failed fields below. Return JSON only with a facts array; each item must contain field,value,source_url,quote. "
                        f"Failed fields: {_json(failed)}",
                        use_search=True,
                    )
                    repaired_data = _parse_json_object(repair["text"]) or {}
                    audit["repair"] = [{"attempt": 1, "raw": repair["text"]}]
                    repaired = [
                        f for f in repaired_data.get("facts", [])
                        if isinstance(f, dict) and all(str(f.get(k, "")).strip() for k in ("field", "value", "source_url", "quote"))
                    ]
                    verified.extend(repaired)
                memory = {"facts": verified[: self.settings.memory_max_facts], "audit": audit}
            if len(memory.get("facts", [])) < 3:
                return {"kind": "draft", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"memory_missing": True, "memory": memory}}
            prompt = (
                f"Write a first outreach email to {job['domain']} in a personal founder-to-founder tone. "
                f"Maximum {self.settings.email_max_words} words. No price, cost, or fee language. "
                "Open with one specific verified fact, use only these verified facts, and end with a soft ask. "
                f"Contact role: {job.get('contact_role')}. Facts: {_json(memory['facts'])}."
            )
            response = await self.muse.generate(prompt, use_search=False)
            body = response["text"].strip()
            if len(body.split()) > self.settings.email_max_words or re.search(r"\$|\b(price|cost|per month)\b", body, re.I):
                retry = await self.muse.generate(prompt + " Strictly obey all constraints; output email body only.", use_search=False)
                body = retry["text"].strip()
            if len(body.split()) > self.settings.email_max_words or re.search(r"\$|\b(price|cost|per month)\b", body, re.I):
                body = ""
            return {"kind": "draft", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"memory": memory, "body": body, "domain": job["domain"]}}

    async def _send_worker(self, job: dict[str, Any]) -> dict[str, Any]:
        async with self._send_sem:
            message_id = int(job.get("message_id") or 0)
            if job.get("do_not_contact") or not job.get("contact_email") or not job.get("message_body"):
                return {"kind": "send", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"status": "blocked_by_do_not_contact" if job.get("do_not_contact") else "failed", "message_id": message_id}}
            try:
                provider_id = await self.resend.send(
                    to=str(job["contact_email"]),
                    subject=str(job.get("subject") or ("Re: " + str(job["domain"]))),
                    text=str(job["message_body"]),
                    idempotency_key=f"ledgerwise-message-{message_id}",
                )
                status = "sent"
            except Exception:
                provider_id = None
                status = "retry" if int(job.get("attempts", 0)) + 1 < self.settings.max_attempts else "failed"
            return {"kind": "send", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"status": status, "message_id": message_id, "provider_message_id": provider_id}}

    async def _reply_worker(self, job: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
        async with self._reply_sem:
            inbound = str(job.get("message_body") or "")
            stop = bool(re.search(r"\b(stop|unsubscribe|not interested|remove me|don't contact|do not contact)\b", inbound, re.I))
            if stop or job.get("do_not_contact"):
                return {"kind": "reply", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"stop": True}}
            safe_history = [
                {"sender": row.get("sender_type"), "body": row.get("body")}
                for row in history[-self.settings.reply_context_window:]
            ]
            response = await self.muse.generate(
                "Reply to the prospect as Ledgerwise's AI assistant. Be honest that you are an AI if asked. "
                "Never quote prices. Every factual claim must be supported by verified company memory or research. "
                "Do not invent details. If unsure, write one brief handoff sentence and mark needs_human=true. "
                f"Maximum {self.settings.reply_max_words} words. Contact role: {job.get('contact_role')}. "
                f"Verified memory: {_json(_load(job.get('memory'), {'facts': []}))}. "
                f"Conversation: {_json(safe_history)}. Latest prospect message: {inbound}",
                use_search=False,
            )
            body = response["text"].strip()
            needs_human = "let me bring in a colleague" in body.lower()
            if len(body.split()) > self.settings.reply_max_words:
                body = "Thanks for your message. Let me bring in a colleague to help with this."
                needs_human = True
            return {"kind": "reply", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"body": body, "needs_human": needs_human, "tool_calls": []}}

    async def _resolve_waiters(self, completions: list[tuple[int, str]]) -> None:
        for message_id, status in completions:
            future = self.message_waiters.pop(message_id, None)
            if future and not future.done():
                future.set_result(status)

    def register_message_waiter(self, message_id: int) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.message_waiters[message_id] = future
        return future

    def release_message_waiter(self, message_id: int, future: asyncio.Future) -> None:
        if self.message_waiters.get(message_id) is future:
            self.message_waiters.pop(message_id, None)
