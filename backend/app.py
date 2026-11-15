# Inputs: typed settings, FastAPI route handlers, optional D1 credentials, and integration environment variables.
# Outputs: the ASGI FastAPI application with startup seeding, D1 migrations, sliding-window rate limits, and orchestrator lifecycle.
# Explanation: Builds the application process and owns startup/shutdown resources; API route business logic remains in api.py.
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import router
from .config import get_settings
from .db import D1Client
from .integrations import ApolloClient, CalComClient, MuseClient, ResendClient
from .orchestrator import Orchestrator
from .security import SlidingWindowRateLimiter, hash_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.db = None
    app.state.resend = None
    app.state.orchestrator = None
    app.state.muse = None
    app.state.apollo = None
    app.state.calcom = None

    has_d1 = bool(settings.cloudflare_account_id and settings.cloudflare_database_id and settings.cloudflare_api_token)
    if settings.app_env.lower() == "production":
        settings.validate_runtime()
    if has_d1:
        db = D1Client(settings)
        await db.open()
        migration = Path(__file__).parent / "migrations" / "0001_init.sql"
        await db.query(migration.read_text(encoding="utf-8"))
        if settings.seed_admin_email and settings.seed_admin_password:
            await db.query(
                "INSERT OR IGNORE INTO users(email,password_hash,is_admin) VALUES (?,?,1)",
                [settings.seed_admin_email.strip().lower(), hash_password(settings.seed_admin_password, settings.bcrypt_cost)],
            )
        muse = MuseClient(settings)
        resend = ResendClient(settings)
        apollo = ApolloClient(settings)
        calcom = CalComClient(settings)
        orchestrator = Orchestrator(db, settings, muse, resend, apollo, calcom)
        app.state.db = db
        app.state.muse = muse
        app.state.resend = resend
        app.state.apollo = apollo
        app.state.calcom = calcom
        app.state.orchestrator = orchestrator
        task = asyncio.create_task(orchestrator.run_forever(), name="ledgerwise-orchestrator")
        app.state.orchestrator_task = task
    else:
        app.state.db = D1Client(settings)
        app.state.resend = ResendClient(settings)
        app.state.muse = MuseClient(settings)
        app.state.apollo = ApolloClient(settings)
        app.state.calcom = CalComClient(settings)
        app.state.orchestrator_task = None

    try:
        yield
    finally:
        task = getattr(app.state, "orchestrator_task", None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        for client_name in ("muse", "resend", "apollo", "calcom"):
            client = getattr(app.state, client_name, None)
            if client:
                await client.close()
        db = getattr(app.state, "db", None)
        if db:
            await db.close()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Ledgerwise Platform API",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.rate_limiter = SlidingWindowRateLimiter(
        auth_limit=settings.rate_auth_limit,
        global_limit=settings.rate_global_limit,
        window_seconds=settings.rate_window_seconds,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=bool(settings.cors_origins),
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Webhook-Signature", "X-Cal-Signature-256"],
    )

    @application.middleware("http")
    async def rate_limit(request, call_next):
        auth_paths = {
            "/auth/login", "/auth/change-password", "/auth/forgot-password",
            "/auth/reset-password", "/auth/accept-invite",
        }
        rate_class = "auth" if request.url.path in auth_paths else "global"
        client_ip = request.client.host if request.client else "unknown"
        decision = application.state.rate_limiter.check(client_ip, rate_class)
        if not decision.allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(decision.retry_after)},
            )
        return await call_next(request)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request, exc: RequestValidationError):
        details = "; ".join(str(error.get("msg", "Invalid request")) for error in exc.errors())
        return JSONResponse(status_code=422, content={"detail": details or "Validation error"})

    @application.exception_handler(HTTPException)
    async def http_error_handler(request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=exc.headers)

    application.include_router(router)
    return application


from .security import SlidingWindowRateLimiter

app = create_app()
