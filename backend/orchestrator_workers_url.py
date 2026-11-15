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
from .orchestrator_helpers import _load
from .integrations import check_url, normalize_domain, registrable_domain

class URLWorkersMixin:
    async def _throttled_url_check(self, url: str) -> dict[str, Any]:
        host = normalize_domain(url)
        lock = self._host_locks.setdefault(host, asyncio.Lock())
        async with lock:
            previous = self._host_last_request.get(host)
            if previous is not None:
                delay = max(0.0, 1.0 - (time.monotonic() - previous))
                if delay:
                    await asyncio.sleep(delay)
            self._host_last_request[host] = time.monotonic()
            return await asyncio.to_thread(
                check_url,
                url,
                self.settings.url_timeout_seconds,
                self.settings.max_redirects,
            )

    async def _url_worker(self, job: dict[str, Any], company: dict[str, Any]) -> dict[str, Any]:
        async with self._http_sem:
            domain_result = await self._throttled_url_check(f"https://{company['domain']}/")
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
            urls = list(dict.fromkeys(
                str(item.get("source_url")) for item in existing.get("reasons", []) if item.get("source_url")
            ))
            urls.extend(
                str(item.get("url")) if isinstance(item, dict) else str(item)
                for item in existing.get("sources", [])
                if (isinstance(item, dict) and item.get("url")) or isinstance(item, str)
            )
            source_rows = []
            for url in list(dict.fromkeys(urls))[: self.settings.max_source_urls]:
                async with self._http_sem:
                    checked = await self._throttled_url_check(url)
                result = checked.get("result", "unverified")
                if checked.get("error") == "nxdomain":
                    result = "dead"
                source_rows.append({"url": url, "result": result, "status": checked.get("status")})
            existing["sources"] = source_rows
        existing["domain_check"] = domain_check
        return {"kind": "url_check", "company_id": int(company["id"]), "result": {"bucket": bucket, "research_data": existing}}
