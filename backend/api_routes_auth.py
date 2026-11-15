# Inputs: FastAPI request context, D1 rows, and the frontend API request/response contract.
# Outputs: shared request helpers, serializers, authentication helpers, and route routers.
# Explanation: Keeps backend.api.router stable while route handlers live in focused modules.
from __future__ import annotations
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
from .api_common import *
from .api_serializers import *
from .api_auth_helpers import *

router = APIRouter()

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
        try:
            await _send_code(request, str(found[0]["email"]), int(found[0]["id"]), "reset", code, _settings(request).code_exp_seconds)
        except Exception:
            # Keep the response identical for unknown accounts and provider failures.
            pass
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
