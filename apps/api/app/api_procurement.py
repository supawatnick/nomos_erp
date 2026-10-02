from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.api_master import trusted_context
from app.application.procurement import (
    ProcurementError,
    award_rfq,
    create_purchase_request,
    create_rfq,
    record_supplier_quote,
    send_rfq,
    transition_purchase_request,
)
from app.core.config import get_settings
from app.domain.security import require_permission

router = APIRouter(prefix="/api/v1/procurement", tags=["procurement"])


class PRLineIn(BaseModel):
    product_id: UUID
    unit_id: UUID
    quantity: Decimal = Field(gt=0)
    note: str | None = None


class PRIn(BaseModel):
    request_number: str = Field(min_length=1, max_length=80)
    needed_by: date | None = None
    reason: str | None = None
    lines: list[PRLineIn] = Field(min_length=1)


class RFQIn(BaseModel):
    rfq_number: str = Field(min_length=1, max_length=80)
    purchase_request_id: UUID | None = None
    supplier_ids: list[UUID] = Field(min_length=1)
    currency_code: str = Field(default="THB", min_length=3, max_length=3)
    response_due_date: date | None = None


class QuoteIn(BaseModel):
    quoted_total: Decimal = Field(ge=0)
    note: str | None = None


def _ctx(request: Request, authorization: str | None, tenant: str | None):
    return trusted_context(request, authorization, tenant)


def _engine():
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def _serialize(rows):
    out = []
    for row in rows:
        item = dict(row)
        for key, value in list(item.items()):
            if isinstance(value, UUID):
                item[key] = str(value)
            elif isinstance(value, Decimal):
                item[key] = format(value, "f")
            elif hasattr(value, "isoformat") and value is not None:
                item[key] = value.isoformat()
        out.append(item)
    return out


@router.get("/requests")
def requests(request: Request, authorization: str | None = Header(default=None),
             x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    require_permission(context, "procurement.read")
    with _engine().connect() as db:
        rows = db.execute(text("""SELECT id,request_number,status,requested_by_tenant_user_id,needed_by,reason,version,updated_at
            FROM purchase_requests WHERE tenant_id=:t ORDER BY updated_at DESC"""), {"t": context.tenant_id}).mappings().all()
    return {"data": _serialize(rows), "meta": {"request_id": str(context.request_id)}}


@router.post("/requests", status_code=201)
def request_create(payload: PRIn, request: Request, authorization: str | None = Header(default=None),
                   x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            rid = create_purchase_request(db, context=context, request_number=payload.request_number,
                needed_by=payload.needed_by, reason=payload.reason,
                lines=[line.model_dump() for line in payload.lines])
    except IntegrityError as exc:
        raise HTTPException(409, detail={"code": "DUPLICATE_RESOURCE"}) from exc
    except ProcurementError as exc:
        raise HTTPException(422, detail={"code": "VALIDATION_FAILED", "message": str(exc)}) from exc
    return {"data": {"id": str(rid)}, "meta": {"request_id": str(context.request_id)}}


@router.post("/requests/{request_id}/transition/{new_status}")
def request_transition(request_id: UUID, new_status: str, request: Request,
                       authorization: str | None = Header(default=None),
                       x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            transition_purchase_request(db, context=context, request_id=request_id, status=new_status.upper())
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_DOCUMENT_STATE", "message": str(exc)}) from exc
    return {"data": {"id": str(request_id), "status": new_status.upper()}}


@router.get("/rfqs")
def rfqs(request: Request, authorization: str | None = Header(default=None),
         x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    require_permission(context, "procurement.read")
    with _engine().connect() as db:
        rows = db.execute(text("""SELECT id,rfq_number,purchase_request_id,status,currency_code,response_due_date,
            awarded_supplier_id,version,updated_at FROM procurement_rfqs WHERE tenant_id=:t ORDER BY updated_at DESC"""),
            {"t": context.tenant_id}).mappings().all()
    return {"data": _serialize(rows), "meta": {"request_id": str(context.request_id)}}


@router.post("/rfqs", status_code=201)
def rfq_create(payload: RFQIn, request: Request, authorization: str | None = Header(default=None),
               x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            rid = create_rfq(db, context=context, **payload.model_dump())
    except (ProcurementError, IntegrityError) as exc:
        raise HTTPException(409, detail={"code": "VALIDATION_FAILED", "message": str(exc)}) from exc
    return {"data": {"id": str(rid)}, "meta": {"request_id": str(context.request_id)}}


@router.post("/rfqs/{rfq_id}/send")
def rfq_send(rfq_id: UUID, request: Request, authorization: str | None = Header(default=None),
             x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            send_rfq(db, context=context, rfq_id=rfq_id)
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_DOCUMENT_STATE", "message": str(exc)}) from exc
    return {"data": {"id": str(rfq_id), "status": "SENT"}}


@router.post("/rfqs/{rfq_id}/suppliers/{supplier_id}/quote")
def quote_record(rfq_id: UUID, supplier_id: UUID, payload: QuoteIn, request: Request,
                 authorization: str | None = Header(default=None),
                 x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            record_supplier_quote(db, context=context, rfq_id=rfq_id, supplier_id=supplier_id,
                                  quoted_total=payload.quoted_total, note=payload.note)
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_DOCUMENT_STATE", "message": str(exc)}) from exc
    return {"data": {"rfq_id": str(rfq_id), "supplier_id": str(supplier_id), "status": "RESPONDED"}}


@router.post("/rfqs/{rfq_id}/award/{supplier_id}")
def rfq_award(rfq_id: UUID, supplier_id: UUID, request: Request,
              authorization: str | None = Header(default=None),
              x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            award_rfq(db, context=context, rfq_id=rfq_id, supplier_id=supplier_id)
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_DOCUMENT_STATE", "message": str(exc)}) from exc
    return {"data": {"id": str(rfq_id), "status": "AWARDED", "supplier_id": str(supplier_id)}}
