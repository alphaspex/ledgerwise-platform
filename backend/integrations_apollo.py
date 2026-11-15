# Inputs: provider configuration and operation payloads for Meta Muse, Resend, Apollo, Cal.com, and URL checks.
# Outputs: normalized provider responses, model usage, delivery identifiers, contact matches, bookings, and URL results.
# Explanation: Exposes provider integrations through focused I/O-bound modules.
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import re
import socket
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
from typing import Any
from urllib.parse import urlparse

import httpx
import requests
import tldextract

from .integrations_common import ROLE_TITLES, normalize_domain


class ApolloRateGate:
    def __init__(self, requests_per_minute: int):
        self.limit = max(1, requests_per_minute)
        self.calls: deque[float] = deque()
        self.lock = asyncio.Lock()

    async def wait(self) -> None:
        while True:
            async with self.lock:
                now = time.monotonic()
                while self.calls and self.calls[0] <= now - 60:
                    self.calls.popleft()
                if len(self.calls) < self.limit:
                    self.calls.append(now)
                    return
                delay = max(0.05, 60 - (now - self.calls[0]))
            await asyncio.sleep(delay)


class ApolloClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.gate = ApolloRateGate(settings.apollo_rate_limit_rpm)
        self.client = httpx.AsyncClient(
            base_url=settings.apollo_api_base_url.rstrip("/"),
            headers={
                "x-api-key": settings.apollo_api_key,
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
            },
            timeout=httpx.Timeout(12.0, connect=5.0),
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def lookup(self, domain: str) -> dict[str, Any]:
        if not self.settings.apollo_enabled or not self.settings.apollo_api_key:
            return {"outcome": "disabled", "candidates": []}
        await self.gate.wait()
        search = await self.client.post(
            "mixed_people/api_search",
            json={
                "q_organization_domains_list": [normalize_domain(domain)],
                "person_titles": ROLE_TITLES["founder"] + ROLE_TITLES["coo"] + ROLE_TITLES["finance"],
                "include_similar_titles": False,
                "per_page": 10,
                "page": 1,
            },
        )
        search.raise_for_status()
        search_data = search.json()
        people = search_data.get("people", []) or []
        candidates = []
        for person in people:
            organization = person.get("organization") or {}
            raw_org_domain = organization.get("primary_domain") or organization.get("website_url")
            organization_domain = ""
            if raw_org_domain:
                try:
                    organization_domain = normalize_domain(str(raw_org_domain))
                except ValueError:
                    organization_domain = ""
            candidates.append({
                "id": str(person.get("id", "")),
                "name": " ".join(part for part in [person.get("first_name"), person.get("last_name")] if part),
                "title": str(person.get("title") or ""),
                "role": infer_contact_role(str(person.get("title") or "")),
                "organization_domain": organization_domain,
            })
        if not candidates:
            return {"outcome": "not_found", "candidates": []}
        if len(candidates) > 1:
            return {"outcome": "multiple", "candidates": candidates}
        candidate = candidates[0]
        if (
            not candidate["id"]
            or candidate["organization_domain"] != normalize_domain(domain)
            or candidate["role"] == "unknown"
        ):
            return {"outcome": "not_found", "candidates": candidates}
        await self.gate.wait()
        match = await self.client.post(
            "people/match",
            json={"id": candidate["id"], "reveal_personal_emails": False},
        )
        match.raise_for_status()
        person = (match.json() or {}).get("person") or {}
        organization = person.get("organization") or {}
        matched_domain = normalize_domain(
            organization.get("primary_domain") or organization.get("website_url") or ""
        ) if (organization.get("primary_domain") or organization.get("website_url")) else ""
        email = str(person.get("email") or "").strip().lower()
        email_status = str(person.get("email_status") or "").lower()
        title = str(person.get("title") or candidate["title"])
        role = infer_contact_role(title)
        if matched_domain != normalize_domain(domain) or not email or email_status != "verified" or is_generic_email(email):
            return {"outcome": "not_found", "candidates": [candidate]}
        return {
            "outcome": "found",
            "email": email,
            "name": " ".join(part for part in [person.get("first_name"), person.get("last_name")] if part),
            "title": title,
            "role": role,
            "candidates": [candidate],
        }


def infer_contact_role(title: str) -> str:
    text = title.lower()
    if any(word in text for word in ("founder", "chief executive", "ceo")):
        return "founder"
    if "chief operating" in text or re.search(r"\bcoo\b", text):
        return "coo"
    if any(word in text for word in ("chief financial", "finance director", "controller")) or re.search(r"\bcfo\b", text):
        return "finance"
    return "unknown"
