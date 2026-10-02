from collections.abc import Awaitable, Callable
from uuid import UUID, uuid4

import structlog
from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.api_admin import router as admin_router
from app.api_approvals import router as approvals_router
from app.api_reports import router as reports_router
from app.api_crm import router as crm_router
from app.api_imports import router as imports_router
from app.api_inventory import router as inventory_router
from app.api_inventory_operations import router as inventory_operations_router
from app.api_master import router as master_router
from app.api_procurement import router as procurement_router
from app.api_sales import router as sales_router
from app.application.auth import create_session, resolve_session, revoke_session
from app.core.config import get_settings
from app.core.database import database_ready

settings = get_settings()
structlog.configure(
    processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()]
)
log = structlog.get_logger()
app = FastAPI(title=settings.app_name, version="0.11.0")
app.include_router(admin_router)
app.include_router(approvals_router)
app.include_router(reports_router)
app.include_router(master_router)
app.include_router(imports_router)
app.include_router(inventory_router)
app.include_router(inventory_operations_router)
app.include_router(crm_router)
app.include_router(procurement_router)
app.include_router(sales_router)


class LoginRequest(BaseModel):
    email: str
    password: str
    tenant_id: UUID


@app.middleware("http")
async def request_context(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = uuid4()
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = str(request_id)
    log.info(
        "http_request",
        request_id=str(request_id),
        correlation_id=request.headers.get("X-Correlation-ID"),
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response) -> dict[str, str]:
    if not database_ready():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}
    return {"status": "ready"}


@app.get("/api/v1/auth/context")
def auth_context(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    if not authorization or not authorization.startswith("Bearer ") or not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_REQUIRED"},
        )
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_REQUIRED"},
        ) from exc
    context = resolve_session(
        authorization.removeprefix("Bearer ").strip(), tenant_id, request.state.request_id
    )
    return {
        "data": {
            "actor_user_id": str(context.actor_user_id),
            "tenant_id": str(context.tenant_id),
            "tenant_user_id": str(context.tenant_user_id),
            "permissions": sorted(context.permissions),
        },
        "meta": {"request_id": str(context.request_id)},
    }


@app.post("/api/v1/auth/login")
def login(payload: LoginRequest, request: Request) -> dict[str, object]:
    token, context = create_session(
        str(payload.email), payload.password, payload.tenant_id, request.state.request_id
    )
    return {
        "data": {
            "session_token": token,
            "tenant_id": str(context.tenant_id),
            "permissions": sorted(context.permissions),
        },
        "meta": {"request_id": str(context.request_id)},
    }


@app.post("/api/v1/auth/logout")
def logout(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    if not authorization or not authorization.startswith("Bearer ") or not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_REQUIRED"},
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_REQUIRED"},
        ) from exc
    context = resolve_session(token, tenant_id, request.state.request_id)
    revoke_session(token, context)
    return {"data": {"revoked": True}, "meta": {"request_id": str(context.request_id)}}
