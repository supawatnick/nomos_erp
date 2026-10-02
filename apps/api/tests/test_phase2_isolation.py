from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.application.auth import resolve_session
from app.core.config import get_settings
from app.domain.security import hash_session_token
from app.infrastructure.platform import (
    LegalEntityRepository,
    claim_idempotency,
    write_audit,
    write_outbox,
)


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


def test_cross_tenant_read_update_archive_are_hidden(postgres_connection) -> None:
    now = datetime.now(UTC)
    tenant_a, tenant_b, entity_id = uuid4(), uuid4(), uuid4()
    for tenant_id in (tenant_a, tenant_b):
        postgres_connection.execute(
            text("INSERT INTO tenants (id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at) VALUES (:id,:slug,'T','ACTIVE','th-TH','Asia/Bangkok','THB',:now,:now)"),
            {"id": tenant_id, "slug": "scope-" + tenant_id.hex, "now": now},
        )
    postgres_connection.execute(
        text("INSERT INTO legal_entities (id,tenant_id,code,legal_name,country_code,base_currency,timezone,status,created_at,updated_at) VALUES (:id,:tenant,'LE','Original','TH','THB','Asia/Bangkok','ACTIVE',:now,:now)"),
        {"id": entity_id, "tenant": tenant_a, "now": now},
    )
    repository = LegalEntityRepository()
    assert repository.get(postgres_connection, tenant_b, entity_id) is None
    assert not repository.rename(postgres_connection, tenant_b, entity_id, "Leaked")
    assert not repository.archive(postgres_connection, tenant_b, entity_id)
    assert repository.get(postgres_connection, tenant_a, entity_id)["legal_name"] == "Original"


def test_admin_audit_and_outbox_are_persisted_atomically(postgres_connection) -> None:
    now = datetime.now(UTC)
    tenant_id, request_id, target_id = uuid4(), uuid4(), uuid4()
    postgres_connection.execute(
        text("INSERT INTO tenants (id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at) VALUES (:id,:slug,'T','ACTIVE','th-TH','Asia/Bangkok','THB',:now,:now)"),
        {"id": tenant_id, "slug": "audit-" + tenant_id.hex, "now": now},
    )
    audit_id = write_audit(
        postgres_connection,
        tenant_id=tenant_id,
        request_id=request_id,
        action="organization.legal_entity.updated",
        actor_user_id=None,
        actor_tenant_user_id=None,
        target_type="legal_entity",
        target_id=target_id,
        metadata={"changed_fields": ["legal_name"]},
    )
    event_id = write_outbox(
        postgres_connection,
        tenant_id=tenant_id,
        aggregate_type="legal_entity",
        aggregate_id=target_id,
        event_type="organization.legal_entity.updated",
        payload={"legal_entity_id": str(target_id)},
    )
    assert postgres_connection.execute(
        text("SELECT count(*) FROM audit_logs WHERE id=:id AND request_id=:request_id"),
        {"id": audit_id, "request_id": request_id},
    ).scalar_one() == 1
    assert postgres_connection.execute(
        text("SELECT count(*) FROM outbox_events WHERE id=:id AND published_at IS NULL"),
        {"id": event_id},
    ).scalar_one() == 1


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


def test_idempotency_replay_and_conflict(postgres_connection) -> None:
    now = datetime.now(UTC)
    tenant_id = uuid4()
    postgres_connection.execute(
        text("INSERT INTO tenants (id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at) VALUES (:id,:slug,'T','ACTIVE','th-TH','Asia/Bangkok','THB',:now,:now)"),
        {"id": tenant_id, "slug": "idem-" + tenant_id.hex, "now": now},
    )
    first = claim_idempotency(
        postgres_connection,
        tenant_id=tenant_id,
        scope="organization.update",
        key="request-1",
        fingerprint="a" * 64,
        expires_at=now + timedelta(hours=1),
    )
    replay = claim_idempotency(
        postgres_connection,
        tenant_id=tenant_id,
        scope="organization.update",
        key="request-1",
        fingerprint="a" * 64,
        expires_at=now + timedelta(hours=1),
    )
    conflict = claim_idempotency(
        postgres_connection,
        tenant_id=tenant_id,
        scope="organization.update",
        key="request-1",
        fingerprint="b" * 64,
        expires_at=now + timedelta(hours=1),
    )
    assert first == (True, True)
    assert replay == (False, True)
    assert conflict == (False, False)


def test_revoked_session_cannot_resolve(postgres_connection) -> None:
    now = datetime.now(UTC)
    tenant_id, user_id, membership_id, session_id = uuid4(), uuid4(), uuid4(), uuid4()
    token = "revoked-" + uuid4().hex
    postgres_connection.execute(
        text("INSERT INTO tenants (id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at) VALUES (:id,:slug,'T','ACTIVE','th-TH','Asia/Bangkok','THB',:now,:now)"),
        {"id": tenant_id, "slug": "revoked-" + tenant_id.hex, "now": now},
    )
    postgres_connection.execute(
        text("INSERT INTO users (id,email,password_hash,display_name,status,created_at,updated_at) VALUES (:id,:email,'x','U','ACTIVE',:now,:now)"),
        {"id": user_id, "email": user_id.hex + "@example.invalid", "now": now},
    )
    postgres_connection.execute(
        text("INSERT INTO tenant_users (id,tenant_id,user_id,status,joined_at,created_at,updated_at) VALUES (:id,:tenant,:user,'ACTIVE',:now,:now,:now)"),
        {"id": membership_id, "tenant": tenant_id, "user": user_id, "now": now},
    )
    postgres_connection.execute(
        text("INSERT INTO sessions (id,user_id,token_hash,expires_at,revoked_at,created_at) VALUES (:id,:user,:hash,:expires,:now,:now)"),
        {"id": session_id, "user": user_id, "hash": hash_session_token(token), "expires": now + timedelta(hours=1), "now": now},
    )
    postgres_connection.commit()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        resolve_session(token, tenant_id, uuid4())
    assert exc.value.status_code == 401
