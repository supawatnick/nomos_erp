from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.application.auth import resolve_session
from app.core.config import get_settings
from app.domain.security import hash_session_token


@pytest.fixture
def postgres_connection():
    url = get_settings().database_url
    if not url.startswith("postgresql"):
        pytest.skip("Phase 2 database isolation gate requires PostgreSQL")
    engine = create_engine(url)
    connection = engine.connect()
    transaction = connection.begin()
    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()
        engine.dispose()


def test_cross_tenant_branch_reference_rejected(postgres_connection) -> None:
    now = datetime.now(UTC)
    tenant_a, tenant_b, entity_a = uuid4(), uuid4(), uuid4()
    for tenant_id, slug in ((tenant_a, "phase2-a-" + tenant_a.hex), (tenant_b, "phase2-b-" + tenant_b.hex)):
        postgres_connection.execute(
            text("INSERT INTO tenants (id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at) VALUES (:id,:slug,'T','ACTIVE','th-TH','Asia/Bangkok','THB',:now,:now)"),
            {"id": tenant_id, "slug": slug, "now": now},
        )
    postgres_connection.execute(
        text("INSERT INTO legal_entities (id,tenant_id,code,legal_name,country_code,base_currency,timezone,status,created_at,updated_at) VALUES (:id,:tenant,'LE','Legal','TH','THB','Asia/Bangkok','ACTIVE',:now,:now)"),
        {"id": entity_a, "tenant": tenant_a, "now": now},
    )
    with pytest.raises(IntegrityError):
        with postgres_connection.begin_nested():
            postgres_connection.execute(
                text("INSERT INTO branches (id,tenant_id,legal_entity_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:entity,'B','Branch','ACTIVE',:now,:now)"),
                {"id": uuid4(), "tenant": tenant_b, "entity": entity_a, "now": now},
            )


def test_disabled_membership_cannot_resolve_session(postgres_connection) -> None:
    now = datetime.now(UTC)
    tenant_id, user_id, membership_id, session_id = uuid4(), uuid4(), uuid4(), uuid4()
    token = "phase2-test-" + uuid4().hex
    postgres_connection.execute(
        text("INSERT INTO tenants (id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at) VALUES (:id,:slug,'T','ACTIVE','th-TH','Asia/Bangkok','THB',:now,:now)"),
        {"id": tenant_id, "slug": "phase2-" + tenant_id.hex, "now": now},
    )
    postgres_connection.execute(
        text("INSERT INTO users (id,email,password_hash,display_name,status,created_at,updated_at) VALUES (:id,:email,'x','U','ACTIVE',:now,:now)"),
        {"id": user_id, "email": user_id.hex + "@example.invalid", "now": now},
    )
    postgres_connection.execute(
        text("INSERT INTO tenant_users (id,tenant_id,user_id,status,joined_at,created_at,updated_at) VALUES (:id,:tenant,:user,'DISABLED',:now,:now,:now)"),
        {"id": membership_id, "tenant": tenant_id, "user": user_id, "now": now},
    )
    postgres_connection.execute(
        text("INSERT INTO sessions (id,user_id,token_hash,expires_at,created_at) VALUES (:id,:user,:hash,:expires,:now)"),
        {"id": session_id, "user": user_id, "hash": hash_session_token(token), "expires": now + timedelta(hours=1), "now": now},
    )
    postgres_connection.commit()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        resolve_session(token, tenant_id, uuid4())
    assert exc.value.status_code == 401
