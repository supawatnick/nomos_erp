from uuid import UUID

from sqlalchemy import Connection, text


def allocate_document_number(
    connection: Connection, *, tenant_id: UUID, document_type: str,
    period_key: str, legal_entity_id: UUID | None = None, branch_id: UUID | None = None
) -> str:
    row = connection.execute(
        text("""
            SELECT id,prefix,next_value,padding FROM document_sequences
            WHERE tenant_id=:tenant AND document_type=:document_type
              AND legal_entity_id IS NOT DISTINCT FROM :entity
              AND branch_id IS NOT DISTINCT FROM :branch AND period_key=:period
            FOR UPDATE
        """),
        {"tenant": tenant_id, "document_type": document_type, "entity": legal_entity_id,
         "branch": branch_id, "period": period_key},
    ).mappings().first()
    if row is None:
        raise ValueError("document sequence not configured")
    connection.execute(
        text("UPDATE document_sequences SET next_value=next_value+1,updated_at=now() WHERE id=:id"),
        {"id": row["id"]},
    )
    return f"{row['prefix']}{int(row['next_value']):0{int(row['padding'])}d}"
