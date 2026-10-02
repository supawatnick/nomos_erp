from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from app.api_master import trusted_context
from app.application.approvals import (
    ApprovalError,
    cancel_approval,
    create_policy,
    decide_approval,
)
from app.core.config import get_settings
from app.domain.security import require_permission

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


class PolicyIn(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    request_type: str = Field(min_length=1, max_length=80)
    required_permission: str = Field(min_length=1, max_length=120)
    steps_required: int = Field(default=1, ge=1)
    prohibit_self_approval: bool = True
    expires_after_hours: int | None = Field(default=None, ge=1)


class DecisionIn(BaseModel):
    decision: str
    reason: str | None = None


def _engine():
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def _context(request: Request, authorization: str | None, tenant: str | None):
    return trusted_context(request, authorization, tenant)


@router.get("")
def list_approvals(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    context = _context(request, authorization, x_tenant_id)
    require_permission(context, "approval.read")
    with _engine().connect() as db:
        rows = db.execute(text("""SELECT r.id,r.request_type,r.source_type,r.source_id,
            r.source_version,r.status,r.current_step,r.expires_at,r.created_at,
            p.code AS policy_code,p.name AS policy_name,p.steps_required
            FROM approval_requests r JOIN approval_policies p
              ON p.tenant_id=r.tenant_id AND p.id=r.policy_id
            WHERE r.tenant_id=:tenant ORDER BY r.created_at DESC"""),
            {"tenant": context.tenant_id}).mappings().all()
    return {"data": [
        {k: (str(v) if isinstance(v, UUID) else v.isoformat() if hasattr(v, "isoformat") else v)
         for k, v in dict(row).items()} for row in rows
    ], "meta": {"request_id": str(context.request_id)}}


@router.post("/policies", status_code=201)
def policy_create(
    payload: PolicyIn,
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    context = _context(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            policy_id = create_policy(db, context=context, **payload.model_dump())
    except ApprovalError as exc:
        raise HTTPException(422, detail={"code": "VALIDATION_FAILED", "message": str(exc)}) from exc
    return {"data": {"id": str(policy_id)}, "meta": {"request_id": str(context.request_id)}}


@router.post("/{approval_request_id}/decide")
def approval_decide(
    approval_request_id: UUID,
    payload: DecisionIn,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    context = _context(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            result = decide_approval(
                db, context=context, approval_request_id=approval_request_id,
                decision=payload.decision, idempotency_key=idempotency_key, reason=payload.reason,
            )
    except ApprovalError as exc:
        raise HTTPException(409, detail={"code": "CONFLICT", "message": str(exc)}) from exc
    return {"data": {"id": str(approval_request_id), "decision": result},
            "meta": {"request_id": str(context.request_id)}}


@router.post("/{approval_request_id}/cancel")
def approval_cancel(
    approval_request_id: UUID,
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    context = _context(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            cancel_approval(db, context=context, approval_request_id=approval_request_id)
    except ApprovalError as exc:
        raise HTTPException(409, detail={"code": "CONFLICT", "message": str(exc)}) from exc
    return {"data": {"id": str(approval_request_id), "status": "CANCELLED"},
            "meta": {"request_id": str(context.request_id)}}
