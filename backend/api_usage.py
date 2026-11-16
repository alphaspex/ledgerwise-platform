# Inputs: D1Client, optional company_id: int, optional module: str, and persisted token/search pricing rows.
# Outputs: ModelUsageSummary with token totals, web-search totals, per-module breakdowns, and configured USD costs.
# Explanation: Aggregates token data separately from the optional pricing table so missing cost data cannot break primary API responses.
from __future__ import annotations

import logging
from typing import Any

from .db import D1Client, DatabaseError, rows
from .models_dashboard import ModelUsageSummary, ModelUsageTotals

logger = logging.getLogger(__name__)


def _usage_totals(row: dict[str, Any]) -> ModelUsageTotals:
    calls = int(row.get("calls") or 0)
    input_tokens = int(row.get("input_tokens") or 0)
    output_tokens = int(row.get("output_tokens") or 0)
    reasoning_tokens = int(row.get("reasoning_tokens") or 0)
    searches = int(row.get("searches") or 0)
    priced_calls = int(row.get("priced_calls") or 0)
    cost_complete = calls == priced_calls
    raw_cost = row.get("cost_usd")
    if calls == 0:
        cost_usd: float | None = 0.0
    elif cost_complete and raw_cost is not None:
        cost_usd = float(raw_cost)
    else:
        cost_usd = None
    return ModelUsageTotals(
        calls=calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        searches=searches,
        total_tokens=input_tokens + output_tokens,
        cost_usd=cost_usd,
        cost_complete=cost_complete,
    )


def _with_cost(totals: ModelUsageTotals, cost_row: dict[str, Any] | None) -> ModelUsageTotals:
    if cost_row is None:
        return totals
    priced_calls = int(cost_row.get("priced_calls") or 0)
    complete = totals.calls == priced_calls
    cost_value = cost_row.get("cost_usd")
    cost = 0.0 if totals.calls == 0 else (
        float(cost_value) if complete and cost_value is not None else None
    )
    return totals.model_copy(update={"cost_usd": cost, "cost_complete": complete, "searches": int(cost_row.get("searches") or 0)})


def _empty_summary() -> ModelUsageSummary:
    return ModelUsageSummary(
        calls=0, input_tokens=0, output_tokens=0, reasoning_tokens=0, searches=0,
        total_tokens=0, cost_usd=None, cost_complete=False, by_module={},
    )


async def _model_usage_summary(
    db: D1Client,
    company_id: int | None = None,
    module: str | None = None,
) -> ModelUsageSummary:
    clauses: list[str] = []
    params: list[Any] = []
    if company_id is not None:
        clauses.append("u.company_id=?")
        params.append(company_id)
    if module is not None:
        clauses.append("u.module=?")
        params.append(module)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""

    aggregate = (
        "SELECT COUNT(*) AS calls,"
        "COALESCE(SUM(u.input_tokens),0) AS input_tokens,"
        "COALESCE(SUM(u.output_tokens),0) AS output_tokens,"
        "COALESCE(SUM(u.reasoning_tokens),0) AS reasoning_tokens "
        "FROM model_usage u" + where
    )
    by_module = (
        "SELECT u.module AS module,COUNT(*) AS calls,"
        "COALESCE(SUM(u.input_tokens),0) AS input_tokens,"
        "COALESCE(SUM(u.output_tokens),0) AS output_tokens,"
        "COALESCE(SUM(u.reasoning_tokens),0) AS reasoning_tokens "
        "FROM model_usage u" + where + " GROUP BY u.module ORDER BY u.module"
    )
    try:
        token_results = await db.batch([
            {"sql": aggregate, "params": params},
            {"sql": by_module, "params": params},
        ])
    except DatabaseError:
        logger.exception("Could not read optional model_usage totals from D1")
        return _empty_summary()

    total_rows = rows(token_results[0])
    total = _usage_totals(total_rows[0] if total_rows else {})
    modules = {
        str(row["module"]): _usage_totals(row)
        for row in rows(token_results[1])
    }

    cost_aggregate = (
        "SELECT COUNT(p.usage_id) AS priced_calls,COALESCE(SUM(p.cost_usd),0) AS cost_usd,COALESCE(SUM(p.searches),0) AS searches "
        "FROM model_usage u LEFT JOIN model_usage_pricing p ON p.usage_id=u.id" + where
    )
    cost_by_module = (
        "SELECT u.module AS module,COUNT(p.usage_id) AS priced_calls,"
        "COALESCE(SUM(p.cost_usd),0) AS cost_usd,COALESCE(SUM(p.searches),0) AS searches "
        "FROM model_usage u LEFT JOIN model_usage_pricing p ON p.usage_id=u.id" +
        where + " GROUP BY u.module ORDER BY u.module"
    )
    try:
        cost_results = await db.batch([
            {"sql": cost_aggregate, "params": params},
            {"sql": cost_by_module, "params": params},
        ])
        cost_rows = rows(cost_results[0])
        total = _with_cost(total, cost_rows[0] if cost_rows else None)
        module_costs = {str(row["module"]): row for row in rows(cost_results[1])}
        modules = {
            name: _with_cost(usage, module_costs.get(name))
            for name, usage in modules.items()
        }
    except DatabaseError:
        logger.exception("Could not read optional model_usage_pricing from D1; returning token totals without costs")

    return ModelUsageSummary(**total.model_dump(), by_module=modules)
