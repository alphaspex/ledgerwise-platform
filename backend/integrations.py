# Inputs: typed integration settings and task payloads for Meta Muse, Resend, Apollo, Cal.com, and URL validation.
# Outputs: model text/tool calls, delivery/provider IDs, Apollo candidate outcomes, booking data, webhook validity, and URL check results.
# Explanation: Owns outbound HTTP integrations and normalizes provider-specific responses into backend-level inputs and outputs.
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

from .config import Settings


GENERIC_INBOX_PREFIXES = {
    "info", "hello", "support", "orders", "service", "customercare", "team", "contact"
}

ROLE_TITLES = {
    "founder": ["Founder", "Co-Founder", "CEO", "Chief Executive Officer"],
    "coo": ["COO", "Chief Operating Officer"],
    "finance": ["CFO", "Chief Financial Officer", "Finance Director", "Controller"],
}


def normalize_domain(value: str) -> str:
    raw = value.strip().lower()
    if not raw:
        raise ValueError("domain is required")
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = (parsed.hostname or "").strip(".").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host or any(ch.isspace() for ch in host):
        raise ValueError("invalid domain")
    return host


def registrable_domain(value: str) -> str:
    extracted = tldextract.TLDExtract(suffix_list_urls=())(normalize_domain(value))
    return extracted.top_domain_under_public_suffix or normalize_domain(value)


def is_generic_email(email: str) -> bool:
    normalized = parseaddr(email)[1].strip().lower()
    if "@" not in normalized:
        return True
    return normalized.split("@", 1)[0].split("+", 1)[0] in GENERIC_INBOX_PREFIXES


def verify_hmac_signature(raw_body: bytes, signature: str, secret: str, prefix: str = "") -> bool:
    if not signature or not secret:
        return False
    supplied = signature.removeprefix(prefix).strip()
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(supplied, expected)


class MuseClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url=settings.muse_api_base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {settings.api_token}", "Content-Type": "application/json"},
            timeout=httpx.Timeout(60.0, connect=10.0),
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def generate(
        self,
        prompt: str | None = None,
        use_search: bool = True,
        max_output_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        previous_response_id: str | None = None,
        input_override: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.settings.muse_model,
            "input": input_override if input_override is not None else (prompt or ""),
            "reasoning": {"effort": self.settings.muse_reasoning_effort},
            "max_output_tokens": max_output_tokens or self.settings.muse_max_output_tokens,
        }
        supplied_tools = list(tools or [])
        if use_search:
            supplied_tools.insert(0, {"type": "web_search"})
        if supplied_tools:
            payload["tools"] = supplied_tools
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        response = await self.client.post("responses", json=payload)
        response.raise_for_status()
        data = response.json()
        text_parts: list[str] = []
        function_calls: list[dict[str, Any]] = []
        for item in data.get("output", []):
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        text_parts.append(str(part.get("text", "")))
            elif item.get("type") == "function_call" and item.get("status", "completed") == "completed":
                function_calls.append(item)
        usage = data.get("usage", {}) or {}
        return {
            "text": "\n".join(text_parts).strip(),
            "function_calls": function_calls,
            "response_id": data.get("id"),
            "input_tokens": int(usage.get("input_tokens", 0) or 0),
            "output_tokens": int(usage.get("output_tokens", 0) or 0),
            "raw": data,
        }


class ResendClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url="https://api.resend.com",
            headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def send(
        self,
        to: str,
        subject: str,
        text: str,
        idempotency_key: str,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "from": self.settings.resend_from_email,
            "to": [to],
            "subject": subject,
            "text": text,
        }
        if reply_to:
            payload["reply_to"] = reply_to
        if headers:
            payload["headers"] = headers
        response = await self.client.post(
            "emails", json=payload, headers={"Idempotency-Key": idempotency_key}
        )
        response.raise_for_status()
        body = response.json()
        if not body.get("id"):
            raise RuntimeError("Resend did not return an email id")
        return str(body["id"])


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


class CalComClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url=settings.calcom_api_base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {settings.calcom_api_key}", "Content-Type": "application/json"},
            timeout=httpx.Timeout(5.0, connect=3.0),
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def check_availability(self) -> list[dict[str, Any]]:
        start = datetime.now(timezone.utc)
        end = start + timedelta(days=self.settings.calcom_avail_days_ahead)
        response = await self.client.get(
            "slots",
            params={
                "eventTypeId": self.settings.calcom_event_type_id,
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
        )
        response.raise_for_status()
        data = response.json()
        slots = data.get("data", data).get("slots", []) if isinstance(data.get("data", data), dict) else []
        flattened = []
        for group in slots if isinstance(slots, list) else []:
            if isinstance(group, dict):
                flattened.append(group)
            elif isinstance(group, list):
                flattened.extend(item for item in group if isinstance(item, dict))
        return flattened[: self.settings.calcom_avail_max_slots]

    async def book_slot(self, start_time: str, email: str, name: str) -> dict[str, Any]:
        response = await self.client.post(
            "bookings",
            json={
                "eventTypeId": int(self.settings.calcom_event_type_id),
                "start": start_time,
                "attendee": {
                    "name": name,
                    "email": email,
                    "timeZone": "UTC",
                    "language": "en",
                },
            },
        )
        if response.status_code == 409:
            return {"success": False, "error": "slot_taken"}
        if response.status_code == 400:
            return {"success": False, "error": "invalid_slot"}
        if response.status_code == 429:
            return {"success": False, "error": "rate_limited"}
        response.raise_for_status()
        data = response.json()
        booking = data.get("data", data)
        uid = booking.get("uid") or booking.get("id")
        return {"success": bool(uid), "uid": str(uid) if uid else None, "data": booking}


def check_url(url: str, timeout: int = 5, max_redirects: int = 5) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return {"result": "unverified", "status": None, "error": "invalid_url"}
    try:
        socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        session = requests.Session()
        session.max_redirects = max_redirects
        response = session.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; LedgerwiseBot/1.0)"},
            timeout=timeout,
            stream=True,
            allow_redirects=True,
        )
        status = int(response.status_code)
        response_url = response.url
        response.close()
        session.close()
        if status == 200:
            return {"result": "live", "status": status, "final_url": response_url}
        if status in {404, 410}:
            return {"result": "dead", "status": status, "final_url": response_url}
        return {"result": "unverified", "status": status, "final_url": response_url}
    except requests.exceptions.HTTPError as exc:
        return {"result": "unverified", "status": getattr(exc.response, "status_code", None), "error": "http_error"}
    except requests.exceptions.TooManyRedirects:
        return {"result": "unverified", "status": None, "error": "too_many_redirects"}
    except requests.exceptions.RequestException as exc:
        return {"result": "unverified", "status": None, "error": type(exc).__name__}
    except socket.gaierror as exc:
        if getattr(exc, "errno", None) == socket.EAI_NONAME:
            return {"result": "dead", "status": None, "error": "nxdomain"}
        return {"result": "unverified", "status": None, "error": "dns_error"}
