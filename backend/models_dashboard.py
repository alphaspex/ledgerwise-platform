# Inputs: JSON response data aggregated from D1 model_usage and model_usage_pricing rows.
# Outputs: validated dashboard usage totals, per-module token/search/cost totals, and dashboard summary schemas.
# Explanation: Defines API response models for usage volume and the user-configured model/search pricing.
from __future__ import annotations

from pydantic import Field

from .models_common import WireModel


class ModelUsageTotals(WireModel):
    calls: int
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    searches: int
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
