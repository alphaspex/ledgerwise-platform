# Inputs: JSON request bodies, query values, and decoded D1 rows conforming to frontend/src/shared/types.ts.
# Outputs: validated Pydantic request, response, and enum types with exact frontend field names and nullable fields.
# Explanation: Defines the backend's wire contract; D1 integer flags are converted to JSON booleans before response validation.
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


class OkResponse(WireModel):
    ok: bool = True


class ErrorBody(WireModel):
    detail: str


class AuthUser(WireModel):
    id: int
    email: str
    is_admin: bool


class UserSummary(AuthUser):
    created_at: str


class AuthEvent(WireModel):
    id: int
    user_id: int | None
    event: AuthEventType
    ip: str | None
    user_agent: str | None
    detail: str | None
    created_at: str


class LoginRequest(WireModel):
    email: str
    password: str


class LoginResponse(WireModel):
    token: str
    user: AuthUser


class ChangePasswordRequest(WireModel):
    old_password: str


class ChangePasswordConfirmRequest(WireModel):
    code: str
    new_password: str
    new_password_confirm: str


class ForgotPasswordRequest(WireModel):
    email: str


class ResetPasswordRequest(WireModel):
    email: str
    code: str
    new_password: str
    new_password_confirm: str


class AcceptInviteRequest(ResetPasswordRequest):
    pass


class InviteRequest(WireModel):
    email: str


class AuthEventsQuery(WireModel):
    limit: int = Field(default=50, ge=1, le=500)


class ResearchRun(WireModel):
    id: int
    status: ResearchRunStatus
    selection: str
    target_approved: int
    created_at: str


class ResearchStatus(WireModel):
    run: ResearchRun | None
    counts: dict[str, int]
    progress: dict[str, int]
    tokens: dict[str, int]
    searches: int


class StartResearchRequest(WireModel):
    selection: str = Field(min_length=1, max_length=4000)


class ReviewCompanyRequest(WireModel):
    company_id: int
    decision: str

    @field_validator("decision")
    @classmethod
    def valid_decision(cls, value: str) -> str:
        if value not in {"human_approved", "human_rejected"}:
            raise ValueError("decision must be human_approved or human_rejected")
        return value


class Reason(WireModel):
    text: str
    source_url: str
    quote: str


class SourceCheck(WireModel):
    url: str
    result: SourceResult
    status: int | None


class DomainCheck(WireModel):
    bucket: int
    status: int | None
    redirected_to: str | None

    @field_validator("bucket")
    @classmethod
    def valid_bucket(cls, value: int) -> int:
        if value not in (1, 2, 3):
            raise ValueError("bucket must be 1, 2, or 3")
        return value


class ResearchData(WireModel):
    reasons: list[Reason]
    domain_check: DomainCheck | None = None
    sources: list[SourceCheck]


class MemoryFact(WireModel):
    field: str
    value: str
    source_url: str
    quote: str


class Memory(WireModel):
    facts: list[MemoryFact]
    audit: dict[str, Any] | None = None


class CompanySummary(WireModel):
    id: int
    domain: str
    score: int | None
    status: CompanyStatus
    email_status: EmailStatus
    thread_state: ThreadState
    do_not_contact: bool
    contact_email: str | None
    contact_role: ContactRole | None
    domain_check: DomainCheck | None
    reasons_preview: list[Reason]
    created_at: str
    updated_at: str


class CompanyDetail(CompanySummary):
    run_id: int
    contact_source: ContactSource | None
    research_data: ResearchData | None
    memory: Memory | None


class CompaniesQuery(WireModel):
    status: list[CompanyStatus] | None = None
    has_contact: bool | None = None


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


class DashboardSummary(WireModel):
    research: dict[str, int]
    emails: dict[str, int]
    conversations: dict[str, int]
    bookings: dict[str, int]
    notifications: dict[str, int]


class WebhookAck(WireModel):
    ok: bool
