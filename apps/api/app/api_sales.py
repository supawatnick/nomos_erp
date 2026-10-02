from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from app.api_master import trusted_context
from app.application.sales import (
    SalesError,
    accept_quotation,
    cancel_order,
    confirm_order,
    create_quotation,
    post_delivery,
    post_sales_return,
    release_reservations,
    reserve_order,
    revise_quotation,
    send_quotation,
)
from app.core.config import get_settings
from app.domain.security import require_permission

router=APIRouter(prefix="/api/v1/sales",tags=["sales"])


class LineIn(BaseModel):
    product_id: UUID
    unit_id: UUID
    quantity: Decimal=Field(gt=0)
    unit_price: Decimal=Field(ge=0)
    discount_amount: Decimal=Field(default=Decimal(0),ge=0)
    tax_amount: Decimal=Field(default=Decimal(0),ge=0)


class QuotationIn(BaseModel):
    legal_entity_id: UUID
    branch_id: UUID|None=None
    customer_id: UUID
    opportunity_id: UUID|None=None
    owner_tenant_user_id: UUID|None=None
    currency_code: str=Field(default="THB",min_length=3,max_length=3)
    valid_until: date|None=None
    terms: str|None=None
    period_key: str|None=None
    lines: list[LineIn]=Field(min_length=1)


class RevisionIn(BaseModel):
    valid_until: date|None=None
    terms: str|None=None
    lines: list[LineIn]=Field(min_length=1)


class AcceptIn(BaseModel):
    accepted_by: str=Field(min_length=1,max_length=240)


class MovementLine(BaseModel):
    sales_order_line_id: UUID
    quantity: Decimal=Field(gt=0)


class MovementIn(BaseModel):
    location_id: UUID
    period_key: str|None=None
    lines: list[MovementLine]=Field(min_length=1)


def _ctx(request,auth,tenant):return trusted_context(request,auth,tenant)
def _engine():return create_engine(get_settings().database_url,pool_pre_ping=True)
def _serialize(rows):
    out=[]
    for row in rows:
        item=dict(row)
        for k,v in list(item.items()):
            if isinstance(v,UUID):item[k]=str(v)
            elif isinstance(v,Decimal):item[k]=format(v,"f")
            elif hasattr(v,"isoformat"):item[k]=v.isoformat()
        out.append(item)
    return out


@router.get("/quotations")
def quotations(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id);require_permission(context,"sales.read")
    with _engine().connect() as db:
        rows=db.execute(text("""SELECT q.id,q.quotation_number,q.customer_id,q.status,q.current_revision,q.valid_until,
          r.total_amount,q.currency_code FROM sales_quotations q JOIN sales_quotation_revisions r
          ON r.tenant_id=q.tenant_id AND r.quotation_id=q.id AND r.revision=q.current_revision
          WHERE q.tenant_id=:t ORDER BY q.created_at DESC"""),{"t":context.tenant_id}).mappings().all()
    return {"data":_serialize(rows),"meta":{"request_id":str(context.request_id)}}


@router.post("/quotations",status_code=201)
def quotation_create(payload:QuotationIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db:
            qid=create_quotation(db,context=context,**payload.model_dump(exclude={"lines"}),lines=[x.model_dump() for x in payload.lines])
    except SalesError as exc:raise HTTPException(409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(qid),"status":"DRAFT"},"meta":{"request_id":str(context.request_id)}}


@router.post("/quotations/{qid}/send")
def quotation_send(qid:UUID,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db:send_quotation(db,context=context,quotation_id=qid)
    except SalesError as exc:raise HTTPException(409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(qid),"status":"SENT"}}


@router.post("/quotations/{qid}/revise")
def quotation_revise(qid:UUID,payload:RevisionIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db:revise_quotation(db,context=context,quotation_id=qid,lines=[x.model_dump() for x in payload.lines],valid_until=payload.valid_until,terms=payload.terms)
    except SalesError as exc:raise HTTPException(409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(qid),"status":"DRAFT"}}


@router.post("/quotations/{qid}/accept",status_code=201)
def quotation_accept(qid:UUID,payload:AcceptIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db:so=accept_quotation(db,context=context,quotation_id=qid,accepted_by=payload.accepted_by)
    except SalesError as exc:raise HTTPException(409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"quotation_id":str(qid),"sales_order_id":str(so),"status":"ACCEPTED"}}


@router.get("/orders")
def orders(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id);require_permission(context,"sales.read")
    with _engine().connect() as db:
        rows=db.execute(text("SELECT id,order_number,customer_id,status,currency_code,source_quotation_id,source_quotation_revision FROM sales_orders WHERE tenant_id=:t ORDER BY created_at DESC"),{"t":context.tenant_id}).mappings().all()
    return {"data":_serialize(rows),"meta":{"request_id":str(context.request_id)}}


@router.get("/orders/{order_id}/lines")
def order_lines(order_id:UUID,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id);require_permission(context,"sales.read")
    with _engine().connect() as db:
        rows=db.execute(text("""SELECT id,line_number,product_id,unit_id,ordered_quantity,reserved_quantity,
          delivered_quantity,returned_quantity,line_total FROM sales_order_lines
          WHERE tenant_id=:t AND sales_order_id=:so ORDER BY line_number"""),{"t":context.tenant_id,"so":order_id}).mappings().all()
    return {"data":_serialize(rows),"meta":{"request_id":str(context.request_id)}}


@router.post("/orders/{order_id}/confirm")
def order_confirm(order_id:UUID,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db:confirm_order(db,context=context,order_id=order_id)
    except SalesError as exc:raise HTTPException(409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(order_id),"status":"CONFIRMED"}}


@router.post("/orders/{order_id}/reserve")
def order_reserve(order_id:UUID,payload:MovementIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db:reserve_order(db,context=context,order_id=order_id,location_id=payload.location_id,lines=[x.model_dump() for x in payload.lines])
    except SalesError as exc:raise HTTPException(409,detail={"code":"INSUFFICIENT_STOCK","message":str(exc)}) from exc
    return {"data":{"id":str(order_id),"reserved":True}}


def _movement(order_id,payload,request,auth,tenant,key,kind):
    context=_ctx(request,auth,tenant)
    try:
        with _engine().begin() as db:
            fn=post_delivery if kind=="delivery" else post_sales_return
            rid=fn(db,context=context,order_id=order_id,location_id=payload.location_id,lines=[x.model_dump() for x in payload.lines],idempotency_key=key,period_key=payload.period_key)
    except SalesError as exc:raise HTTPException(409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(rid),"status":"POSTED"}}


@router.post("/orders/{order_id}/deliveries",status_code=201)
def delivery(order_id:UUID,payload:MovementIn,request:Request,idempotency_key:str=Header(alias="Idempotency-Key"),authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    return _movement(order_id,payload,request,authorization,x_tenant_id,idempotency_key,"delivery")


@router.post("/orders/{order_id}/returns",status_code=201)
def sales_return(order_id:UUID,payload:MovementIn,request:Request,idempotency_key:str=Header(alias="Idempotency-Key"),authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    return _movement(order_id,payload,request,authorization,x_tenant_id,idempotency_key,"return")


@router.get("/orders/{order_id}/timeline")
def order_timeline(order_id:UUID,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id);require_permission(context,"sales.read")
    with _engine().connect() as db:
        rows=db.execute(text("""SELECT event_type,from_status,to_status,occurred_at,actor_tenant_user_id
          FROM sales_order_events WHERE tenant_id=:t AND sales_order_id=:so ORDER BY occurred_at,id"""),
          {"t":context.tenant_id,"so":order_id}).mappings().all()
    return {"data":_serialize(rows),"meta":{"request_id":str(context.request_id)}}


@router.post("/orders/{order_id}/release-reservations")
def order_release(order_id:UUID,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db:release_reservations(db,context=context,order_id=order_id)
    except SalesError as exc:raise HTTPException(409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(order_id),"released":True}}


@router.post("/orders/{order_id}/cancel")
def order_cancel(order_id:UUID,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    context=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db:cancel_order(db,context=context,order_id=order_id)
    except SalesError as exc:raise HTTPException(409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(order_id),"status":"CANCELLED"}}
