# Inputs: FastAPI request context, D1 rows, and the frontend API request/response contract.
# Outputs: shared request helpers, serializers, authentication helpers, and route routers.
# Explanation: Keeps backend.api.router stable while route handlers live in focused modules.
from fastapi import APIRouter
from .api_routes_auth import router as auth_router
from .api_routes_admin import router as admin_router
from .api_routes_research import router as research_router
from .api_routes_emails import router as emails_router
from .api_routes_threads import router as threads_router
from .api_routes_dashboard import router as dashboard_router
from .api_routes_webhooks import router as webhooks_router

router = APIRouter()
for route_group in (
    auth_router, admin_router, research_router, emails_router,
    threads_router, dashboard_router, webhooks_router,
):
    router.include_router(route_group)
