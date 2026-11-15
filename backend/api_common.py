# Inputs: FastAPI request context, D1 rows, and the frontend API request/response contract.
# Outputs: shared request helpers, serializers, authentication helpers, and route routers.
# Explanation: Keeps backend.api.router stable while route handlers live in focused modules.
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from fastapi import Request
from .config import Settings
from .db import D1Client

def _db(request: Request) -> D1Client:
    return request.app.state.db

def _settings(request: Request) -> Settings:
    return request.app.state.settings

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _iso(value: Any) -> str:
    if value is None:
        return _now()
    raw = str(value)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return raw

def _json_load(value: Any, fallback: Any = None) -> Any:
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback

def _bool(value: Any) -> bool:
    return value is True or value == 1 or value == "1"

def _ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"
