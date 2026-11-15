# Inputs: JSON request bodies, query values, and decoded D1 rows conforming to frontend/src/shared/types.ts.
# Outputs: validated Pydantic request, response, and enum types with exact frontend field names and nullable fields.
# Explanation: Defines the backend wire contract in small domain-specific schema modules.
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models_common import WireModel, BookingSource, BookingStatus, NotificationReason


class Booking(WireModel):
    id: int
    company_id: int
    domain: str
    cal_booking_uid: str
    scheduled_at: str
    status: BookingStatus
    source: BookingSource
    created_at: str
    updated_at: str


class BookingsQuery(WireModel):
    from_: str = Field(alias="from")
    to: str

    @field_validator("from_", "to")
    @classmethod
    def iso_datetime(cls, value: str) -> str:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("must be an ISO date-time string") from exc
        return value

    @model_validator(mode="after")
    def valid_range(self):
        start = datetime.fromisoformat(self.from_.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.to.replace("Z", "+00:00"))
        if end <= start:
            raise ValueError("to must be later than from")
        return self


class Notification(WireModel):
    id: int
    company_id: int
    domain: str
    reason: NotificationReason
    body: str | None
    read: bool
    created_at: str


class MarkReadRequest(WireModel):
    ids: list[int] = Field(min_length=1)
