# Inputs: JSON request bodies, query values, decoded D1 rows, and aggregated model-usage summaries.
# Outputs: validated research, company, and contact request/response types matching the frontend wire contract.
# Explanation: Defines research and company schemas, including per-company AI usage totals.
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models_common import WireModel, CompanyStatus, ContactRole, ContactSource, EmailStatus, ResearchRunStatus, SourceResult, ThreadState
from .models_dashboard import ModelUsageSummary


class ResearchRun(WireModel):
    id: int
    status: ResearchRunStatus
    selection: str
    target_approved: int
    created_at: str


class ResearchStatus(WireModel):
    run: ResearchRun | None
    counts: dict[str, int]
    progress: dict[str, int]
    tokens: dict[str, int]
    searches: int


class StartResearchRequest(WireModel):
    selection: str = Field(min_length=1, max_length=4000)


class ReviewCompanyRequest(WireModel):
    company_id: int
    decision: str

    @field_validator("decision")
    @classmethod
    def valid_decision(cls, value: str) -> str:
        if value not in {"human_approved", "human_rejected"}:
            raise ValueError("decision must be human_approved or human_rejected")
        return value


class Reason(WireModel):
    text: str
    source_url: str
    quote: str


class SourceCheck(WireModel):
    url: str
    result: SourceResult
    status: int | None


class DomainCheck(WireModel):
    bucket: int
    status: int | None
    redirected_to: str | None

    @field_validator("bucket")
    @classmethod
    def valid_bucket(cls, value: int) -> int:
        if value not in (1, 2, 3):
            raise ValueError("bucket must be 1, 2, or 3")
        return value


class ResearchData(WireModel):
    reasons: list[Reason]
    domain_check: DomainCheck | None = None
    sources: list[SourceCheck]


class MemoryFact(WireModel):
    field: str
    value: str
    source_url: str
    quote: str


class Memory(WireModel):
    facts: list[MemoryFact]


class CompanySummary(WireModel):
    id: int
    domain: str
    score: int | None
    status: CompanyStatus
    email_status: EmailStatus
    thread_state: ThreadState
    do_not_contact: bool
    contact_email: str | None
    contact_role: ContactRole | None
    domain_check: DomainCheck | None
    reasons_preview: list[Reason]
    created_at: str
    updated_at: str


class CompanyDetail(CompanySummary):
    run_id: int
    contact_source: ContactSource | None
    research_data: ResearchData | None
    memory: Memory | None
    usage: ModelUsageSummary


class CompaniesQuery(WireModel):
    status: list[CompanyStatus] | None = None
    has_contact: bool | None = None
