# Inputs: FastAPI request headers and raw bodies, D1 rows, Resend API responses, and Cal.com webhook payloads.
# Outputs: verified webhook acknowledgements, inbound prospect messages, and queued Module 2 replies.
# Explanation: Verifies provider webhooks, retrieves full received email content, deduplicates events, and routes valid prospect replies into their company thread.
from __future__ import annotations
from __future__ import annotations

import html
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
from .integrations import is_generic_email, normalize_domain, verify_hmac_signature, verify_svix_signature
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
async def inbound_email_webhook(request: Request):
    raw = await request.body()
    headers = request.headers
    webhook_id = headers.get("svix-id") or headers.get("webhook-id")
    webhook_timestamp = headers.get("svix-timestamp") or headers.get("webhook-timestamp")
    webhook_signature = headers.get("svix-signature") or headers.get("webhook-signature")
    settings = _settings(request)
    if not verify_svix_signature(raw, webhook_id, webhook_timestamp, webhook_signature, settings.resend_webhook_secret):
        raise HTTPException(status_code=400, detail="Invalid Resend webhook signature")
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid Resend webhook JSON")
    if not isinstance(payload, dict) or payload.get("type") != "email.received":
        return {"ok": True}
    event_data = payload.get("data") or {}
    email_id = str(event_data.get("email_id") or "").strip()
    if not email_id or not webhook_id:
        raise HTTPException(status_code=400, detail="Resend inbound event is missing its identifiers")
    db = _db(request)
    existing = rows(await db.query("SELECT status,message_id FROM inbound_email_events WHERE event_id=? OR email_id=? LIMIT 1", [webhook_id, email_id]))
    if existing and existing[0].get("status") in {"processed", "ignored"}:
        return {"ok": True}
    if not existing:
        await db.query("INSERT INTO inbound_email_events(event_id,email_id,status) VALUES (?,?,'pending') ON CONFLICT DO NOTHING", [webhook_id, email_id])
    resend = getattr(request.app.state, "resend", None)
    if resend is None:
        raise HTTPException(status_code=503, detail="Resend integration is unavailable")
    try:
        received = await resend.get_received_email(email_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not retrieve the received email from Resend") from exc
    email_data = received.get("data", received)
    sender = parseaddr(str(email_data.get("from") or event_data.get("from") or ""))[1].strip().lower()
    body = str(email_data.get("text") or "").strip()
    if not body:
        body = html.unescape(re.sub(r"<[^>]+>", " ", str(email_data.get("html") or "")))
        body = re.sub(r"\s+", " ", body).strip()
    subject = str(email_data.get("subject") or event_data.get("subject") or "").strip()
    if not sender or not body:
        await db.query("UPDATE inbound_email_events SET status='ignored' WHERE email_id=?", [email_id])
        return {"ok": True}
    recipients = email_data.get("to") or event_data.get("to") or []
    received_for = email_data.get("received_for") or event_data.get("received_for") or []
    if isinstance(recipients, str): recipients = [recipients]
    if isinstance(received_for, str): received_for = [received_for]
    inbound_domain = str(settings.resend_inbound_domain or "").strip().lower().strip(".")
    company_id = None
    if inbound_domain:
        for recipient in list(recipients) + list(received_for):
            address = parseaddr(str(recipient))[1].strip().lower()
            local, separator, domain = address.partition("@")
            alias = re.fullmatch(r"reply\+(\d+)", local)
            if separator and domain == inbound_domain and alias:
                company_id = int(alias.group(1))
                break
    company = []
    if company_id is not None:
        company = rows(await db.query("SELECT id FROM companies WHERE id=? AND lower(contact_email)=? LIMIT 1", [company_id, sender]))
    if not company:
        company = rows(await db.query("SELECT id FROM companies WHERE lower(contact_email)=? ORDER BY updated_at DESC,id DESC LIMIT 1", [sender]))
    if not company:
        await db.query("UPDATE inbound_email_events SET status='ignored' WHERE email_id=?", [email_id])
        return {"ok": True}
    company_id = int(company[0]["id"])
    persisted = await db.batch([
        {"sql":"INSERT INTO thread_messages(company_id,sender_type,body,status,subject,provider_message_id) VALUES (?,'prospect',?,'received',?,?) ON CONFLICT(provider_message_id) DO NOTHING","params":[company_id,body,subject or None,email_id]},
        {"sql":"INSERT INTO module_2_queue(type,company_id,message_id,state) SELECT 'reply',?,id,'pending' FROM thread_messages WHERE provider_message_id=? AND NOT EXISTS (SELECT 1 FROM module_2_queue WHERE type='reply' AND message_id=(SELECT id FROM thread_messages WHERE provider_message_id=?))","params":[company_id,email_id,email_id]},
        {"sql":"UPDATE companies SET thread_state=CASE WHEN thread_state='inactive' THEN 'auto' ELSE thread_state END,updated_at=CURRENT_TIMESTAMP WHERE id=?","params":[company_id]},
        {"sql":"UPDATE inbound_email_events SET status='processed',company_id=?,message_id=(SELECT id FROM thread_messages WHERE provider_message_id=?),updated_at=CURRENT_TIMESTAMP WHERE email_id=?","params":[company_id,email_id,email_id]},
    ])
    if not persisted:
        raise HTTPException(status_code=502, detail="Could not persist the inbound email")
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
