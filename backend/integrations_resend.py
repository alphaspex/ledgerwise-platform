# Inputs: Resend API key, configured sender and receiving domain, outbound message fields, and received email IDs.
# Outputs: Resend delivery IDs, provider reply addresses, and full received-email payloads.
# Explanation: Owns outbound delivery and inbound-message retrieval through the Resend API.
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
from urllib.parse import quote, urlparse

import httpx
import requests
import tldextract


class ResendClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient(
            base_url="https://api.resend.com",
            headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

    def reply_to_for_company(self, company_id: int) -> str | None:
        domain = str(self.settings.resend_inbound_domain or "").strip().lower().strip(".")
        if not domain or "@" in domain or "/" in domain or " " in domain:
            return None
        return f"reply+{int(company_id)}@{domain}"

    async def get_received_email(self, email_id: str) -> dict[str, Any]:
        if not email_id or "/" in email_id or "\\" in email_id:
            raise ValueError("Invalid Resend received email ID")
        response = await self.client.get(f"emails/receiving/{quote(email_id, safe='')}")
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError("Resend returned an invalid received email payload")
        return body

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
