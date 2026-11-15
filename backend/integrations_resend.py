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
