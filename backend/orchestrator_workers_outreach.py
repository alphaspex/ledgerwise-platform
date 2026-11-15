# Inputs: orchestrator dependencies, queue jobs, and completed worker results for the Ledgerwise backend.
# Outputs: bounded worker and orchestration methods that return data or append state for the single writer.
# Explanation: Implements one focused orchestrator responsibility; D1 queue writes remain in tick commit stages.
from __future__ import annotations
from __future__ import annotations

import asyncio
from contextvars import ContextVar
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
from .orchestrator_helpers import _json, _load

class OutreachWorkersMixin:
    def _dispatch_m2(self, job: dict[str, Any], thread_rows: list[dict[str, Any]]) -> None:
        if job["type"] == "draft" and not job.get("contact_email"):
            self._dispatch(self._apollo_worker(job), f"m2-apollo-{job['queue_id']}", {"kind": "apollo", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"worker_error": True}})
        elif job["type"] == "draft":
            self._dispatch(self._draft_worker(job), f"m2-draft-{job['queue_id']}", {"kind": "draft", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"worker_error": True}})
        elif job["type"] == "send":
            self._dispatch(self._send_worker(job), f"m2-send-{job['queue_id']}", {"kind": "send", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"status": "retry", "message_id": int(job.get("message_id") or 0), "worker_error": True}})
        elif job["type"] == "reply":
            history = [row for row in thread_rows if int(row["company_id"]) == int(job["company_id"])]
            self._dispatch(self._reply_worker(job, history), f"m2-reply-{job['queue_id']}", {"kind": "reply", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"worker_error": True}})

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
            if job.get("do_not_contact"):
                status = "blocked_by_do_not_contact"
            elif job.get("message_status") != "approved":
                status = "failed"
            elif not job.get("contact_email") or not job.get("message_body"):
                status = "failed"
            elif job.get("sender_type") == "agent" and job.get("thread_state") in {"human_taken_over", "closed"}:
                status = "failed"
            elif (
                job.get("sender_type") == "agent"
                and job.get("in_reply_to_message_id") is not None
                and int(job.get("latest_prospect_message_id") or 0) != int(job["in_reply_to_message_id"])
            ):
                status = "failed"
            else:
                status = ""
            if status:
                return {"kind": "send", "queue_id": int(job["queue_id"]), "company_id": int(job["company_id"]), "result": {"status": status, "message_id": message_id}}
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
