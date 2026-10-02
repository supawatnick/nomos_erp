from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit


def list_rows(
    connection: Connection, *, table: str, tenant_id: UUID, limit: int = 200
) -> list[dict[str, Any]]:
    queries = {
        "categories": "SELECT id,code,name,status,parent_id FROM categories WHERE tenant_id=:tenant ORDER BY code,id LIMIT :limit",
        "units": "SELECT id,code,name,symbol,precision,status FROM units WHERE tenant_id=:tenant ORDER BY code,id LIMIT :limit",
        "locations": "SELECT id,warehouse_id,parent_id,code,name,location_type,allow_stock,status FROM warehouse_locations WHERE tenant_id=:tenant ORDER BY code,id LIMIT :limit",
    }
    if table not in queries:
        raise ValueError("unsupported master table")
    return [dict(row) for row in connection.execute(text(queries[table]), {"tenant": tenant_id, "limit": limit}).mappings()]


def create_category(
    connection: Connection, *, context: RequestContext, code: str, name: str,
    parent_id: UUID | None = None
) -> UUID:
    require_permission(context, "product.manage")
    category_id, now = uuid4(), datetime.now(UTC)
    connection.execute(
        text("INSERT INTO categories (id,tenant_id,parent_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:parent,:code,:name,'ACTIVE',:now,:now)"),
        {"id": category_id, "tenant": context.tenant_id, "parent": parent_id, "code": code, "name": name, "now": now},
    )
    write_audit(connection, tenant_id=context.tenant_id, request_id=context.request_id,
                action="catalog.category.created", actor_user_id=context.actor_user_id,
                actor_tenant_user_id=context.tenant_user_id, target_type="category",
                target_id=category_id, metadata={"code": code})
    return category_id


def create_unit(
    connection: Connection, *, context: RequestContext, code: str, name: str,
    symbol: str | None, precision: int
) -> UUID:
    require_permission(context, "product.manage")
    unit_id, now = uuid4(), datetime.now(UTC)
    connection.execute(
        text("INSERT INTO units (id,tenant_id,code,name,symbol,precision,status,created_at,updated_at) VALUES (:id,:tenant,:code,:name,:symbol,:precision,'ACTIVE',:now,:now)"),
        {"id": unit_id, "tenant": context.tenant_id, "code": code, "name": name, "symbol": symbol, "precision": precision, "now": now},
    )
    write_audit(connection, tenant_id=context.tenant_id, request_id=context.request_id,
                action="catalog.unit.created", actor_user_id=context.actor_user_id,
                actor_tenant_user_id=context.tenant_user_id, target_type="unit",
                target_id=unit_id, metadata={"code": code})
    return unit_id


def create_warehouse(
    connection: Connection, *, context: RequestContext, legal_entity_id: UUID,
    branch_id: UUID | None, code: str, name: str
) -> UUID:
    require_permission(context, "warehouse.manage")
    warehouse_id, now = uuid4(), datetime.now(UTC)
    connection.execute(
        text("INSERT INTO warehouses (id,tenant_id,legal_entity_id,branch_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:entity,:branch,:code,:name,'ACTIVE',:now,:now)"),
        {"id": warehouse_id, "tenant": context.tenant_id, "entity": legal_entity_id, "branch": branch_id, "code": code, "name": name, "now": now},
    )
    write_audit(connection, tenant_id=context.tenant_id, request_id=context.request_id,
                action="warehouse.warehouse.created", actor_user_id=context.actor_user_id,
                actor_tenant_user_id=context.tenant_user_id, target_type="warehouse",
                target_id=warehouse_id, metadata={"code": code})
    return warehouse_id


def create_location(
    connection: Connection, *, context: RequestContext, warehouse_id: UUID,
    parent_id: UUID | None, code: str, name: str, location_type: str = "STORAGE",
    allow_stock: bool = True
) -> UUID:
    from app.application.warehouse import validate_location_parent
    require_permission(context, "warehouse.manage")
    location_id, now = uuid4(), datetime.now(UTC)
    validate_location_parent(connection, tenant_id=context.tenant_id, warehouse_id=warehouse_id,
                             location_id=location_id, parent_id=parent_id)
    connection.execute(
        text("INSERT INTO warehouse_locations (id,tenant_id,warehouse_id,parent_id,code,name,location_type,allow_stock,status,created_at,updated_at) VALUES (:id,:tenant,:warehouse,:parent,:code,:name,:kind,:allow,'ACTIVE',:now,:now)"),
        {"id": location_id, "tenant": context.tenant_id, "warehouse": warehouse_id, "parent": parent_id,
         "code": code, "name": name, "kind": location_type, "allow": allow_stock, "now": now},
    )
    write_audit(connection, tenant_id=context.tenant_id, request_id=context.request_id,
                action="warehouse.location.created", actor_user_id=context.actor_user_id,
                actor_tenant_user_id=context.tenant_user_id, target_type="warehouse_location",
                target_id=location_id, metadata={"code": code})
    return location_id


def archive_master(
    connection: Connection, *, context: RequestContext, resource: str, resource_id: UUID
) -> bool:
    config = {
        "category": ("categories", "product.manage", "catalog.category.archived"),
        "warehouse": ("warehouses", "warehouse.manage", "warehouse.warehouse.archived"),
        "location": ("warehouse_locations", "warehouse.manage", "warehouse.location.archived"),
    }
    if resource not in config:
        raise ValueError("unsupported archive resource")
    table, permission, action = config[resource]
    require_permission(context, permission)
    queries = {
        "categories": "UPDATE categories SET status='ARCHIVED',archived_at=:now,updated_at=:now WHERE tenant_id=:tenant AND id=:id AND status<>'ARCHIVED'",
        "warehouses": "UPDATE warehouses SET status='ARCHIVED',archived_at=:now,updated_at=:now WHERE tenant_id=:tenant AND id=:id AND status<>'ARCHIVED'",
        "warehouse_locations": "UPDATE warehouse_locations SET status='ARCHIVED',archived_at=:now,updated_at=:now WHERE tenant_id=:tenant AND id=:id AND status<>'ARCHIVED'",
    }
    result = connection.execute(text(queries[table]), {"now": datetime.now(UTC), "tenant": context.tenant_id, "id": resource_id})
    if result.rowcount:
        write_audit(connection, tenant_id=context.tenant_id, request_id=context.request_id,
                    action=action, actor_user_id=context.actor_user_id,
                    actor_tenant_user_id=context.tenant_user_id, target_type=resource,
                    target_id=resource_id, metadata={})
    return bool(result.rowcount)


def add_product_unit(
    connection: Connection, *, context: RequestContext, product_id: UUID, unit_id: UUID,
    factor_to_base: Decimal, is_purchase_unit: bool = False, is_sales_unit: bool = False
) -> UUID:
    from app.application.catalog import validate_conversion
    require_permission(context, "product.manage")
    validate_conversion(factor_to_base)
    row_id, now = uuid4(), datetime.now(UTC)
    connection.execute(
        text("INSERT INTO product_units (id,tenant_id,product_id,unit_id,factor_to_base,is_purchase_unit,is_sales_unit,created_at,updated_at) VALUES (:id,:tenant,:product,:unit,:factor,:purchase,:sales,:now,:now)"),
        {"id": row_id, "tenant": context.tenant_id, "product": product_id, "unit": unit_id,
         "factor": factor_to_base, "purchase": is_purchase_unit, "sales": is_sales_unit, "now": now},
    )
    write_audit(connection, tenant_id=context.tenant_id, request_id=context.request_id,
                action="catalog.product.updated", actor_user_id=context.actor_user_id,
                actor_tenant_user_id=context.tenant_user_id, target_type="product",
                target_id=product_id, metadata={"changed_fields": ["units"]})
    return row_id


def add_product_barcode(
    connection: Connection, *, context: RequestContext, product_id: UUID,
    barcode: str, product_unit_id: UUID | None = None
) -> UUID:
    require_permission(context, "product.manage")
    row_id = uuid4()
    connection.execute(
        text("INSERT INTO product_barcodes (id,tenant_id,product_id,product_unit_id,barcode,created_at) VALUES (:id,:tenant,:product,:product_unit,:barcode,:now)"),
        {"id": row_id, "tenant": context.tenant_id, "product": product_id,
         "product_unit": product_unit_id, "barcode": barcode, "now": datetime.now(UTC)},
    )
    write_audit(connection, tenant_id=context.tenant_id, request_id=context.request_id,
                action="catalog.product.updated", actor_user_id=context.actor_user_id,
                actor_tenant_user_id=context.tenant_user_id, target_type="product",
                target_id=product_id, metadata={"changed_fields": ["barcodes"]})
    return row_id
