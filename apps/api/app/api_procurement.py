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
    approve_purchase_order,
    award_rfq,
    create_purchase_order,
    create_purchase_request,
    create_rfq,
    post_goods_receipt,
    post_purchase_return,
    record_supplier_quote,
    send_purchase_order,
    send_rfq,
    submit_purchase_order,
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


class QuoteLineIn(BaseModel):
    rfq_line_id: UUID
    offered_quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(default=Decimal(0), ge=0)
    tax_amount: Decimal = Field(default=Decimal(0), ge=0)


class QuoteIn(BaseModel):
    quoted_total: Decimal | None = Field(default=None, ge=0)
    lines: list[QuoteLineIn] | None = None
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


def _request_command(request_id: UUID, status: str, request: Request,
                     authorization: str | None, x_tenant_id: str | None):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            transition_purchase_request(db, context=context, request_id=request_id, status=status)
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_DOCUMENT_STATE", "message": str(exc)}) from exc
    return {"data": {"id": str(request_id), "status": status}}


@router.post("/requests/{request_id}/submit")
def request_submit(request_id: UUID, request: Request, authorization: str | None = Header(default=None),
                   x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    return _request_command(request_id, "PENDING_APPROVAL", request, authorization, x_tenant_id)


@router.post("/requests/{request_id}/approve")
def request_approve(request_id: UUID, request: Request, authorization: str | None = Header(default=None),
                    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    return _request_command(request_id, "APPROVED", request, authorization, x_tenant_id)


@router.post("/requests/{request_id}/reject")
def request_reject(request_id: UUID, request: Request, authorization: str | None = Header(default=None),
                   x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    return _request_command(request_id, "REJECTED", request, authorization, x_tenant_id)


@router.post("/requests/{request_id}/cancel")
def request_cancel(request_id: UUID, request: Request, authorization: str | None = Header(default=None),
                   x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    return _request_command(request_id, "CANCELLED", request, authorization, x_tenant_id)


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
                                  quoted_total=payload.quoted_total, note=payload.note,
                                  lines=[line.model_dump() for line in payload.lines] if payload.lines is not None else None)
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_DOCUMENT_STATE", "message": str(exc)}) from exc
    return {"data": {"rfq_id": str(rfq_id), "supplier_id": str(supplier_id), "status": "RESPONDED"}}


@router.get("/rfqs/{rfq_id}/comparison")
def rfq_comparison(rfq_id: UUID, request: Request, authorization: str | None = Header(default=None),
                   x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    require_permission(context, "procurement.read")
    with _engine().connect() as db:
        rows = db.execute(text("""SELECT s.supplier_id,s.status,s.quoted_total,l.rfq_line_id,
            l.offered_quantity,l.unit_price,l.discount_amount,l.tax_amount,l.line_total
            FROM procurement_rfq_suppliers s LEFT JOIN procurement_rfq_supplier_lines l
              ON l.tenant_id=s.tenant_id AND l.rfq_supplier_id=s.id
            WHERE s.tenant_id=:t AND s.rfq_id=:rfq ORDER BY s.supplier_id,l.rfq_line_id"""),
            {"t": context.tenant_id, "rfq": rfq_id}).mappings().all()
    return {"data": _serialize(rows), "meta": {"request_id": str(context.request_id)}}


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


class POLineIn(BaseModel):
    product_id: UUID
    unit_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(default=Decimal(0), ge=0)
    tax_amount: Decimal = Field(default=Decimal(0), ge=0)


class POIn(BaseModel):
    legal_entity_id: UUID
    branch_id: UUID | None = None
    supplier_id: UUID
    source_rfq_id: UUID | None = None
    currency_code: str = Field(default="THB", min_length=3, max_length=3)
    period_key: str | None = Field(default=None, min_length=1, max_length=32)
    lines: list[POLineIn] = Field(min_length=1)


@router.get("/orders")
def orders(request: Request, authorization: str | None = Header(default=None),
           x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    require_permission(context, "procurement.read")
    with _engine().connect() as db:
        rows = db.execute(text("""SELECT id,order_number,legal_entity_id,branch_id,supplier_id,source_rfq_id,
            currency_code,status,version,approved_version,approved_at,updated_at
            FROM purchase_orders WHERE tenant_id=:t ORDER BY updated_at DESC"""),
            {"t": context.tenant_id}).mappings().all()
    return {"data": _serialize(rows), "meta": {"request_id": str(context.request_id)}}


@router.post("/orders", status_code=201)
def order_create(payload: POIn, request: Request, authorization: str | None = Header(default=None),
                 x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            order_id = create_purchase_order(db, context=context, **payload.model_dump())
    except (ProcurementError, ValueError, IntegrityError) as exc:
        raise HTTPException(409, detail={"code": "VALIDATION_FAILED", "message": str(exc)}) from exc
    return {"data": {"id": str(order_id)}, "meta": {"request_id": str(context.request_id)}}


@router.post("/orders/{order_id}/submit")
def order_submit(order_id: UUID, request: Request, authorization: str | None = Header(default=None),
                 x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            submit_purchase_order(db, context=context, order_id=order_id)
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_DOCUMENT_STATE", "message": str(exc)}) from exc
    return {"data": {"id": str(order_id), "status": "PENDING_APPROVAL"}}


@router.post("/orders/{order_id}/approve")
def order_approve(order_id: UUID, request: Request, authorization: str | None = Header(default=None),
                  x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            approve_purchase_order(db, context=context, order_id=order_id)
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_DOCUMENT_STATE", "message": str(exc)}) from exc
    return {"data": {"id": str(order_id), "status": "APPROVED"}}


@router.post("/orders/{order_id}/send")
def order_send(order_id: UUID, request: Request, authorization: str | None = Header(default=None),
               x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            send_purchase_order(db, context=context, order_id=order_id)
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_DOCUMENT_STATE", "message": str(exc)}) from exc
    return {"data": {"id": str(order_id), "status": "SENT"}}


class ReceiptLineIn(BaseModel):
    purchase_order_line_id: UUID
    quantity: Decimal = Field(gt=0)


class ReceiptIn(BaseModel):
    location_id: UUID
    period_key: str | None = Field(default=None, min_length=1, max_length=32)
    lines: list[ReceiptLineIn] = Field(min_length=1)


@router.get("/orders/{order_id}/lines")
def order_lines(order_id: UUID, request: Request, authorization: str | None = Header(default=None),
                x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    require_permission(context, "procurement.read")
    with _engine().connect() as db:
        rows = db.execute(text("""SELECT id,line_number,product_id,unit_id,ordered_quantity,unit_price,
            discount_amount,tax_amount,line_total,received_quantity,returned_quantity
            FROM purchase_order_lines WHERE tenant_id=:t AND purchase_order_id=:po ORDER BY line_number"""),
            {"t": context.tenant_id, "po": order_id}).mappings().all()
    return {"data": _serialize(rows), "meta": {"request_id": str(context.request_id)}}


@router.post("/orders/{order_id}/receipts", status_code=201)
def receipt_post(order_id: UUID, payload: ReceiptIn, request: Request,
                 idempotency_key: str = Header(alias="Idempotency-Key"),
                 authorization: str | None = Header(default=None),
                 x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            receipt_id = post_goods_receipt(db, context=context, order_id=order_id,
                location_id=payload.location_id, lines=[line.model_dump() for line in payload.lines],
                idempotency_key=idempotency_key, period_key=payload.period_key)
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_RECEIPT", "message": str(exc)}) from exc
    return {"data": {"id": str(receipt_id), "status": "POSTED"},
            "meta": {"request_id": str(context.request_id)}}


@router.post("/orders/{order_id}/returns", status_code=201)
def return_post(order_id: UUID, payload: ReceiptIn, request: Request,
                idempotency_key: str = Header(alias="Idempotency-Key"),
                authorization: str | None = Header(default=None),
                x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    context = _ctx(request, authorization, x_tenant_id)
    try:
        with _engine().begin() as db:
            return_id = post_purchase_return(db, context=context, order_id=order_id,
                location_id=payload.location_id, lines=[line.model_dump() for line in payload.lines],
                idempotency_key=idempotency_key, period_key=payload.period_key)
    except ProcurementError as exc:
        raise HTTPException(409, detail={"code": "INVALID_RETURN", "message": str(exc)}) from exc
    return {"data": {"id": str(return_id), "status": "POSTED"},
            "meta": {"request_id": str(context.request_id)}}
