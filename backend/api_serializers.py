# Inputs: FastAPI request context, D1 rows, and the frontend API request/response contract.
# Outputs: shared request helpers, serializers, authentication helpers, and route routers.
# Explanation: Keeps backend.api.router stable while route handlers live in focused modules.
from __future__ import annotations
from typing import Any
from .models import AuthUser, UserSummary, CompanySummary, CompanyDetail, ThreadMessage, ThreadSummary
from .api_common import _iso, _json_load, _bool

def _user(row: dict[str, Any]) -> AuthUser:
    return AuthUser(id=int(row["id"]), email=str(row["email"]), is_admin=_bool(row["is_admin"]))

def _user_summary(row: dict[str, Any]) -> UserSummary:
    return UserSummary(id=int(row["id"]), email=str(row["email"]), is_admin=_bool(row["is_admin"]), created_at=_iso(row["created_at"]))

def _reason_preview(research: dict[str, Any]) -> list[dict[str, Any]]:
    return (research.get("reasons") or [])[:3]

def _company_summary(row: dict[str, Any]) -> CompanySummary:
    research = _json_load(row.get("research_data"), {}) or {}
    return CompanySummary(
        id=int(row["id"]),
        domain=str(row["domain"]),
        score=int(row["score"]) if row.get("score") is not None else None,
        status=row["status"],
        email_status=row.get("email_status") or "not_started",
        thread_state=row.get("thread_state") or "inactive",
        do_not_contact=_bool(row.get("do_not_contact", 0)),
        contact_email=row.get("contact_email"),
        contact_role=row.get("contact_role"),
        domain_check=research.get("domain_check"),
        reasons_preview=_reason_preview(research),
        created_at=_iso(row.get("created_at")),
        updated_at=_iso(row.get("updated_at")),
    )

def _company_detail(row: dict[str, Any]) -> CompanyDetail:
    summary = _company_summary(row).model_dump()
    research = _json_load(row.get("research_data"), None)
    memory = _json_load(row.get("memory"), None)
    if isinstance(memory, dict):
        memory = {"facts": memory.get("facts", [])}
    summary.update({
        "run_id": int(row["run_id"]),
        "contact_source": row.get("contact_source"),
        "research_data": research,
        "memory": memory,
    })
    return CompanyDetail.model_validate(summary)

def _message(row: dict[str, Any]) -> ThreadMessage:
    return ThreadMessage(
        id=int(row["id"]),
        company_id=int(row["company_id"]),
        sender_type=row["sender_type"],
        body=row["body"],
        status=row["status"],
        tool_calls=_json_load(row.get("tool_calls"), None),
        created_at=_iso(row["created_at"]),
        updated_at=_iso(row["updated_at"]),
    )

def _thread_summary(row: dict[str, Any]) -> ThreadSummary:
    return ThreadSummary(
        company_id=int(row["company_id"]),
        domain=row["domain"],
        contact_email=row.get("contact_email"),
        thread_state=row["thread_state"],
        last_message_preview=str(row.get("last_message_preview") or ""),
        last_message_sender=row.get("last_message_sender") or "agent",
        last_message_at=_iso(row.get("last_message_at")),
    )
