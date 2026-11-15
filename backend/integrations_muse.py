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
