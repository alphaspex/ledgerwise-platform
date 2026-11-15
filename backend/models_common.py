# Inputs: JSON request bodies, query values, and decoded D1 rows conforming to frontend/src/shared/types.ts.
# Outputs: validated Pydantic request, response, and enum types with exact frontend field names and nullable fields.
# Explanation: Defines the backend wire contract in small domain-specific schema modules.
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ContactRole(str, Enum):
    founder = "founder"
    coo = "coo"
    finance = "finance"
    unknown = "unknown"


class ContactSource(str, Enum):
    manual = "manual"
    apollo = "apollo"


class CompanyStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    needs_human_review = "needs_human_review"
    human_approved = "human_approved"
    human_rejected = "human_rejected"
    rejected_low_evidence = "rejected_low_evidence"
    failed_404 = "failed_404"
    failed_enrichment = "failed_enrichment"


class EmailStatus(str, Enum):
    not_started = "not_started"
    drafting = "drafting"
    pending_review = "pending_review"
    approved = "approved"
    sent = "sent"
    rejected_by_human = "rejected_by_human"
    failed_contact = "failed_contact"


class ThreadState(str, Enum):
    inactive = "inactive"
    auto = "auto"
    needs_human = "needs_human"
    human_taken_over = "human_taken_over"
    closed = "closed"


class ResearchRunStatus(str, Enum):
    running = "running"
    paused = "paused"
    done = "done"


class SourceResult(str, Enum):
    untested = "untested"
    live = "live"
    dead = "dead"
    unverified = "unverified"


class MessageSender(str, Enum):
    agent = "agent"
    prospect = "prospect"
    human = "human"


class MessageStatus(str, Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    sent = "sent"
    received = "received"
    failed = "failed"
    blocked_by_do_not_contact = "blocked_by_do_not_contact"


class BookingStatus(str, Enum):
    booked = "booked"
    cancelled = "cancelled"
    rescheduled = "rescheduled"
    completed = "completed"


class BookingSource(str, Enum):
    agent = "agent"
    prospect_link = "prospect_link"


class NotificationReason(str, Enum):
    unsure_answer = "unsure_answer"
    do_not_contact = "do_not_contact"
    booking_conflict = "booking_conflict"
    contact_missing = "contact_missing"


class AuthEventType(str, Enum):
    login_ok = "login_ok"
    login_fail = "login_fail"
    password_change = "password_change"
    password_reset = "password_reset"
    invite_sent = "invite_sent"
    invite_accepted = "invite_accepted"
    user_removed = "user_removed"
    logout = "logout"
    rate_limited = "rate_limited"


class ToolName(str, Enum):
    check_availability = "check_availability"
    book_slot = "book_slot"
    call_human = "call_human"
