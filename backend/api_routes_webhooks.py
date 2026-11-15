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
    found = rows(await _db(request).query(
        "SELECT id FROM companies WHERE lower(contact_email)=? OR lower(contact_email)=? ORDER BY CASE WHEN lower(contact_email)=? THEN 0 ELSE 1 END LIMIT 1",
        [reply_to, sender, reply_to],
    ))
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
