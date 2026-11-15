# Inputs: Cloudflare D1 account/database identifiers, API token, SQL text, and typed positional SQL parameters.
# Outputs: D1Client query/batch methods returning decoded row dictionaries and statement metadata.
# Explanation: Provides the only D1 REST transport used by the API and orchestrator; callers never access Cloudflare endpoints directly.
from __future__ import annotations

from typing import Any, Iterable, Sequence

import httpx

from .config import Settings


class DatabaseError(RuntimeError):
    pass


class D1Client:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self._client = client
        self._owns_client = client is None
        self.base_url = (
            f"{settings.d1_api_base_url.rstrip('/')}/accounts/"
            f"{settings.cloudflare_account_id}/d1/database/"
            f"{settings.cloudflare_database_id}/query"
        )

    async def open(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=5.0),
                headers={
                    "Authorization": f"Bearer {self.settings.cloudflare_api_token}",
                    "Content-Type": "application/json",
                },
            )

    async def close(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
        self._client = None if self._owns_client else self._client

    async def query(self, sql: str, params: Sequence[Any] = ()) -> dict[str, Any]:
        results = await self.batch([{"sql": sql, "params": list(params)}])
        return results[0] if results else {"results": [], "meta": {"changes": 0}}

    async def batch(self, statements: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        await self.open()
        payload = {
            "batch": [
                {"sql": statement["sql"], "params": list(statement.get("params", []))}
                for statement in statements
            ]
        }
        if not payload["batch"]:
            return []
        assert self._client is not None
        try:
            response = await self._client.post(self.base_url, json=payload)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise DatabaseError(f"D1 request failed: {exc}") from exc
        if not isinstance(body, dict) or body.get("success") is False:
            errors = body.get("errors", []) if isinstance(body, dict) else []
            raise DatabaseError(f"D1 API rejected the request: {errors}")
        raw_results = body.get("result", [])
        if isinstance(raw_results, dict):
            raw_results = [raw_results]
        if not isinstance(raw_results, list):
            raise DatabaseError("D1 response did not contain a result list")
        normalized: list[dict[str, Any]] = []
        for result in raw_results:
            if not isinstance(result, dict) or result.get("success") is False:
                raise DatabaseError(f"D1 statement failed: {result}")
            normalized.append(
                {
                    "results": result.get("results", []) or [],
                    "meta": result.get("meta", {}) or {},
                    "success": result.get("success", True),
                }
            )
        return normalized


def rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    data = result.get("results", [])
    return [dict(row) for row in data if isinstance(row, dict)]


def changes(result: dict[str, Any]) -> int:
    return int((result.get("meta") or {}).get("changes", 0))


def last_row_id(result: dict[str, Any]) -> int | None:
    value = (result.get("meta") or {}).get("last_row_id")
    return int(value) if value not in (None, "") else None
