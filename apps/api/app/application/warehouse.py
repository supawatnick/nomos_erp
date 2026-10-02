from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

from app.domain.security import RequestContext, require_permission


class WarehouseRepository:
    def list_warehouses(
        self, connection: Connection, tenant_id: UUID, *, search: str | None,
        status: str | None, limit: int, after: UUID | None
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            text("""
                SELECT id,code,name,legal_entity_id,branch_id,status,updated_at
                FROM warehouses WHERE tenant_id=:tenant
                  AND (:status IS NULL OR status=:status)
                  AND (:search IS NULL OR code ILIKE :pattern OR name ILIKE :pattern)
                  AND (:after IS NULL OR id > :after)
                ORDER BY id ASC LIMIT :limit
            """),
            {"tenant": tenant_id, "status": status, "search": search,
             "pattern": f"%{search}%" if search else None, "after": after, "limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def validate_location_parent(
    connection: Connection, *, tenant_id: UUID, warehouse_id: UUID,
    location_id: UUID, parent_id: UUID | None
) -> None:
    if parent_id is None:
        return
    if parent_id == location_id:
        raise ValueError("location cannot be its own parent")
    current: UUID | None = parent_id
    visited: set[UUID] = set()
    while current is not None:
        if current in visited or current == location_id:
            raise ValueError("location hierarchy cycle")
        visited.add(current)
        row = connection.execute(
            text("SELECT parent_id FROM warehouse_locations WHERE tenant_id=:tenant AND warehouse_id=:warehouse AND id=:id"),
            {"tenant": tenant_id, "warehouse": warehouse_id, "id": current},
        ).mappings().first()
        if row is None:
            raise ValueError("parent location not found in warehouse")
        current = row["parent_id"]


def archive_location(
    connection: Connection, *, context: RequestContext, location_id: UUID
) -> bool:
    require_permission(context, "warehouse.manage")
    now = datetime.now(UTC)
    result = connection.execute(
        text("""
            UPDATE warehouse_locations SET status='ARCHIVED',archived_at=:now,updated_at=:now
            WHERE tenant_id=:tenant AND id=:id AND status<>'ARCHIVED'
              AND NOT EXISTS (
                SELECT 1 FROM inventory_balances b
                WHERE b.tenant_id=warehouse_locations.tenant_id
                  AND b.location_id=warehouse_locations.id AND b.on_hand<>0
              )
        """),
        {"now": now, "tenant": context.tenant_id, "id": location_id},
    )
    return bool(result.rowcount)
