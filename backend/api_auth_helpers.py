# Inputs: FastAPI request context, D1 rows, and the frontend API request/response contract.
# Outputs: shared request helpers, serializers, authentication helpers, and route routers.
# Explanation: Keeps backend.api.router stable while route handlers live in focused modules.
from __future__ import annotations

__all__ = [
    "current_user", "admin_user", "_event", "_send_code",
    "_get_code_user", "_check_code", "_validate_password", "_new_user_hash",
]
import json
import secrets
from datetime import datetime, timezone
from fastapi import Depends, Header, HTTPException, Request
import jwt
from .config import Settings
from .db import rows
from .api_common import _db, _settings, _ip
from .security import decode_token, hash_code, hash_password, new_code, verify_password

async def current_user(request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token")
    token = authorization[7:].strip()
    try:
        return decode_token(token, _settings(request))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token")

async def admin_user(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    if not bool(user.get("is_admin")):
        raise HTTPException(status_code=403, detail="Admin only")
    return user

async def _event(request: Request, user_id: int | None, event: str, detail: str | None = None) -> None:
    await _db(request).query(
        "INSERT INTO auth_events(user_id,event,ip,user_agent,detail) VALUES (?,?,?,?,?)",
        [user_id, event, _ip(request), request.headers.get("user-agent"), detail],
    )

async def _send_code(request: Request, email: str, user_id: int, purpose: str, code: str, expires_seconds: int) -> None:
    await _db(request).query(
        "INSERT INTO password_codes(user_id,code_hash,purpose,attempts,expires_at) VALUES (?,?,?,?,datetime('now',?))",
        [user_id, hash_code(code), purpose, 0, f"+{expires_seconds} seconds"],
    )
    purpose_label = {"change": "password change", "reset": "password reset", "invite": "invitation"}.get(purpose, purpose)
    text = f"Your Ledgerwise {purpose_label} code is {code}. It expires in {max(1, expires_seconds // 60)} minutes."
    await request.app.state.resend.send(
        to=email,
        subject=f"Your Ledgerwise {purpose_label} code",
        text=text,
        idempotency_key=f"ledgerwise-code-{user_id}-{purpose}-{hash_code(code)[:16]}",
    )

async def _get_code_user(request: Request, email: str, purpose: str) -> tuple[dict[str, Any], dict[str, Any]]:
    user_rows = rows(await _db(request).query("SELECT * FROM users WHERE email=? COLLATE NOCASE", [email]))
    if not user_rows:
        raise HTTPException(status_code=410, detail="Code expired or invalid")
    user = user_rows[0]
    code_rows = rows(await _db(request).query(
        "SELECT * FROM password_codes WHERE user_id=? AND purpose=? ORDER BY id DESC LIMIT 1",
        [int(user["id"]), purpose],
    ))
    if not code_rows:
        raise HTTPException(status_code=410, detail="Code expired or invalid")
    return user, code_rows[0]

async def _check_code(request: Request, user_id: int, code_row: dict[str, Any], code: str) -> None:
    expiry = str(code_row["expires_at"])
    try:
        expires_at = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        expired = expires_at <= datetime.now(timezone.utc)
    except ValueError:
        expired = True
    if expired or int(code_row.get("attempts", 0)) >= _settings(request).code_max_attempts:
        await _db(request).query("DELETE FROM password_codes WHERE id=?", [int(code_row["id"])])
        raise HTTPException(status_code=410, detail="Code expired or invalidated")
    if not secrets.compare_digest(hash_code(code), str(code_row["code_hash"])):
        attempts = int(code_row.get("attempts", 0)) + 1
        await _db(request).query(
            "UPDATE password_codes SET attempts=? WHERE id=?",
            [attempts, int(code_row["id"])],
        )
        if attempts >= _settings(request).code_max_attempts:
            await _db(request).query("DELETE FROM password_codes WHERE id=?", [int(code_row["id"])])
            raise HTTPException(status_code=410, detail="Code expired or invalidated")
        raise HTTPException(status_code=400, detail="Wrong code")

def _validate_password(password: str, confirm: str, settings: Settings) -> None:
    if password != confirm:
        raise HTTPException(status_code=422, detail="new_password_confirm must match new_password")
    if len(password) < settings.password_min_len:
        raise HTTPException(status_code=422, detail=f"Password must contain at least {settings.password_min_len} characters")

def _new_user_hash(settings: Settings) -> str:
    return hash_password(secrets.token_urlsafe(32), settings.bcrypt_cost)
