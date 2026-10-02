import base64
import json
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.application.auth import resolve_session
from app.application.catalog import CatalogRepository, archive_product, create_product
from app.application.master_data import (
    archive_master,
    create_category,
    create_location,
    create_unit,
    create_warehouse,
    list_rows,
)
from app.application.warehouse import WarehouseRepository
from app.core.config import get_settings
from app.domain.security import RequestContext, require_permission

router = APIRouter(prefix="/api/v1")


class CategoryCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    parent_id: UUID | None = None


class UnitCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=100)
    symbol: str | None = Field(default=None, max_length=24)
    precision: int = Field(default=0, ge=0, le=8)


class WarehouseCreate(BaseModel):
    legal_entity_id: UUID
    branch_id: UUID | None = None
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)


class LocationCreate(BaseModel):
    warehouse_id: UUID
    parent_id: UUID | None = None
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    location_type: str = "STORAGE"
    allow_stock: bool = True


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=240)
    product_type: str
    base_unit_id: UUID
    category_id: UUID | None = None
    tracking_type: str = "NONE"
    description: str | None = None


def trusted_context(
    request: Request, authorization: str | None, tenant_header: str | None
) -> RequestContext:
    if not authorization or not authorization.startswith("Bearer ") or not tenant_header:
        raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"})
    try:
        tenant_id = UUID(tenant_header)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"}) from exc
    return resolve_session(
        authorization.removeprefix("Bearer ").strip(), tenant_id, request.state.request_id
    )


def encode_cursor(resource_id: UUID) -> str:
    raw = json.dumps({"id": str(resource_id)}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str | None) -> UUID | None:
    if cursor is None:
        return None
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return UUID(payload["id"])
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail={"code": "VALIDATION_FAILED"}) from exc


@router.get("/products")
def products(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    search: str | None = Query(default=None, max_length=100),
    resource_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = None,
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    require_permission(context, "product.read")
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        rows = CatalogRepository().list_products(
            connection, context.tenant_id, search=search, status=resource_status,
            limit=limit + 1, after=decode_cursor(cursor),
        )
    has_more = len(rows) > limit
    data = rows[:limit]
    next_cursor = encode_cursor(data[-1]["id"]) if has_more and data else None
    for row in data:
        row["id"] = str(row["id"])
        row["category_id"] = str(row["category_id"]) if row["category_id"] else None
        row["base_unit_id"] = str(row["base_unit_id"])
        row["updated_at"] = row["updated_at"].isoformat()
    return {"data": data, "meta": {"request_id": str(context.request_id), "next_cursor": next_cursor}}


@router.post("/products", status_code=status.HTTP_201_CREATED)
def product_create(
    payload: ProductCreate,
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            product_id = create_product(
                connection, context=context, sku=payload.sku, name=payload.name,
                product_type=payload.product_type, base_unit_id=payload.base_unit_id,
                category_id=payload.category_id, tracking_type=payload.tracking_type,
                description=payload.description,
            )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail={"code": "DUPLICATE_RESOURCE"}) from exc
    return {"data": {"id": str(product_id)}, "meta": {"request_id": str(context.request_id)}}


@router.post("/products/{product_id}/archive")
def product_archive(
    product_id: UUID,
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.begin() as connection:
        changed = archive_product(connection, context=context, product_id=product_id)
    if not changed:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})
    return {"data": {"id": str(product_id), "status": "ARCHIVED"}, "meta": {"request_id": str(context.request_id)}}


@router.get("/warehouses")
def warehouses(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    search: str | None = Query(default=None, max_length=100),
    resource_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = None,
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    require_permission(context, "warehouse.read")
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        rows = WarehouseRepository().list_warehouses(
            connection, context.tenant_id, search=search, status=resource_status,
            limit=limit + 1, after=decode_cursor(cursor),
        )
    has_more = len(rows) > limit
    data = rows[:limit]
    next_cursor = encode_cursor(data[-1]["id"]) if has_more and data else None
    for row in data:
        for key in ("id", "legal_entity_id", "branch_id"):
            row[key] = str(row[key]) if row[key] else None
        row["updated_at"] = row["updated_at"].isoformat()
    return {"data": data, "meta": {"request_id": str(context.request_id), "next_cursor": next_cursor}}


@router.get("/master-data/summary")
def master_summary(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    require_permission(context, "product.read")
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        counts: dict[str, int] = {}
        for table in ("products", "categories", "units", "warehouses", "warehouse_locations"):
            counts[table] = connection.execute(
                text(f"SELECT count(*) FROM {table} WHERE tenant_id=:tenant AND status='ACTIVE'"),
                {"tenant": context.tenant_id},
            ).scalar_one()
    return {"data": counts, "meta": {"request_id": str(context.request_id)}}


def serialize_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    for row in rows:
        for key, value in list(row.items()):
            if isinstance(value, UUID):
                row[key] = str(value)
    return rows


@router.get("/categories")
def categories_list(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    require_permission(context, "product.read")
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        rows = list_rows(connection, table="categories", tenant_id=context.tenant_id)
    return {"data": serialize_rows(rows), "meta": {"request_id": str(context.request_id)}}


@router.post("/categories", status_code=201)
def categories_create(
    payload: CategoryCreate, request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            resource_id = create_category(connection, context=context, **payload.model_dump())
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail={"code": "DUPLICATE_RESOURCE"}) from exc
    return {"data": {"id": str(resource_id)}, "meta": {"request_id": str(context.request_id)}}


@router.get("/units")
def units_list(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    require_permission(context, "product.read")
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        rows = list_rows(connection, table="units", tenant_id=context.tenant_id)
    return {"data": serialize_rows(rows), "meta": {"request_id": str(context.request_id)}}


@router.post("/units", status_code=201)
def units_create(
    payload: UnitCreate, request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            resource_id = create_unit(connection, context=context, **payload.model_dump())
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail={"code": "DUPLICATE_RESOURCE"}) from exc
    return {"data": {"id": str(resource_id)}, "meta": {"request_id": str(context.request_id)}}


@router.post("/warehouses", status_code=201)
def warehouses_create(
    payload: WarehouseCreate, request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            resource_id = create_warehouse(connection, context=context, **payload.model_dump())
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail={"code": "VALIDATION_FAILED"}) from exc
    return {"data": {"id": str(resource_id)}, "meta": {"request_id": str(context.request_id)}}


@router.get("/locations")
def locations_list(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    require_permission(context, "warehouse.read")
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        rows = list_rows(connection, table="locations", tenant_id=context.tenant_id)
    return {"data": serialize_rows(rows), "meta": {"request_id": str(context.request_id)}}


@router.post("/locations", status_code=201)
def locations_create(
    payload: LocationCreate, request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = trusted_context(request, authorization, x_tenant_id)
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            resource_id = create_location(connection, context=context, **payload.model_dump())
    except (IntegrityError, ValueError) as exc:
        raise HTTPException(status_code=409, detail={"code": "VALIDATION_FAILED"}) from exc
    return {"data": {"id": str(resource_id)}, "meta": {"request_id": str(context.request_id)}}


@router.post("/{resource}/{resource_id}/archive")
def master_archive(
    resource: str, resource_id: UUID, request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    if resource not in {"category", "warehouse", "location"}:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})
    context = trusted_context(request, authorization, x_tenant_id)
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.begin() as connection:
        changed = archive_master(connection, context=context, resource=resource, resource_id=resource_id)
    if not changed:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})
    return {"data": {"id": str(resource_id), "status": "ARCHIVED"}, "meta": {"request_id": str(context.request_id)}}
