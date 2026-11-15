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
        {"sql": "INSERT INTO auth_events(user_id,event,ip,user_agent) SELECT id,'invite_sent',?,? FROM users WHERE email=? COLLATE NOCASE", "params": [_ip(request), request.headers.get("user-agent"), body.email]},
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
