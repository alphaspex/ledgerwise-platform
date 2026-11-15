# Inputs: plaintext passwords/codes, user claims, JWT bearer values, request IPs, and rate-class names.
# Outputs: bcrypt hashes and checks, HS256 JWT tokens, one-time codes, decoded claims, and per-IP allow/deny results.
# Explanation: Encapsulates authentication primitives and in-memory sliding-window limits without writing rate-limit state to D1.
from __future__ import annotations

import hashlib
import secrets
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

import bcrypt
import jwt

from .config import Settings


def hash_password(password: str, cost: int) -> str:
    salt = bcrypt.gensalt(rounds=cost)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), encoded_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def new_code(length: int) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def create_token(user: dict[str, Any], settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": int(user["id"]),
        "email": str(user["email"]),
        "is_admin": bool(user["is_admin"]),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.jwt_exp_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str, settings: Settings) -> dict[str, Any]:
    claims = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if not isinstance(claims.get("user_id"), int) or not isinstance(claims.get("email"), str):
        raise jwt.InvalidTokenError("Invalid claims")
    claims["is_admin"] = bool(claims.get("is_admin", False))
    return claims


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after: int


class SlidingWindowRateLimiter:
    def __init__(self, auth_limit: int = 5, global_limit: int = 60, window_seconds: int = 60):
        self.auth_limit = auth_limit
        self.global_limit = global_limit
        self.window_seconds = window_seconds
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, ip: str, rate_class: str, now: float | None = None) -> RateLimitDecision:
        current = time.monotonic() if now is None else now
        key = (ip, rate_class)
        limit = self.auth_limit if rate_class == "auth" else self.global_limit
        cutoff = current - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry = max(1, int(self.window_seconds - (current - events[0]) + 0.999))
                return RateLimitDecision(False, retry)
            events.append(current)
            return RateLimitDecision(True, 0)


AUTH_RATE_PATHS = {
    "/auth/login",
    "/auth/change-password",
    "/auth/forgot-password",
    "/auth/reset-password",
    "/auth/accept-invite",
}
