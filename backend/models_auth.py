# Inputs: JSON request bodies, query values, and decoded D1 rows conforming to frontend/src/shared/types.ts.
# Outputs: validated Pydantic request, response, and enum types with exact frontend field names and nullable fields.
# Explanation: Defines the backend wire contract in small domain-specific schema modules.
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models_common import WireModel


class OkResponse(WireModel):
    ok: bool = True


class ErrorBody(WireModel):
    detail: str


class AuthUser(WireModel):
    id: int
    email: str
    is_admin: bool


class UserSummary(AuthUser):
    created_at: str


class AuthEvent(WireModel):
    id: int
    user_id: int | None
    event: AuthEventType
    ip: str | None
    user_agent: str | None
    detail: str | None
    created_at: str


class LoginRequest(WireModel):
    email: str
    password: str


class LoginResponse(WireModel):
    token: str
    user: AuthUser


class ChangePasswordRequest(WireModel):
    old_password: str


class ChangePasswordConfirmRequest(WireModel):
    code: str
    new_password: str
    new_password_confirm: str


class ForgotPasswordRequest(WireModel):
    email: str


class ResetPasswordRequest(WireModel):
    email: str
    code: str
    new_password: str
    new_password_confirm: str


class AcceptInviteRequest(ResetPasswordRequest):
    pass


class InviteRequest(WireModel):
    email: str


class AuthEventsQuery(WireModel):
    limit: int = Field(default=50, ge=1, le=500)
