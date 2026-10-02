from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from app.api_master import trusted_context
from app.application.inventory import (
    IdempotencyConflict,
    InsufficientStock,
    InventoryError,
    StockLine,
    post_inventory,
    reconcile_inventory,
    reverse_inventory,
)
from app.core.config import get_settings
from app.domain.security import require_permission

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


class InventoryLineRequest(BaseModel):
    product_id: UUID
    unit_id: UUID
    location_id: UUID
    quantity: Decimal = Field(gt=0)
    destination_location_id: UUID | None = None
    adjustment_direction: int | None = None


class InventoryPostRequest(BaseModel):
    transaction_type: str
    legal_entity_id: UUID
    branch_id: UUID | None = None
    lines: list[InventoryLineRequest] = Field(min_length=1, max_length=200)
    reference: str | None = Field(default=None, max_length=240)
    reason: str | None = Field(default=None, max_length=1000)
    source_type: str | None = Field(default=None, max_length=80)
    source_id: UUID | None = None
    source_number: str | None = Field(default=None, max_length=120)


class ReverseRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


def _context(request: Request, authorization: str | None, tenant: str | None):
    return trusted_context(request, authorization, tenant)


@router.post("/transactions", status_code=status.HTTP_201_CREATED)
def post_transaction(
    payload: InventoryPostRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    if not idempotency_key or len(idempotency_key) > 200:
        raise HTTPException(status_code=422, detail={"code":"VALIDATION_FAILED","message":"Idempotency-Key required"})
    context=_context(request,authorization,x_tenant_id)
    lines=[StockLine(**line.model_dump()) for line in payload.lines]
    engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            tx_id=post_inventory(connection,context=context,transaction_type=payload.transaction_type,
                legal_entity_id=payload.legal_entity_id,branch_id=payload.branch_id,lines=lines,
                idempotency_key=idempotency_key,reference=payload.reference,reason=payload.reason,
                source_type=payload.source_type,source_id=payload.source_id,source_number=payload.source_number)
    except InsufficientStock as exc:
        raise HTTPException(status_code=409,detail={"code":"INSUFFICIENT_STOCK"}) from exc
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409,detail={"code":"IDEMPOTENCY_CONFLICT"}) from exc
    except InventoryError as exc:
        raise HTTPException(status_code=409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(tx_id),"status":"POSTED"},"meta":{"request_id":str(context.request_id)}}


@router.post("/transactions/{transaction_id}/reverse", status_code=status.HTTP_201_CREATED)
def reverse_transaction(
    transaction_id: UUID, payload: ReverseRequest, request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    if not idempotency_key or len(idempotency_key)>200:
        raise HTTPException(status_code=422,detail={"code":"VALIDATION_FAILED","message":"Idempotency-Key required"})
    context=_context(request,authorization,x_tenant_id)
    engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            tx_id=reverse_inventory(connection,context=context,transaction_id=transaction_id,
                                    idempotency_key=idempotency_key,reason=payload.reason)
    except InsufficientStock as exc:
        raise HTTPException(status_code=409,detail={"code":"INSUFFICIENT_STOCK"}) from exc
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409,detail={"code":"IDEMPOTENCY_CONFLICT"}) from exc
    except InventoryError as exc:
        raise HTTPException(status_code=409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(tx_id),"status":"POSTED","reversal_of_id":str(transaction_id)},"meta":{"request_id":str(context.request_id)}}




@router.get("/transactions")
def transactions(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context=_context(request,authorization,x_tenant_id)
    require_permission(context,"inventory.read")
    engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    with engine.connect() as connection:
        rows=connection.execute(text("""
            SELECT id,legal_entity_id,branch_id,transaction_type,status,source_type,source_id,source_number,
                   reference,reason,reversal_of_id,reversed_by_id,posted_at
            FROM inventory_transactions WHERE tenant_id=:tenant
            ORDER BY posted_at DESC,id DESC LIMIT 200
        """),{"tenant":context.tenant_id}).mappings().all()
    data=[]
    for row in rows:
        item=dict(row)
        for key in ("id","legal_entity_id","branch_id","source_id","reversal_of_id","reversed_by_id"):
            item[key]=str(item[key]) if item[key] else None
        item["posted_at"]=item["posted_at"].isoformat()
        data.append(item)
    return {"data":data,"meta":{"request_id":str(context.request_id)}}


@router.get("/balances")
def balances(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context=_context(request,authorization,x_tenant_id)
    require_permission(context,"inventory.read")
    engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    with engine.connect() as connection:
        rows=connection.execute(text("""
            SELECT b.product_id,p.sku,p.name product_name,b.location_id,l.code location_code,l.name location_name,
                   w.id warehouse_id,w.code warehouse_code,w.name warehouse_name,b.on_hand,b.updated_at
            FROM inventory_balances b
            JOIN products p ON p.tenant_id=b.tenant_id AND p.id=b.product_id
            JOIN warehouse_locations l ON l.tenant_id=b.tenant_id AND l.id=b.location_id
            JOIN warehouses w ON w.tenant_id=l.tenant_id AND w.id=l.warehouse_id
            WHERE b.tenant_id=:tenant ORDER BY p.sku,l.code,b.product_id,b.location_id LIMIT 200
        """),{"tenant":context.tenant_id}).mappings().all()
    data=[{"product_id":str(x["product_id"]),"sku":x["sku"],"product_name":x["product_name"],
           "location_id":str(x["location_id"]),"location_code":x["location_code"],"location_name":x["location_name"],
           "warehouse_id":str(x["warehouse_id"]),"warehouse_code":x["warehouse_code"],"warehouse_name":x["warehouse_name"],
           "on_hand":format(x["on_hand"],"f"),"updated_at":x["updated_at"].isoformat()} for x in rows]
    return {"data":data,"meta":{"request_id":str(context.request_id)}}


@router.get("/reconciliation")
def reconciliation(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context=_context(request,authorization,x_tenant_id)
    require_permission(context,"inventory.read")
    engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    with engine.connect() as connection:
        mismatches=reconcile_inventory(connection,context.tenant_id)
    data=[{"product_id":str(x["product_id"]),"location_id":str(x["location_id"]),
           "ledger_on_hand":format(x["ledger_on_hand"],"f"),"balance_on_hand":format(x["balance_on_hand"],"f")} for x in mismatches]
    return {"data":data,"meta":{"request_id":str(context.request_id),"reconciled":not data}}
