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
