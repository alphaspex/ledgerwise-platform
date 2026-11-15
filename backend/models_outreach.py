# Inputs: JSON request bodies, query values, and decoded D1 rows conforming to frontend/src/shared/types.ts.
# Outputs: validated Pydantic request, response, and enum types with exact frontend field names and nullable fields.
# Explanation: Defines the backend wire contract in small domain-specific schema modules.
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models_common import WireModel, ContactRole, ContactSource, EmailStatus, MessageSender, MessageStatus, ThreadState, ToolName


class ContactRequest(WireModel):
    contact_email: str
    contact_role: ContactRole


class EmailDraft(WireModel):
    message_id: int
    company_id: int
    domain: str
    contact_email: str
    contact_role: ContactRole
    body: str
    facts: list[MemoryFact]
    created_at: str


class EmailReviewRequest(WireModel):
    action: str
    body: str | None = None

    @model_validator(mode="after")
    def validate_action(self):
        if self.action not in {"approve", "edit", "reject"}:
            raise ValueError("action must be approve, edit, or reject")
        if self.action == "edit" and not self.body:
            raise ValueError("body is required for edit")
        return self


class ToolCall(WireModel):
    name: ToolName
    args: dict[str, Any]
    result: dict[str, Any] | None


class ThreadMessage(WireModel):
    id: int
    company_id: int
    sender_type: MessageSender
    body: str
    status: MessageStatus
    tool_calls: list[ToolCall] | None
    created_at: str
    updated_at: str


class ThreadSummary(WireModel):
    company_id: int
    domain: str
    contact_email: str | None
    thread_state: ThreadState
    last_message_preview: str
    last_message_sender: MessageSender
    last_message_at: str


class ThreadDetail(WireModel):
    summary: ThreadSummary
    messages: list[ThreadMessage]


class HumanReplyRequest(WireModel):
    body: str = Field(min_length=1, max_length=10000)
