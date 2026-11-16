# Inputs: authenticated FastAPI requests, D1 dashboard counts, and persisted model_usage records.
# Outputs: dashboard business counts plus all-module token and optional cost summaries.
# Explanation: Serves the dashboard API summary, including complete or explicitly unpriced AI usage totals.
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

from .api_usage import _model_usage_summary
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
        usage=await _model_usage_summary(db),
    )
