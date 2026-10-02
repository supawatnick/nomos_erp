from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.domain.security import RequestContext, hash_session_token


def resolve_session(token: str, tenant_id: UUID, request_id: UUID) -> RequestContext:
    query = text("""
        SELECT s.user_id, tu.id AS tenant_user_id, tu.tenant_id,
               COALESCE(array_agg(DISTINCT p.code) FILTER (WHERE p.code IS NOT NULL), '{}')
                   AS permissions
        FROM sessions s
        JOIN users u ON u.id=s.user_id
        JOIN tenant_users tu ON tu.user_id=u.id AND tu.tenant_id=:tenant_id
        LEFT JOIN tenant_user_roles tur
          ON tur.tenant_id=tu.tenant_id AND tur.tenant_user_id=tu.id
        LEFT JOIN roles r
          ON r.tenant_id=tur.tenant_id AND r.id=tur.role_id AND r.status='ACTIVE'
        LEFT JOIN role_permissions rp ON rp.tenant_id=r.tenant_id AND rp.role_id=r.id
        LEFT JOIN permissions p ON p.id=rp.permission_id
        WHERE s.token_hash=:token_hash AND s.revoked_at IS NULL AND s.expires_at>:now
          AND u.status='ACTIVE' AND tu.status='ACTIVE'
        GROUP BY s.user_id,tu.id,tu.tenant_id
    """)
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    params = {
        "tenant_id": tenant_id,
        "token_hash": hash_session_token(token),
        "now": datetime.now(UTC),
    }
    with engine.connect() as connection:
        row = connection.execute(query, params).mappings().first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_REQUIRED"},
        )
    return RequestContext(
        request_id=request_id,
        actor_user_id=row["user_id"],
        tenant_id=row["tenant_id"],
        tenant_user_id=row["tenant_user_id"],
        permissions=frozenset(row["permissions"]),
    )
