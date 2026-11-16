# Inputs: authenticated FastAPI requests, D1 research-run rows, company counts, queue state, and persisted model-usage rows.
# Outputs: exact research, company, and contact API response models.
# Explanation: Serves research status from shared D1 state so every backend instance reports the same current run and totals.
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

@router.post("/research/start", response_model=ResearchRun)
async def start_research(body: StartResearchRequest, request: Request, user: dict[str, Any] = Depends(current_user)):
    result = await _db(request).query(
        "INSERT INTO research_runs(status,selection,target_approved) SELECT 'running',?,? WHERE NOT EXISTS (SELECT 1 FROM research_runs WHERE status IN ('running','paused')) RETURNING id,status,selection,target_approved,created_at",
        [body.selection, _settings(request).target_approved],
    )
    created = rows(result)
    if not created:
        raise HTTPException(status_code=409, detail="A research run is already running or paused")
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
    db = _db(request)
    results = await db.batch([
        {"sql": "SELECT id,status,selection,target_approved,created_at FROM research_runs ORDER BY id DESC LIMIT 1"},
        {"sql": "SELECT search_queue,system_status FROM module_1_queues WHERE id=1"},
        {"sql": "SELECT status,COUNT(*) AS total FROM companies WHERE run_id=(SELECT id FROM research_runs ORDER BY id DESC LIMIT 1) GROUP BY status"},
        {"sql": "SELECT COALESCE(SUM(input_tokens),0) AS input_tokens,COALESCE(SUM(output_tokens),0) AS output_tokens FROM model_usage WHERE module='research' AND run_id=(SELECT id FROM research_runs ORDER BY id DESC LIMIT 1)"},
        {"sql": "SELECT COUNT(*) AS total FROM model_usage WHERE module='research' AND operation='search' AND run_id=(SELECT id FROM research_runs ORDER BY id DESC LIMIT 1)"},
    ])
    run_rows = rows(results[0])
    if not run_rows:
        return ResearchStatus(run=None, counts={}, progress={"search_jobs": 0}, tokens={"in": 0, "out": 0}, searches=0)
    row = run_rows[0]
    run_id = int(row["id"])
    run = ResearchRun(
        id=run_id,
        status=row["status"],
        selection=row["selection"],
        target_approved=int(row["target_approved"]),
        created_at=_iso(row["created_at"]),
    )
    queue_rows = rows(results[1])
    queue = queue_rows[0] if queue_rows else {}
    system_status = _json_load(queue.get("system_status"), {}) or {}
    same_run = int(system_status.get("run_id") or 0) == run_id
    search_queue = _json_load(queue.get("search_queue"), []) or []
    counts = {str(item["status"]): int(item["total"]) for item in rows(results[2])}
    usage_rows = rows(results[3])
    usage = usage_rows[0] if usage_rows else {}
    search_rows = rows(results[4])
    searches = int(search_rows[0]["total"]) if search_rows else 0
    return ResearchStatus(
        run=run,
        counts=counts,
        progress={"search_jobs": len(search_queue) if same_run else 0},
        tokens={"in": int(usage.get("input_tokens") or 0), "out": int(usage.get("output_tokens") or 0)},
        searches=searches,
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
    usage = await _model_usage_summary(_db(request), company_id=id)
    return _company_detail(result[0], usage)

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
