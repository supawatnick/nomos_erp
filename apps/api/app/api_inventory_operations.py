from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from app.application.auth import resolve_session
from app.application.inventory_operations import (
    InventoryOperationsError,
    create_stock_count,
    post_stock_count,
    record_count,
    reorder_status,
    upsert_reorder_policy,
)
from app.core.config import get_settings
from app.domain.security import RequestContext, require_permission

router=APIRouter(prefix="/api/v1/inventory/operations",tags=["inventory-operations"])


def _context(request:Request,authorization:str|None,tenant:str|None)->RequestContext:
    if not authorization or not authorization.startswith("Bearer ") or not tenant:
        raise HTTPException(status_code=401,detail={"code":"AUTHENTICATION_REQUIRED"})
    try:return resolve_session(authorization.removeprefix("Bearer ").strip(),UUID(tenant),request.state.request_id)
    except (ValueError,TypeError) as exc:raise HTTPException(status_code=401,detail={"code":"AUTHENTICATION_REQUIRED"}) from exc


class CountCreate(BaseModel):
    legal_entity_id:UUID
    warehouse_id:UUID
    count_number:str
    reference:str|None=None


class CountLine(BaseModel):
    line_id:UUID
    counted_quantity:Decimal


class CountRecord(BaseModel):
    lines:list[CountLine]


class ReorderPolicy(BaseModel):
    product_id:UUID
    location_id:UUID
    reorder_point:Decimal
    target_quantity:Decimal
    is_active:bool=True


@router.post("/stock-counts",status_code=status.HTTP_201_CREATED)
def create_count(payload:CountCreate,request:Request,authorization:str|None=Header(default=None),
                 x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    try:
        with engine.begin() as db:
            count_id=create_stock_count(db,context=context,legal_entity_id=payload.legal_entity_id,
                warehouse_id=payload.warehouse_id,count_number=payload.count_number,reference=payload.reference)
    except InventoryOperationsError as exc:raise HTTPException(status_code=409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(count_id),"status":"DRAFT"},"meta":{"request_id":str(context.request_id)}}


@router.get("/stock-counts")
def counts(request:Request,authorization:str|None=Header(default=None),
           x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);require_permission(context,"inventory.read")
    engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    with engine.connect() as db:
        rows=db.execute(text("""
          SELECT sc.id,sc.count_number,sc.status,sc.reference,sc.warehouse_id,w.code warehouse_code,w.name warehouse_name,
                 sc.counted_at,sc.posted_transaction_id,sc.created_at,
                 count(scl.id) line_count,
                 count(*) FILTER (WHERE scl.counted_quantity IS NOT NULL) counted_lines,
                 COALESCE(sum(abs(COALESCE(scl.counted_quantity,scl.system_quantity)-scl.system_quantity)),0) variance_quantity
          FROM stock_counts sc JOIN warehouses w ON w.tenant_id=sc.tenant_id AND w.id=sc.warehouse_id
          LEFT JOIN stock_count_lines scl ON scl.tenant_id=sc.tenant_id AND scl.stock_count_id=sc.id
          WHERE sc.tenant_id=:tenant GROUP BY sc.id,w.code,w.name ORDER BY sc.created_at DESC
        """),{"tenant":context.tenant_id}).mappings().all()
    data=[] 
    for x in rows:
        d=dict(x)
        for key in ("id","warehouse_id","posted_transaction_id"):d[key]=str(d[key]) if d[key] else None
        for key in ("counted_at","created_at"):d[key]=d[key].isoformat() if d[key] else None
        d["variance_quantity"]=format(d["variance_quantity"],"f");data.append(d)
    return {"data":data,"meta":{"request_id":str(context.request_id)}}


@router.get("/stock-counts/{count_id}")
def count_detail(count_id:UUID,request:Request,authorization:str|None=Header(default=None),
                 x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);require_permission(context,"inventory.read")
    engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    with engine.connect() as db:
        head=db.execute(text("SELECT id,count_number,status,warehouse_id,reference FROM stock_counts WHERE tenant_id=:tenant AND id=:id"),
                        {"tenant":context.tenant_id,"id":count_id}).mappings().first()
        if not head:raise HTTPException(status_code=404,detail={"code":"RESOURCE_NOT_FOUND"})
        rows=db.execute(text("""
          SELECT scl.id,scl.product_id,p.sku,p.name product_name,scl.location_id,l.code location_code,
                 scl.system_quantity,scl.counted_quantity,(scl.counted_quantity-scl.system_quantity) variance
          FROM stock_count_lines scl JOIN products p ON p.tenant_id=scl.tenant_id AND p.id=scl.product_id
          JOIN warehouse_locations l ON l.tenant_id=scl.tenant_id AND l.id=scl.location_id
          WHERE scl.tenant_id=:tenant AND scl.stock_count_id=:id ORDER BY scl.line_no
        """),{"tenant":context.tenant_id,"id":count_id}).mappings().all()
    h=dict(head);h["id"]=str(h["id"]);h["warehouse_id"]=str(h["warehouse_id"])
    h["lines"]=[{"id":str(x["id"]),"product_id":str(x["product_id"]),"sku":x["sku"],"product_name":x["product_name"],
                 "location_id":str(x["location_id"]),"location_code":x["location_code"],"system_quantity":format(x["system_quantity"],"f"),
                 "counted_quantity":format(x["counted_quantity"],"f") if x["counted_quantity"] is not None else None,
                 "variance":format(x["variance"],"f") if x["variance"] is not None else None} for x in rows]
    return {"data":h,"meta":{"request_id":str(context.request_id)}}


@router.put("/stock-counts/{count_id}/counts")
def save_counts(count_id:UUID,payload:CountRecord,request:Request,authorization:str|None=Header(default=None),
                x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    try:
        with engine.begin() as db:record_count(db,context=context,count_id=count_id,lines=[(x.line_id,x.counted_quantity) for x in payload.lines])
    except InventoryOperationsError as exc:raise HTTPException(status_code=409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(count_id),"saved":True},"meta":{"request_id":str(context.request_id)}}


@router.post("/stock-counts/{count_id}/post")
def post_count(count_id:UUID,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),
               authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    if not idempotency_key:raise HTTPException(status_code=422,detail={"code":"VALIDATION_FAILED","message":"Idempotency-Key required"})
    context=_context(request,authorization,x_tenant_id);engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    try:
        with engine.begin() as db:tx=post_stock_count(db,context=context,count_id=count_id,idempotency_key=idempotency_key)
    except InventoryOperationsError as exc:raise HTTPException(status_code=409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(count_id),"status":"POSTED","transaction_id":str(tx) if tx else None},"meta":{"request_id":str(context.request_id)}}


@router.put("/reorder-policies")
def put_reorder(payload:ReorderPolicy,request:Request,authorization:str|None=Header(default=None),
                x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    try:
        with engine.begin() as db:pid=upsert_reorder_policy(db,context=context,product_id=payload.product_id,location_id=payload.location_id,
            reorder_point=payload.reorder_point,target_quantity=payload.target_quantity,active=payload.is_active)
    except InventoryOperationsError as exc:raise HTTPException(status_code=409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(pid)},"meta":{"request_id":str(context.request_id)}}


@router.get("/reorder")
def reorder(request:Request,authorization:str|None=Header(default=None),
            x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);require_permission(context,"inventory.read")
    engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    with engine.connect() as db:rows=reorder_status(db,context.tenant_id)
    data=[]
    for x in rows:
        d=dict(x)
        for key in ("id","product_id","location_id"):d[key]=str(d[key])
        for key in ("reorder_point","target_quantity","on_hand","suggested_quantity"):d[key]=format(d[key],"f")
        d["needs_reorder"]=Decimal(d["on_hand"])<=Decimal(d["reorder_point"]);data.append(d)
    return {"data":data,"meta":{"request_id":str(context.request_id),"procurement_document_created":False}}


@router.get("/reports/summary")
def report_summary(request:Request,authorization:str|None=Header(default=None),
                   x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);require_permission(context,"inventory.report")
    engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    with engine.connect() as db:
        row=db.execute(text("""
          SELECT (SELECT count(*) FROM inventory_balances WHERE tenant_id=:t AND on_hand>0) stock_positions,
                 (SELECT COALESCE(sum(on_hand),0) FROM inventory_balances WHERE tenant_id=:t) total_on_hand,
                 (SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t) movements,
                 (SELECT count(*) FROM stock_counts WHERE tenant_id=:t AND status='POSTED') posted_counts,
                 (SELECT count(*) FROM reorder_policies rp LEFT JOIN inventory_balances b
                    ON b.tenant_id=rp.tenant_id AND b.product_id=rp.product_id AND b.location_id=rp.location_id
                    WHERE rp.tenant_id=:t AND rp.is_active AND COALESCE(b.on_hand,0)<=rp.reorder_point) low_stock
        """),{"t":context.tenant_id}).mappings().one()
    data=dict(row);data["total_on_hand"]=format(data["total_on_hand"],"f")
    return {"data":data,"meta":{"request_id":str(context.request_id)}}
