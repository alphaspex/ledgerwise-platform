# Inputs: JSON request bodies, query values, and decoded D1 rows conforming to frontend/src/shared/types.ts.
# Outputs: validated Pydantic request, response, and enum types with exact frontend field names and nullable fields.
# Explanation: Defines the backend wire contract in small domain-specific schema modules.
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models_common import WireModel


class DashboardSummary(WireModel):
    research: dict[str, int]
    emails: dict[str, int]
    conversations: dict[str, int]
    bookings: dict[str, int]
    notifications: dict[str, int]


class WebhookAck(WireModel):
    ok: bool
