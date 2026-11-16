# Inputs: Meta Muse settings, prompts, tool options, and Responses API payloads containing model usage and web-search call results.
# Outputs: generated text, function calls, response identifiers, token counts, and exact completed web-search call counts.
# Explanation: Sends Muse Responses API requests and reports per-call token and web-search usage to the orchestrator callback.
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
from typing import Any, Callable
from urllib.parse import urlparse

import httpx
import requests
import tldextract


class MuseClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.usage_callback: Callable[[dict[str, Any]], None] | None = None
        self.client = httpx.AsyncClient(
            base_url=settings.muse_api_base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {settings.api_token}", "Content-Type": "application/json"},
            timeout=httpx.Timeout(60.0, connect=10.0),
        )

    def set_usage_callback(self, callback: Callable[[dict[str, Any]], None] | None) -> None:
        self.usage_callback = callback

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
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        output_details = usage.get("output_tokens_details", {}) or {}
        reasoning_tokens = int(output_details.get("reasoning_tokens", 0) or 0)
        searches = sum(1 for item in data.get("output", []) if isinstance(item, dict) and item.get("type") == "web_search_call")
        usage_record = {
            "model": self.settings.muse_model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "searches": searches,
        }
        if self.usage_callback is not None:
            self.usage_callback(usage_record)
        return {
            "text": "\n".join(text_parts).strip(),
            "function_calls": function_calls,
            "response_id": data.get("id"),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "searches": searches,
            "raw": data,
        }
