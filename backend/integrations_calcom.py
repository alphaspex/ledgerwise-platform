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
                "timeZone": "UTC",
            },
            headers={"cal-api-version": "2024-09-04"},
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
            headers={"cal-api-version": "2024-08-13"},
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
