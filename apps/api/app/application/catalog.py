from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit, write_outbox


class CatalogRepository:
    def list_products(
        self, connection: Connection, tenant_id: UUID, *, search: str | None, status: str | None,
        limit: int, after: UUID | None
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            text("""
                SELECT id,sku,name,product_type,tracking_type,status,category_id,base_unit_id,updated_at
                FROM products
                WHERE tenant_id=:tenant
                  AND (:status IS NULL OR status=:status)
                  AND (:search IS NULL OR sku ILIKE :pattern OR name ILIKE :pattern)
                  AND (:after IS NULL OR id > :after)
                ORDER BY id ASC LIMIT :limit
            """),
            {"tenant": tenant_id, "status": status, "search": search,
             "pattern": f"%{search}%" if search else None, "after": after, "limit": limit},
        ).mappings()
        return [dict(row) for row in rows]

    def get_product(self, connection: Connection, tenant_id: UUID, product_id: UUID) -> dict[str, Any] | None:
        row = connection.execute(
            text("SELECT * FROM products WHERE tenant_id=:tenant AND id=:id"),
            {"tenant": tenant_id, "id": product_id},
        ).mappings().first()
        return dict(row) if row else None

    def create_product(
        self, connection: Connection, *, tenant_id: UUID, sku: str, name: str,
        product_type: str, base_unit_id: UUID, category_id: UUID | None,
        tracking_type: str, description: str | None
    ) -> UUID:
        product_id, now = uuid4(), datetime.now(UTC)
        connection.execute(
            text("""
                INSERT INTO products
                (id,tenant_id,sku,name,description,category_id,product_type,base_unit_id,
                 tracking_type,status,created_at,updated_at)
                VALUES (:id,:tenant,:sku,:name,:description,:category,:product_type,:unit,
                        :tracking,'ACTIVE',:now,:now)
            """),
            {"id": product_id, "tenant": tenant_id, "sku": sku, "name": name,
             "description": description, "category": category_id, "product_type": product_type,
             "unit": base_unit_id, "tracking": tracking_type, "now": now},
        )
        return product_id

    def archive_product(self, connection: Connection, tenant_id: UUID, product_id: UUID) -> bool:
        now = datetime.now(UTC)
        result = connection.execute(
            text("UPDATE products SET status='ARCHIVED',archived_at=:now,updated_at=:now WHERE tenant_id=:tenant AND id=:id AND status<>'ARCHIVED'"),
            {"now": now, "tenant": tenant_id, "id": product_id},
        )
        return bool(result.rowcount)


def create_product(
    connection: Connection, *, context: RequestContext, sku: str, name: str,
    product_type: str, base_unit_id: UUID, category_id: UUID | None = None,
    tracking_type: str = "NONE", description: str | None = None
) -> UUID:
    require_permission(context, "product.manage")
    product_id = CatalogRepository().create_product(
        connection, tenant_id=context.tenant_id, sku=sku, name=name,
        product_type=product_type, base_unit_id=base_unit_id, category_id=category_id,
        tracking_type=tracking_type, description=description,
    )
    write_audit(
        connection, tenant_id=context.tenant_id, request_id=context.request_id,
        action="catalog.product.created", actor_user_id=context.actor_user_id,
        actor_tenant_user_id=context.tenant_user_id, target_type="product",
        target_id=product_id, metadata={"sku": sku},
    )
    write_outbox(
        connection, tenant_id=context.tenant_id, aggregate_type="product",
        aggregate_id=product_id, event_type="catalog.product.created",
        payload={"product_id": str(product_id)},
    )
    return product_id


def archive_product(connection: Connection, *, context: RequestContext, product_id: UUID) -> bool:
    require_permission(context, "product.manage")
    changed = CatalogRepository().archive_product(connection, context.tenant_id, product_id)
    if changed:
        write_audit(
            connection, tenant_id=context.tenant_id, request_id=context.request_id,
            action="catalog.product.archived", actor_user_id=context.actor_user_id,
            actor_tenant_user_id=context.tenant_user_id, target_type="product",
            target_id=product_id, metadata={},
        )
    return changed


def validate_conversion(factor_to_base: Decimal) -> None:
    if factor_to_base <= Decimal("0"):
        raise ValueError("factor_to_base must be positive")
    if factor_to_base.as_tuple().exponent < -8:
        raise ValueError("factor_to_base supports at most 8 decimal places")
