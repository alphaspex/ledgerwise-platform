# Inputs: JSON response data aggregated from persisted D1 model_usage rows.
# Outputs: validated dashboard usage totals, per-module usage totals, and dashboard summary schemas.
# Explanation: Defines the API response models for token volume and optional, explicitly priced model costs.
from __future__ import annotations

from pydantic import Field

from .models_common import WireModel


class ModelUsageTotals(WireModel):
    calls: int
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    total_tokens: int
    cost_usd: float | None
    cost_complete: bool


class ModelUsageSummary(ModelUsageTotals):
    by_module: dict[str, ModelUsageTotals]


class DashboardSummary(WireModel):
    research: dict[str, int]
    emails: dict[str, int]
    conversations: dict[str, int]
    bookings: dict[str, int]
    notifications: dict[str, int]
    usage: ModelUsageSummary


class WebhookAck(WireModel):
    ok: bool
