# Inputs: D1Client, optional company_id: int, and optional module: str.
# Outputs: ModelUsageSummary with total calls, input/output/reasoning tokens, optional cost, and per-module breakdowns.
# Explanation: Aggregates durable per-call model usage without inventing costs for rows that have no configured pricing.
from __future__ import annotations

from typing import Any

from .db import D1Client, rows
from .models_dashboard import ModelUsageSummary, ModelUsageTotals


def _usage_totals(row: dict[str, Any]) -> ModelUsageTotals:
    calls = int(row.get("calls") or 0)
    input_tokens = int(row.get("input_tokens") or 0)
    output_tokens = int(row.get("output_tokens") or 0)
    reasoning_tokens = int(row.get("reasoning_tokens") or 0)
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
        total_tokens=input_tokens + output_tokens,
        cost_usd=cost_usd,
        cost_complete=cost_complete,
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
        "COALESCE(SUM(input_tokens),0) AS input_tokens,"
        "COALESCE(SUM(output_tokens),0) AS output_tokens,"
        "COALESCE(SUM(reasoning_tokens),0) AS reasoning_tokens,"
        "COUNT(c.cost_usd) AS priced_calls,SUM(c.cost_usd) AS cost_usd "
        "FROM model_usage u LEFT JOIN model_usage_costs c ON c.usage_id=u.id" + where
    )
    by_module = (
        "SELECT u.module AS module,COUNT(*) AS calls,"
        "COALESCE(SUM(input_tokens),0) AS input_tokens,"
        "COALESCE(SUM(output_tokens),0) AS output_tokens,"
        "COALESCE(SUM(reasoning_tokens),0) AS reasoning_tokens,"
        "COUNT(cost_usd) AS priced_calls,SUM(cost_usd) AS cost_usd "
        "FROM model_usage u LEFT JOIN model_usage_costs c ON c.usage_id=u.id" + where + " GROUP BY u.module ORDER BY u.module"
    )
    results = await db.batch([
        {"sql": aggregate, "params": params},
        {"sql": by_module, "params": params},
    ])
    total_rows = rows(results[0])
    total = _usage_totals(total_rows[0] if total_rows else {})
    modules = {
        str(row["module"]): _usage_totals(row)
        for row in rows(results[1])
    }
    return ModelUsageSummary(**total.model_dump(), by_module=modules)
