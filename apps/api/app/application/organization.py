from uuid import UUID

from sqlalchemy import Connection

from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import LegalEntityRepository, write_audit, write_outbox


def rename_legal_entity(
    connection: Connection,
    *,
    context: RequestContext,
    entity_id: UUID,
    legal_name: str,
) -> bool:
    require_permission(context, "organization.manage")
    repository = LegalEntityRepository()
    changed = repository.rename(connection, context.tenant_id, entity_id, legal_name)
    if not changed:
        return False
    write_audit(
        connection,
        tenant_id=context.tenant_id,
        request_id=context.request_id,
        action="organization.legal_entity.updated",
        actor_user_id=context.actor_user_id,
        actor_tenant_user_id=context.tenant_user_id,
        target_type="legal_entity",
        target_id=entity_id,
        metadata={"changed_fields": ["legal_name"]},
    )
    write_outbox(
        connection,
        tenant_id=context.tenant_id,
        aggregate_type="legal_entity",
        aggregate_id=entity_id,
        event_type="organization.legal_entity.updated",
        payload={"legal_entity_id": str(entity_id)},
    )
    return True
