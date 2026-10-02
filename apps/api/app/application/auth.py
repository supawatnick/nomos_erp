from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.domain.security import (
    RequestContext,
    hash_session_token,
    new_session_token,
    verify_password,
)


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


def create_session(
    email: str, password: str, tenant_id: UUID, request_id: UUID
) -> tuple[str, RequestContext]:
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    token = new_session_token()
    now = datetime.now(UTC)
    with engine.begin() as connection:
        row = connection.execute(
            text("""
                SELECT u.id AS user_id,u.password_hash,tu.id AS tenant_user_id
                FROM users u JOIN tenant_users tu ON tu.user_id=u.id AND tu.tenant_id=:tenant
                WHERE lower(u.email)=lower(:email) AND u.status='ACTIVE' AND tu.status='ACTIVE'
            """),
            {"tenant": tenant_id, "email": email},
        ).mappings().first()
        if row is None or not verify_password(password, row["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "AUTHENTICATION_REQUIRED"},
            )
        connection.execute(
            text("INSERT INTO sessions (id,user_id,token_hash,expires_at,created_at) VALUES (:id,:user,:hash,:expires,:now)"),
            {
                "id": __import__("uuid").uuid4(),
                "user": row["user_id"],
                "hash": hash_session_token(token),
                "expires": now + timedelta(hours=12),
                "now": now,
            },
        )
    return token, resolve_session(token, tenant_id, request_id)


def revoke_session(token: str) -> bool:
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.begin() as connection:
        result = connection.execute(
            text("UPDATE sessions SET revoked_at=:now WHERE token_hash=:hash AND revoked_at IS NULL"),
            {"now": datetime.now(UTC), "hash": hash_session_token(token)},
        )
    return bool(result.rowcount)
