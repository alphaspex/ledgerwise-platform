# Inputs: orchestrator dependencies, queue jobs, and completed worker results for the Ledgerwise backend.
# Outputs: bounded worker and orchestration methods that return data or append state for the single writer.
# Explanation: Implements one focused orchestrator responsibility; D1 queue writes remain in tick commit stages.
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from typing import Any

def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _load(value: Any, fallback: Any):
    if isinstance(value, (dict, list)):
        return value
    try:
        parsed = json.loads(value or "")
        return parsed
    except (TypeError, json.JSONDecodeError):
        return fallback


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json_object(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    raw = re.sub(r"^\u0060\u0060\u0060(?:json)?\s*|\s*\u0060\u0060\u0060$", "", raw, flags=re.I)
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None
