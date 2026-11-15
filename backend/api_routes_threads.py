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
    if not messages or row.get("last_message_at") is None:
        raise HTTPException(status_code=404, detail="Thread not found")
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
        {"sql": "INSERT INTO thread_messages(company_id,sender_type,body,status) VALUES (?,'human',?,'approved') RETURNING *", "params": [company_id, body.body]},
        {"sql": "INSERT INTO module_2_queue(type,company_id,message_id,state) VALUES ('send',?,last_insert_rowid(),'pending')", "params": [company_id]},
    ])
    message_rows = rows(created[0])
    if not message_rows:
        raise HTTPException(status_code=422, detail="Could not queue human reply")
    message = message_rows[0]
    orchestrator = request.app.state.orchestrator
    waiter = orchestrator.register_message_waiter(int(message["id"]))
    try:
        persisted = rows(await _db(request).query(
            "SELECT * FROM thread_messages WHERE id=?",
            [int(message["id"])],
        ))
        if persisted and persisted[0]["status"] != "approved":
            message = persisted[0]
        else:
            message["status"] = await waiter
            message["updated_at"] = _now()
    finally:
        orchestrator.release_message_waiter(int(message["id"]), waiter)
    return _message(message)
