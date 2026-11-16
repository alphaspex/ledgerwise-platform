# Inputs: the backend package, installed test dependencies, and deterministic in-memory test values.
# Outputs: pytest assertions for the route contract, serializers, rate limits, contact helpers, and Apollo role mapping.
# Explanation: Guards the backend's public route shape and core pure logic without requiring live provider credentials or D1 access.
import json

from fastapi.routing import APIRoute

from backend.api import _bool, _company_detail, _company_summary
from backend.app import create_app
from backend.integrations import GENERIC_INBOX_PREFIXES, infer_contact_role, is_generic_email, normalize_domain
from backend.security import SlidingWindowRateLimiter


EXPECTED_ROUTES = {
    "POST /auth/login",
    "POST /auth/logout",
    "POST /auth/change-password",
    "POST /auth/change-password/confirm",
    "POST /auth/forgot-password",
    "POST /auth/reset-password",
    "POST /auth/accept-invite",
    "GET /auth/events",
    "GET /admin/users",
    "POST /admin/users/invite",
    "DELETE /admin/users/{id}",
    "POST /research/start",
    "POST /research/pause",
    "POST /research/resume",
    "GET /research/status",
    "GET /companies",
    "GET /companies/{id}",
    "POST /research/review",
    "PUT /companies/{id}/contact",
    "GET /emails/drafts",
    "POST /emails/{message_id}/review",
    "GET /threads",
    "GET /threads/{company_id}",
    "POST /threads/{company_id}/takeover",
    "POST /threads/{company_id}/messages",
    "GET /bookings",
    "GET /notifications",
    "POST /notifications/read",
    "GET /dashboard",
}

EXPECTED_WEBHOOKS = {
    "POST /webhooks/resend/inbound",
    "POST /webhooks/calcom",
}


def route_inventory() -> set[str]:
    return {
        f"{method} {route.path}"
        for route in create_app().routes
        if isinstance(route, APIRoute)
        for method in route.methods
        if method in {"GET", "POST", "PUT", "DELETE"}
    }


def base_company_row() -> dict:
    return {
        "id": 7,
        "run_id": 2,
        "domain": "example.com",
        "score": 8,
        "status": "approved",
        "email_status": "not_started",
        "thread_state": "inactive",
        "do_not_contact": 1,
        "contact_email": None,
        "contact_role": None,
        "contact_source": None,
        "research_data": json.dumps({
            "reasons": [{"text": "Evidence", "source_url": "https://example.com", "quote": "Verbatim"}],
            "domain_check": {"bucket": 3, "status": 200, "redirected_to": None},
            "sources": [{"url": "https://example.com", "result": "live", "status": 200}],
        }),
        "memory": json.dumps({
            "facts": [{"field": "name", "value": "Example", "source_url": "https://example.com", "quote": "Example"}],
            "audit": {"extract": {"raw": "private audit"}},
        }),
        "created_at": "2026-11-15 10:00:00",
        "updated_at": "2026-11-15 10:01:00",
    }


def test_frontend_api_route_contract_is_exact() -> None:
    inventory = route_inventory()
    assert inventory == EXPECTED_ROUTES | EXPECTED_WEBHOOKS


def test_d1_flags_serialize_as_json_booleans() -> None:
    assert _bool(1) is True
    assert _bool(0) is False
    summary = _company_summary(base_company_row())
    assert summary.do_not_contact is True
    assert isinstance(summary.model_dump()["do_not_contact"], bool)


def test_memory_audit_is_not_exposed_in_company_detail() -> None:
    detail = _company_detail(base_company_row())
    assert detail.memory is not None
    assert set(detail.memory.model_dump().keys()) == {"facts"}


def test_rate_limit_sliding_window_and_retry_after() -> None:
    limiter = SlidingWindowRateLimiter(auth_limit=5, global_limit=60, window_seconds=60)
    for _ in range(5):
        assert limiter.check("192.0.2.1", "auth", now=100.0).allowed
    denied = limiter.check("192.0.2.1", "auth", now=101.0)
    assert denied.allowed is False
    assert denied.retry_after > 0
    assert limiter.check("192.0.2.1", "auth", now=160.0).allowed


def test_domain_normalization_and_generic_inboxes() -> None:
    assert normalize_domain("https://WWW.Example.com:443/about?q=1") == "example.com"
    assert normalize_domain("www.example.com/path") == "example.com"
    assert is_generic_email("info@example.com") is True
    assert is_generic_email("hello+sales@example.com") is True
    assert is_generic_email("founder@example.com") is False
    assert "contact" in GENERIC_INBOX_PREFIXES


def test_apollo_role_title_mapping() -> None:
    assert infer_contact_role("Co-Founder and CEO") == "founder"
    assert infer_contact_role("Chief Operating Officer") == "coo"
    assert infer_contact_role("Controller") == "finance"
    assert infer_contact_role("Operations Manager") == "unknown"


def test_pydantic_model_references_are_resolved() -> None:
    from backend.models import AuthEvent, CompanySummary, EmailDraft

    for model in (AuthEvent, CompanySummary, EmailDraft):
        assert model.model_rebuild(force=True) is not False


def test_resend_svix_signature_verification() -> None:
    import base64
    import hashlib
    import hmac
    import time

    from backend.integrations import verify_svix_signature

    key = b"ledgerwise-test-webhook-key"
    secret = "whsec_" + base64.b64encode(key).decode("ascii").rstrip("=")
    body = b'{"type":"email.received","data":{"email_id":"mail_123"}}'
    message_id = "msg_test_123"
    timestamp = str(int(time.time()))
    signed = message_id.encode() + b"." + timestamp.encode() + b"." + body
    signature = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode("ascii")

    assert verify_svix_signature(body, message_id, timestamp, "v1," + signature, secret)
    assert not verify_svix_signature(body + b" ", message_id, timestamp, "v1," + signature, secret)
    assert not verify_svix_signature(body, message_id, str(int(time.time()) - 600), "v1," + signature, secret)


def test_research_status_uses_shared_d1_state() -> None:
    from pathlib import Path

    source_path = Path(__file__).resolve().parents[1] / "api_routes_research.py"
    source = source_path.read_text(encoding="utf-8")
    route = source.split('@router.get("/research/status"', 1)[1].split('@router.get("/companies"', 1)[0]

    assert "request.app.state.orchestrator.snapshot" not in route
    assert "FROM research_runs ORDER BY id DESC LIMIT 1" in route
    assert "FROM model_usage WHERE module='research'" in route
    assert "FROM companies WHERE run_id=" in route
