# Inputs: FastAPI requests matching frontend/src/api/endpoints.ts and frontend/src/shared/types.ts, plus D1 and provider clients in app.state.
# Outputs: the 29 contract routes, JSON error bodies, authenticated responses, and signed inbound-email/Cal.com webhook acknowledgements.
# Explanation: Implements the public backend HTTP boundary; it validates wire types, enforces route permissions, writes standard rows, and never writes module_1_queues.
from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timezone
from email.utils import parseaddr
from typing import Any
from urllib.parse import quote

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import ValidationError

from .config import Settings
from .db import D1Client, changes, last_row_id, rows
from .integrations import is_generic_email, normalize_domain, verify_hmac_signature
from .models import (
    AcceptInviteRequest, AuthEvent, AuthEventsQuery, AuthUser, Booking, BookingsQuery,
    ChangePasswordConfirmRequest, ChangePasswordRequest, CompaniesQuery, CompanyDetail,
    CompanySummary, ContactRequest, DashboardSummary, EmailDraft, EmailReviewRequest,
    ForgotPasswordRequest, HumanReplyRequest, InviteRequest, LoginRequest, LoginResponse,
    MarkReadRequest, Notification, OkResponse, ResearchRun, ResearchStatus,
    ResetPasswordRequest, ReviewCompanyRequest, StartResearchRequest, ThreadDetail,
    ThreadMessage, ThreadSummary, UserSummary,
)
from .security import create_token, decode_token, hash_code, hash_password, new_code, verify_password


router = APIRouter()


def _db(request: Request) -> D1Client:
    return request.app.state.db


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(value: Any) -> str:
    if value is None:
        return _now()
    raw = str(value)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return raw


def _json_load(value: Any, fallback: Any = None) -> Any:
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _bool(value: Any) -> bool:
    return value is True or value == 1 or value == "1"


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


async def current_user(request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token")
    token = authorization[7:].strip()
    try:
        return decode_token(token, _settings(request))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token")


async def admin_user(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    if not bool(user.get("is_admin")):
        raise HTTPException(status_code=403, detail="Admin only")
    return user


def _ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


async def _event(request: Request, user_id: int | None, event: str, detail: str | None = None) -> None:
    await _db(request).query(
        "INSERT INTO auth_events(user_id,event,ip,user_agent,detail) VALUES (?,?,?,?,?)",
        [user_id, event, _ip(request), request.headers.get("user-agent"), detail],
    )


async def _send_code(request: Request, email: str, user_id: int, purpose: str, code: str, expires_seconds: int) -> None:
    await _db(request).query(
        "INSERT INTO password_codes(user_id,code_hash,purpose,attempts,expires_at) VALUES (?,?,?,?,datetime('now',?))",
        [user_id, hash_code(code), purpose, 0, f"+{expires_seconds} seconds"],
    )
    purpose_label = {"change": "password change", "reset": "password reset", "invite": "invitation"}.get(purpose, purpose)
    text = f"Your Ledgerwise {purpose_label} code is {code}. It expires in {max(1, expires_seconds // 60)} minutes."
    await request.app.state.resend.send(
        to=email,
        subject=f"Your Ledgerwise {purpose_label} code",
        text=text,
        idempotency_key=f"ledgerwise-code-{user_id}-{purpose}-{hash_code(code)[:16]}",
    )


async def _get_code_user(request: Request, email: str, purpose: str) -> tuple[dict[str, Any], dict[str, Any]]:
    user_rows = rows(await _db(request).query("SELECT * FROM users WHERE email=? COLLATE NOCASE", [email]))
    if not user_rows:
        raise HTTPException(status_code=410, detail="Code expired or invalid")
    user = user_rows[0]
    code_rows = rows(await _db(request).query(
        "SELECT * FROM password_codes WHERE user_id=? AND purpose=? ORDER BY id DESC LIMIT 1",
        [int(user["id"]), purpose],
    ))
    if not code_rows:
        raise HTTPException(status_code=410, detail="Code expired or invalid")
    return user, code_rows[0]


async def _check_code(request: Request, user_id: int, code_row: dict[str, Any], code: str) -> None:
    expiry = str(code_row["expires_at"])
    try:
        expired = datetime.fromisoformat(expiry.replace("Z", "+00:00")) <= datetime.now(timezone.utc)
        if datetime.fromisoformat(expiry).tzinfo is None:
            expired = datetime.fromisoformat(expiry).replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc)
    except ValueError:
        expired = True
    if expired or int(code_row.get("attempts", 0)) >= _settings(request).code_max_attempts:
        await _db(request).query("DELETE FROM password_codes WHERE id=?", [int(code_row["id"])])
        raise HTTPException(status_code=410, detail="Code expired or invalidated")
    if not secrets.compare_digest(hash_code(code), str(code_row["code_hash"])):
        attempts = int(code_row.get("attempts", 0)) + 1
        await _db(request).query(
            "UPDATE password_codes SET attempts=? WHERE id=?",
            [attempts, int(code_row["id"])],
        )
        if attempts >= _settings(request).code_max_attempts:
            await _db(request).query("DELETE FROM password_codes WHERE id=?", [int(code_row["id"])])
            raise HTTPException(status_code=410, detail="Code expired or invalidated")
        raise HTTPException(status_code=400, detail="Wrong code")


def _validate_password(password: str, confirm: str, settings: Settings) -> None:
    if password != confirm:
        raise HTTPException(status_code=422, detail="new_password_confirm must match new_password")
    if len(password) < settings.password_min_len:
        raise HTTPException(status_code=422, detail=f"Password must contain at least {settings.password_min_len} characters")


def _new_user_hash(settings: Settings) -> str:
    return hash_password(secrets.token_urlsafe(32), settings.bcrypt_cost)


@router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request):
    found = rows(await _db(request).query("SELECT * FROM users WHERE email=? COLLATE NOCASE", [body.email]))
    user = found[0] if found else None
    if not user or not verify_password(body.password, str(user["password_hash"])):
        await _event(request, int(user["id"]) if user else None, "login_fail")
        raise HTTPException(status_code=401, detail="Wrong email or password")
    await _event(request, int(user["id"]), "login_ok")
    return LoginResponse(token=create_token(user, _settings(request)), user=_user(user))


@router.post("/auth/logout", response_model=OkResponse)
async def logout(request: Request, user: dict[str, Any] = Depends(current_user)):
    await _event(request, int(user["user_id"]), "logout")
    return OkResponse(ok=True)


@router.post("/auth/change-password", response_model=OkResponse)
async def change_password_request(body: ChangePasswordRequest, request: Request, user: dict[str, Any] = Depends(current_user)):
    found = rows(await _db(request).query("SELECT password_hash FROM users WHERE id=?", [int(user["user_id"])]))
    if not found or not verify_password(body.old_password, str(found[0]["password_hash"])):
        raise HTTPException(status_code=400, detail="Old password is wrong")
    code = new_code(_settings(request).code_length)
    await _send_code(request, user["email"], int(user["user_id"]), "change", code, _settings(request).code_exp_seconds)
    return OkResponse(ok=True)


@router.post("/auth/change-password/confirm", response_model=OkResponse)
async def change_password_confirm(body: ChangePasswordConfirmRequest, request: Request, user: dict[str, Any] = Depends(current_user)):
    settings = _settings(request)
    _validate_password(body.new_password, body.new_password_confirm, settings)
    code_user, code_row = await _get_code_user(request, str(user["email"]), "change")
    await _check_code(request, int(code_user["id"]), code_row, body.code)
    await _db(request).batch([
        {"sql": "UPDATE users SET password_hash=? WHERE id=?", "params": [hash_password(body.new_password, settings.bcrypt_cost), int(user["user_id"])]},
        {"sql": "DELETE FROM password_codes WHERE user_id=? AND purpose='change'", "params": [int(user["user_id"])]},
        {"sql": "INSERT INTO auth_events(user_id,event,ip,user_agent) VALUES (?,'password_change',?,?)", "params": [int(user["user_id"]), _ip(request), request.headers.get("user-agent")]},
    ])
    return OkResponse(ok=True)


@router.post("/auth/forgot-password", response_model=OkResponse)
async def forgot_password(body: ForgotPasswordRequest, request: Request):
    found = rows(await _db(request).query("SELECT id,email FROM users WHERE email=? COLLATE NOCASE", [body.email]))
    if found:
        code = new_code(_settings(request).code_length)
        await _send_code(request, str(found[0]["email"]), int(found[0]["id"]), "reset", code, _settings(request).code_exp_seconds)
    return OkResponse(ok=True)


@router.post("/auth/reset-password", response_model=OkResponse)
async def reset_password(body: ResetPasswordRequest, request: Request):
    settings = _settings(request)
    _validate_password(body.new_password, body.new_password_confirm, settings)
    user, code_row = await _get_code_user(request, body.email, "reset")
    await _check_code(request, int(user["id"]), code_row, body.code)
    await _db(request).batch([
        {"sql": "UPDATE users SET password_hash=? WHERE id=?", "params": [hash_password(body.new_password, settings.bcrypt_cost), int(user["id"])]},
        {"sql": "DELETE FROM password_codes WHERE user_id=? AND purpose='reset'", "params": [int(user["id"])]},
        {"sql": "INSERT INTO auth_events(user_id,event) VALUES (?,'password_reset')", "params": [int(user["id"])]},
    ])
    return OkResponse(ok=True)


@router.post("/auth/accept-invite", response_model=OkResponse)
async def accept_invite(body: AcceptInviteRequest, request: Request):
    settings = _settings(request)
    _validate_password(body.new_password, body.new_password_confirm, settings)
    user, code_row = await _get_code_user(request, body.email, "invite")
    await _check_code(request, int(user["id"]), code_row, body.code)
    await _db(request).batch([
        {"sql": "UPDATE users SET password_hash=? WHERE id=?", "params": [hash_password(body.new_password, settings.bcrypt_cost), int(user["id"])]},
        {"sql": "DELETE FROM password_codes WHERE user_id=? AND purpose='invite'", "params": [int(user["id"])]},
        {"sql": "INSERT INTO auth_events(user_id,event) VALUES (?,'invite_accepted')", "params": [int(user["id"])]},
    ])
    return OkResponse(ok=True)


@router.get("/auth/events", response_model=list[AuthEvent])
async def list_auth_events(request: Request, limit: int = Query(default=50, ge=1, le=500), user: dict[str, Any] = Depends(current_user)):
    result = rows(await _db(request).query(
        "SELECT * FROM auth_events WHERE created_at >= datetime('now', ?) ORDER BY created_at DESC,id DESC LIMIT ?",
        [f"-{_settings(request).auth_events_retention_days} days", limit],
    ))
    return [AuthEvent(
        id=int(row["id"]), user_id=int(row["user_id"]) if row.get("user_id") is not None else None,
        event=row["event"], ip=row.get("ip"), user_agent=row.get("user_agent"),
        detail=row.get("detail"), created_at=_iso(row["created_at"]),
    ) for row in result]


@router.get("/admin/users", response_model=list[UserSummary])
async def list_users(request: Request, admin: dict[str, Any] = Depends(admin_user)):
    result = rows(await _db(request).query("SELECT id,email,is_admin,created_at FROM users ORDER BY created_at DESC,id DESC"))
    return [_user_summary(row) for row in result]


@router.post("/admin/users/invite", response_model=UserSummary)
async def invite_user(body: InviteRequest, request: Request, admin: dict[str, Any] = Depends(admin_user)):
    settings = _settings(request)
    existing = rows(await _db(request).query("SELECT id FROM users WHERE email=? COLLATE NOCASE", [body.email]))
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")
    code = new_code(settings.code_length)
    await _db(request).batch([
        {"sql": "INSERT INTO users(email,password_hash,is_admin) VALUES (?,?,0)", "params": [body.email, _new_user_hash(settings)]},
        {"sql": "INSERT INTO password_codes(user_id,code_hash,purpose,attempts,expires_at) VALUES (last_insert_rowid(),?,'invite',0,datetime('now',?))", "params": [hash_code(code), f"+{settings.invite_exp_seconds} seconds"]},
        {"sql": "INSERT INTO auth_events(user_id,event,ip,user_agent) VALUES (last_insert_rowid(),'invite_sent',?,?)", "params": [_ip(request), request.headers.get("user-agent")]},
    ])
    created = rows(await _db(request).query("SELECT id,email,is_admin,created_at FROM users WHERE email=? COLLATE NOCASE", [body.email]))
    if not created:
        raise HTTPException(status_code=422, detail="Could not create invitation")
    invite_url = settings.public_app_url.rstrip("/") + "/accept-invite?email=" + quote(body.email) + "&code=" + quote(code)
    await request.app.state.resend.send(
        to=body.email, subject="Your Ledgerwise invitation",
        text=f"Accept your Ledgerwise invitation using this link: {invite_url}",
        idempotency_key=f"ledgerwise-invite-{int(created[0]['id'])}",
    )
    return _user_summary(created[0])


@router.delete("/admin/users/{id}", response_model=OkResponse)
async def remove_user(id: int, request: Request, admin: dict[str, Any] = Depends(admin_user)):
    found = rows(await _db(request).query("SELECT id FROM users WHERE id=?", [id]))
    if not found:
        raise HTTPException(status_code=404, detail="User not found")
    await _db(request).batch([
        {"sql": "INSERT INTO auth_events(user_id,event,ip,user_agent) VALUES (?,'user_removed',?,?)", "params": [id, _ip(request), request.headers.get("user-agent")]},
        {"sql": "DELETE FROM users WHERE id=?", "params": [id]},
    ])
    return OkResponse(ok=True)


@router.post("/research/start", response_model=ResearchRun)
async def start_research(body: StartResearchRequest, request: Request, user: dict[str, Any] = Depends(current_user)):
    result = await _db(request).query(
        "INSERT INTO research_runs(status,selection,target_approved) SELECT 'running',?,? WHERE NOT EXISTS (SELECT 1 FROM research_runs WHERE status IN ('running','paused')) RETURNING id,status,selection,target_approved,created_at",
        [body.selection, _settings(request).target_approved],
    )
    created = rows(result)
    if not created:
        raise HTTPException(status_code=409, detail="A research run is already running or paused")
    await _db(request).query(
        "UPDATE module_1_queues SET version=version+1,system_status=? WHERE id=1",
        [json.dumps({"run_id": int(created[0]["id"]), "counts": {}, "progress": {"search_jobs": 0}, "tokens": {"in": 0, "out": 0}, "searches": 0})],
    )
    return ResearchRun(id=int(created[0]["id"]), status=created[0]["status"], selection=created[0]["selection"], target_approved=int(created[0]["target_approved"]), created_at=_iso(created[0]["created_at"]))


@router.post("/research/pause", response_model=ResearchRun)
async def pause_research(request: Request, user: dict[str, Any] = Depends(current_user)):
    result = rows(await _db(request).query(
        "UPDATE research_runs SET status='paused' WHERE id=(SELECT id FROM research_runs WHERE status='running' ORDER BY id DESC LIMIT 1) RETURNING id,status,selection,target_approved,created_at"
    ))
    if not result:
        raise HTTPException(status_code=409, detail="No running run")
    row = result[0]
    return ResearchRun(id=int(row["id"]), status=row["status"], selection=row["selection"], target_approved=int(row["target_approved"]), created_at=_iso(row["created_at"]))


@router.post("/research/resume", response_model=ResearchRun)
async def resume_research(request: Request, user: dict[str, Any] = Depends(current_user)):
    result = rows(await _db(request).query(
        "UPDATE research_runs SET status='running' WHERE id=(SELECT id FROM research_runs WHERE status='paused' ORDER BY id DESC LIMIT 1) RETURNING id,status,selection,target_approved,created_at"
    ))
    if not result:
        raise HTTPException(status_code=409, detail="No paused run")
    row = result[0]
    return ResearchRun(id=int(row["id"]), status=row["status"], selection=row["selection"], target_approved=int(row["target_approved"]), created_at=_iso(row["created_at"]))


@router.get("/research/status", response_model=ResearchStatus)
async def get_research_status(request: Request, user: dict[str, Any] = Depends(current_user)):
    snapshot = request.app.state.orchestrator.snapshot if request.app.state.orchestrator else {}
    return ResearchStatus(
        run=snapshot.get("run"),
        counts=snapshot.get("counts", {}),
        progress=snapshot.get("progress", {"search_jobs": 0}),
        tokens=snapshot.get("tokens", {"in": 0, "out": 0}),
        searches=int(snapshot.get("searches", 0)),
    )


@router.get("/companies", response_model=list[CompanySummary])
async def list_companies(
    request: Request,
    status: str | None = Query(default=None),
    has_contact: bool | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    statuses = [value.strip() for value in status.split(",") if value.strip()] if status else []
    known = {"pending", "approved", "needs_human_review", "human_approved", "human_rejected", "rejected_low_evidence", "failed_404", "failed_enrichment"}
    if any(value not in known for value in statuses):
        raise HTTPException(status_code=422, detail="status contains an unsupported company status")
    clauses = []
    params: list[Any] = []
    if statuses:
        clauses.append("status IN (" + ",".join("?" for _ in statuses) + ")")
        params.extend(statuses)
    if has_contact is True:
        clauses.append("contact_email IS NOT NULL")
    elif has_contact is False:
        clauses.append("contact_email IS NULL")
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    result = rows(await _db(request).query("SELECT * FROM companies" + where + " ORDER BY created_at DESC,id DESC", params))
    return [_company_summary(row) for row in result]


@router.get("/companies/{id}", response_model=CompanyDetail)
async def get_company(id: int, request: Request, user: dict[str, Any] = Depends(current_user)):
    result = rows(await _db(request).query("SELECT * FROM companies WHERE id=?", [id]))
    if not result:
        raise HTTPException(status_code=404, detail="Company not found")
    return _company_detail(result[0])


@router.post("/research/review", response_model=OkResponse)
async def review_company(body: ReviewCompanyRequest, request: Request, user: dict[str, Any] = Depends(current_user)):
    found = rows(await _db(request).query("SELECT id,domain,status FROM companies WHERE id=?", [body.company_id]))
    if not found:
        raise HTTPException(status_code=404, detail="Company not found")
    if found[0]["status"] != "needs_human_review":
        raise HTTPException(status_code=409, detail="Company is not in needs_human_review")
    domain_status = "approved" if body.decision == "human_approved" else "human_rejected"
    await _db(request).batch([
        {"sql": "UPDATE companies SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [body.decision, body.company_id]},
        {"sql": "UPDATE domain_memory SET status=? WHERE domain=?", "params": [domain_status, found[0]["domain"]]},
    ])
    return OkResponse(ok=True)


@router.put("/companies/{id}/contact", response_model=CompanySummary)
async def save_contact(id: int, body: ContactRequest, request: Request, user: dict[str, Any] = Depends(current_user)):
    email = parseaddr(body.contact_email)[1].strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or is_generic_email(email):
        raise HTTPException(status_code=422, detail="Invalid named contact email")
    result = rows(await _db(request).query(
        "UPDATE companies SET contact_email=?,contact_role=?,contact_source='manual',updated_at=CURRENT_TIMESTAMP WHERE id=? RETURNING *",
        [email, body.contact_role.value, id],
    ))
    if not result:
        raise HTTPException(status_code=404, detail="Company not found")
    return _company_summary(result[0])


@router.get("/emails/drafts", response_model=list[EmailDraft])
async def list_email_drafts(request: Request, user: dict[str, Any] = Depends(current_user)):
    result = rows(await _db(request).query(
        "SELECT tm.*,c.domain,c.contact_email,c.contact_role,c.memory FROM thread_messages tm JOIN companies c ON c.id=tm.company_id WHERE tm.sender_type='agent' AND tm.status='pending_review' ORDER BY tm.created_at DESC,tm.id DESC"
    ))
    output = []
    for row in result:
        memory = _json_load(row.get("memory"), {}) or {}
        output.append(EmailDraft(
            message_id=int(row["id"]), company_id=int(row["company_id"]), domain=row["domain"],
            contact_email=row["contact_email"], contact_role=row["contact_role"] or "unknown",
            body=row["body"], facts=memory.get("facts", []), created_at=_iso(row["created_at"]),
        ))
    return output


@router.post("/emails/{message_id}/review", response_model=OkResponse)
async def review_email(message_id: int, body: EmailReviewRequest, request: Request, user: dict[str, Any] = Depends(current_user)):
    found = rows(await _db(request).query(
        "SELECT tm.id,tm.company_id,tm.status FROM thread_messages tm WHERE tm.id=? AND tm.sender_type='agent'",
        [message_id],
    ))
    if not found:
        raise HTTPException(status_code=404, detail="Draft not found")
    if found[0]["status"] != "pending_review":
        raise HTTPException(status_code=409, detail="Draft is no longer pending_review")
    company_id = int(found[0]["company_id"])
    if body.action == "reject":
        await _db(request).batch([
            {"sql": "UPDATE thread_messages SET status='failed',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [message_id]},
            {"sql": "UPDATE companies SET email_status='rejected_by_human',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [company_id]},
        ])
    else:
        statements = []
        if body.action == "edit":
            statements.append({"sql": "UPDATE thread_messages SET body=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [body.body, message_id]})
        statements.extend([
            {"sql": "UPDATE thread_messages SET status='approved',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [message_id]},
            {"sql": "UPDATE companies SET email_status='approved',updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [company_id]},
            {"sql": "INSERT INTO module_2_queue(type,company_id,message_id,state) VALUES ('send',?,?,'pending')", "params": [company_id, message_id]},
        ])
        await _db(request).batch(statements)
    return OkResponse(ok=True)


@router.get("/threads", response_model=list[ThreadSummary])
async def list_threads(request: Request, user: dict[str, Any] = Depends(current_user)):
    result = rows(await _db(request).query(
        "SELECT c.id AS company_id,c.domain,c.contact_email,c.thread_state,tm.body AS last_message_preview,tm.sender_type AS last_message_sender,tm.created_at AS last_message_at FROM companies c JOIN thread_messages tm ON tm.id=(SELECT id FROM thread_messages WHERE company_id=c.id ORDER BY id DESC LIMIT 1) WHERE c.thread_state<>'inactive' ORDER BY tm.created_at DESC,tm.id DESC"
    ))
    return [_thread_summary(row) for row in result]


@router.get("/threads/{company_id}", response_model=ThreadDetail)
async def get_thread(company_id: int, request: Request, user: dict[str, Any] = Depends(current_user)):
    found = rows(await _db(request).query(
        "SELECT c.id AS company_id,c.domain,c.contact_email,c.thread_state,tm.body AS last_message_preview,tm.sender_type AS last_message_sender,tm.created_at AS last_message_at FROM companies c LEFT JOIN thread_messages tm ON tm.id=(SELECT id FROM thread_messages WHERE company_id=c.id ORDER BY id DESC LIMIT 1) WHERE c.id=?",
        [company_id],
    ))
    if not found:
        raise HTTPException(status_code=404, detail="Thread not found")
    messages = rows(await _db(request).query("SELECT * FROM thread_messages WHERE company_id=? ORDER BY id", [company_id]))
    row = found[0]
    summary = _thread_summary(row)
    return ThreadDetail(summary=summary, messages=[_message(message) for message in messages])


@router.post("/threads/{company_id}/takeover", response_model=ThreadSummary)
async def takeover_thread(company_id: int, request: Request, user: dict[str, Any] = Depends(current_user)):
    found = rows(await _db(request).query("SELECT id,thread_state FROM companies WHERE id=?", [company_id]))
    if not found:
        raise HTTPException(status_code=404, detail="Thread not found")
    if found[0]["thread_state"] == "closed":
        raise HTTPException(status_code=409, detail="Thread is closed")
    await _db(request).query("UPDATE companies SET thread_state='human_taken_over',updated_at=CURRENT_TIMESTAMP WHERE id=?", [company_id])
    detail = await get_thread(company_id, request, user)
    return detail.summary


@router.post("/threads/{company_id}/messages", response_model=ThreadMessage)
async def send_human_reply(company_id: int, body: HumanReplyRequest, request: Request, user: dict[str, Any] = Depends(current_user)):
    found = rows(await _db(request).query("SELECT id,thread_state,do_not_contact FROM companies WHERE id=?", [company_id]))
    if not found:
        raise HTTPException(status_code=404, detail="Thread not found")
    company = found[0]
    if company["thread_state"] != "human_taken_over" or _bool(company["do_not_contact"]):
        raise HTTPException(status_code=409, detail="Thread not taken over, or do_not_contact is set")
    created = await _db(request).batch([
        {"sql": "INSERT INTO thread_messages(company_id,sender_type,body,status) VALUES (?,'human',?,'approved')", "params": [company_id, body.body]},
        {"sql": "INSERT INTO module_2_queue(type,company_id,message_id,state) VALUES ('send',?,last_insert_rowid(),'pending')", "params": [company_id]},
        {"sql": "SELECT * FROM thread_messages WHERE id=last_insert_rowid()"},
    ])
    message_rows = rows(created[2])
    if not message_rows:
        raise HTTPException(status_code=422, detail="Could not queue human reply")
    message = message_rows[0]
    orchestrator = request.app.state.orchestrator
    waiter = orchestrator.register_message_waiter(int(message["id"]))
    try:
        final_status = await waiter
    finally:
        orchestrator.release_message_waiter(int(message["id"]), waiter)
    message["status"] = final_status
    message["updated_at"] = _now()
    return _message(message)


@router.get("/bookings", response_model=list[Booking])
async def list_bookings(request: Request, from_: str = Query(alias="from"), to: str = Query(), user: dict[str, Any] = Depends(current_user)):
    try:
        start = datetime.fromisoformat(from_.replace("Z", "+00:00"))
        end = datetime.fromisoformat(to.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=422, detail="from and to must be ISO date-time strings")
    if end <= start:
        raise HTTPException(status_code=422, detail="to must be later than from")
    result = rows(await _db(request).query(
        "SELECT b.*,c.domain FROM bookings b JOIN companies c ON c.id=b.company_id WHERE b.scheduled_at>=? AND b.scheduled_at<=? ORDER BY b.scheduled_at",
        [from_, to],
    ))
    return [Booking(
        id=int(r["id"]), company_id=int(r["company_id"]), domain=r["domain"],
        cal_booking_uid=r["cal_booking_uid"], scheduled_at=_iso(r["scheduled_at"]),
        status=r["status"], source=r["source"], created_at=_iso(r["created_at"]), updated_at=_iso(r["updated_at"]),
    ) for r in result]


@router.get("/notifications", response_model=list[Notification])
async def list_notifications(request: Request, user: dict[str, Any] = Depends(current_user)):
    result = rows(await _db(request).query(
        "SELECT n.*,c.domain FROM notifications n JOIN companies c ON c.id=n.company_id ORDER BY n.created_at DESC,n.id DESC LIMIT 50"
    ))
    return [Notification(
        id=int(r["id"]), company_id=int(r["company_id"]), domain=r["domain"], reason=r["reason"],
        body=r.get("body"), read=_bool(r.get("read", 0)), created_at=_iso(r["created_at"]),
    ) for r in result]


@router.post("/notifications/read", response_model=OkResponse)
async def mark_notifications_read(body: MarkReadRequest, request: Request, user: dict[str, Any] = Depends(current_user)):
    placeholders = ",".join("?" for _ in body.ids)
    await _db(request).query(f"UPDATE notifications SET read=1 WHERE id IN ({placeholders})", body.ids)
    return OkResponse(ok=True)


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(request: Request, user: dict[str, Any] = Depends(current_user)):
    db = _db(request)
    sql = [
        "SELECT COUNT(*) AS total FROM companies WHERE status IN ('approved','human_approved')",
        "SELECT COUNT(*) AS total FROM companies WHERE status='pending'",
        "SELECT COUNT(*) AS total FROM companies WHERE status='needs_human_review'",
        "SELECT COUNT(*) AS total FROM thread_messages WHERE sender_type='agent' AND status='pending_review'",
        "SELECT COUNT(*) AS total FROM companies WHERE email_status='sent'",
        "SELECT COUNT(*) AS total FROM companies WHERE email_status='rejected_by_human'",
        "SELECT COUNT(*) AS total FROM companies WHERE thread_state='auto'",
        "SELECT COUNT(*) AS total FROM companies WHERE thread_state='needs_human'",
        "SELECT COUNT(*) AS total FROM companies WHERE thread_state='human_taken_over'",
        "SELECT COUNT(*) AS total FROM bookings WHERE scheduled_at>=datetime('now') AND status='booked'",
        "SELECT COUNT(*) AS total FROM notifications WHERE read=0",
    ]
    results = await db.batch([{"sql": statement} for statement in sql])
    counts = [int(rows(result)[0]["total"]) if rows(result) else 0 for result in results]
    return DashboardSummary(
        research={"approved": counts[0], "pending": counts[1], "needs_human_review": counts[2]},
        emails={"pending_review": counts[3], "sent": counts[4], "rejected": counts[5]},
        conversations={"auto": counts[6], "needs_human": counts[7], "human_taken_over": counts[8]},
        bookings={"upcoming": counts[9]},
        notifications={"unread": counts[10]},
    )


@router.post("/webhooks/resend/inbound")
async def inbound_email_webhook(request: Request, x_webhook_signature: str | None = Header(default=None)):
    raw = await request.body()
    if not verify_hmac_signature(raw, x_webhook_signature or "", _settings(request).resend_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid webhook JSON")
    data = payload.get("data", payload)
    sender = parseaddr(str(data.get("from") or data.get("sender") or ""))[1].lower()
    reply_to = parseaddr(str(data.get("reply_to") or data.get("replyTo") or ""))[1].lower()
    text = str(data.get("text") or data.get("text_body") or data.get("html") or "")
    target = reply_to or sender
    found = rows(await _db(request).query("SELECT id FROM companies WHERE lower(contact_email)=?", [target]))
    if not found:
        return {"ok": True}
    company_id = int(found[0]["id"])
    await _db(request).batch([
        {"sql": "INSERT INTO thread_messages(company_id,sender_type,body,status) VALUES (?,'prospect',?,'received')", "params": [company_id, text]},
        {"sql": "UPDATE companies SET thread_state=CASE WHEN thread_state='inactive' THEN 'auto' ELSE thread_state END,updated_at=CURRENT_TIMESTAMP WHERE id=?", "params": [company_id]},
        {"sql": "INSERT INTO module_2_queue(type,company_id,message_id,state) VALUES ('reply',?,last_insert_rowid(),'pending')", "params": [company_id]},
    ])
    return {"ok": True}


@router.post("/webhooks/calcom")
async def calcom_webhook(request: Request, x_cal_signature_256: str | None = Header(default=None)):
    raw = await request.body()
    if not verify_hmac_signature(raw, x_cal_signature_256 or "", _settings(request).calcom_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid webhook JSON")
    event = str(payload.get("triggerEvent") or payload.get("type") or "")
    data = payload.get("payload", payload.get("data", {})) or {}
    uid = str(data.get("uid") or data.get("bookingUid") or "")
    start = str(data.get("startTime") or data.get("start") or "")
    attendee = data.get("attendees", [{}])
    attendee_email = str((attendee[0] if attendee else {}).get("email") or data.get("email") or "").lower()
    if not uid:
        return {"ok": True}
    company = rows(await _db(request).query("SELECT id FROM companies WHERE lower(contact_email)=?", [attendee_email])) if attendee_email else []
    if not company:
        return {"ok": True}
    company_id = int(company[0]["id"])
    if event == "BOOKING_CREATED":
        await _db(request).query(
            "INSERT INTO bookings(company_id,cal_booking_uid,scheduled_at,status,source) VALUES (?,?,?,'booked','prospect_link') ON CONFLICT(cal_booking_uid) DO NOTHING",
            [company_id, uid, start],
        )
    elif event == "BOOKING_CANCELLED":
        await _db(request).query("UPDATE bookings SET status='cancelled',updated_at=CURRENT_TIMESTAMP WHERE cal_booking_uid=?", [uid])
    elif event == "BOOKING_RESCHEDULED":
        await _db(request).query("UPDATE bookings SET scheduled_at=?,status='rescheduled',updated_at=CURRENT_TIMESTAMP WHERE cal_booking_uid=?", [start, uid])
    return {"ok": True}
