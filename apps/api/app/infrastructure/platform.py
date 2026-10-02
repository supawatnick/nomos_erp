from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, text


class LegalEntityRepository:
    def get(self, connection: Connection, tenant_id: UUID, entity_id: UUID) -> dict[str, Any] | None:
        row = connection.execute(
            text("SELECT id,tenant_id,code,legal_name,status FROM legal_entities WHERE tenant_id=:tenant AND id=:id"),
            {"tenant": tenant_id, "id": entity_id},
        ).mappings().first()
        return dict(row) if row else None

    def rename(self, connection: Connection, tenant_id: UUID, entity_id: UUID, legal_name: str) -> bool:
        result = connection.execute(
            text("UPDATE legal_entities SET legal_name=:name,updated_at=:now WHERE tenant_id=:tenant AND id=:id"),
            {"name": legal_name, "now": datetime.now(UTC), "tenant": tenant_id, "id": entity_id},
        )
        return bool(result.rowcount)

    def archive(self, connection: Connection, tenant_id: UUID, entity_id: UUID) -> bool:
        now = datetime.now(UTC)
        result = connection.execute(
            text("UPDATE legal_entities SET status='ARCHIVED',archived_at=:now,updated_at=:now WHERE tenant_id=:tenant AND id=:id"),
            {"now": now, "tenant": tenant_id, "id": entity_id},
        )
        return bool(result.rowcount)


def write_audit(
    connection: Connection,
    *,
    tenant_id: UUID,
    request_id: UUID,
    action: str,
    actor_user_id: UUID | None,
    actor_tenant_user_id: UUID | None,
    target_type: str | None,
    target_id: UUID | None,
    metadata: dict[str, Any],
) -> UUID:
    audit_id = uuid4()
    connection.execute(
        text("""
            INSERT INTO audit_logs
            (id,tenant_id,occurred_at,actor_user_id,actor_tenant_user_id,action,target_type,
             target_id,channel,request_id,result,metadata)
            VALUES (:id,:tenant,:now,:actor,:membership,:action,:target_type,:target_id,
                    'WEB',:request_id,'SUCCESS',CAST(:metadata AS JSONB))
        """),
        {
            "id": audit_id,
            "tenant": tenant_id,
            "now": datetime.now(UTC),
            "actor": actor_user_id,
            "membership": actor_tenant_user_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "request_id": request_id,
            "metadata": __import__("json").dumps(metadata),
        },
    )
    return audit_id


def write_outbox(
    connection: Connection,
    *,
    tenant_id: UUID,
    aggregate_type: str,
    aggregate_id: UUID,
    event_type: str,
    payload: dict[str, Any],
) -> UUID:
    event_id = uuid4()
    now = datetime.now(UTC)
    connection.execute(
        text("""
            INSERT INTO outbox_events
            (id,tenant_id,aggregate_type,aggregate_id,event_type,payload,occurred_at,available_at)
            VALUES (:id,:tenant,:aggregate_type,:aggregate_id,:event_type,CAST(:payload AS JSONB),:now,:now)
        """),
        {
            "id": event_id,
            "tenant": tenant_id,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "event_type": event_type,
            "payload": __import__("json").dumps(payload),
            "now": now,
        },
    )
    return event_id
