from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from test_phase4_inventory import ctx, seed

from app.application.approvals import (
    ApprovalError,
    ApprovalStale,
    cancel_approval,
    create_policy,
    decide_approval,
    mark_executed,
    request_approval,
    require_approved_snapshot,
)
from app.core.config import get_settings


@pytest.fixture
def engine():
    url = get_settings().database_url
    if not url.startswith("postgresql"):
        pytest.skip("Phase 10 acceptance requires PostgreSQL")
    value = create_engine(url, pool_pre_ping=True)
    try:
        yield value
    finally:
        value.dispose()


def approval_ctx(engine, tenant, permissions, label):
    base = ctx(tenant)
    now = datetime.now(UTC)
    with engine.begin() as db:
        db.execute(text("""INSERT INTO users
            (id,email,password_hash,display_name,status,created_at,updated_at)
            VALUES (:id,:email,'x',:name,'ACTIVE',:now,:now)"""),
            {"id": base.actor_user_id, "email": f"{label}-{base.actor_user_id.hex}@example.test",
             "name": label, "now": now})
        db.execute(text("""INSERT INTO tenant_users
            (id,tenant_id,user_id,status,joined_at,created_at,updated_at)
            VALUES (:id,:tenant,:user,'ACTIVE',:now,:now,:now)"""),
            {"id": base.tenant_user_id, "tenant": tenant, "user": base.actor_user_id, "now": now})
    return type(base)(
        request_id=base.request_id, actor_user_id=base.actor_user_id, tenant_id=tenant,
        tenant_user_id=base.tenant_user_id, permissions=frozenset(permissions),
    )


def test_approval_separation_of_duties_idempotency_and_execution(engine):
    tenant, *_ = seed(engine)
    requester = approval_ctx(engine, tenant, {"approval.request"}, "requester")
    approver = approval_ctx(engine, tenant, {"approval.decide", "purchase_order.approve"}, "approver")
    admin = approval_ctx(engine, tenant, {"approval.policy.manage"}, "admin")
    source_id = uuid4()
    snapshot = {"status": "PENDING_APPROVAL", "version": 4, "total": "12500.00"}
    with engine.begin() as db:
        create_policy(db, context=admin, code="PO-HIGH", name="High PO",
            request_type="PURCHASE_ORDER", required_permission="purchase_order.approve",
            prohibit_self_approval=True)
        approval_id = request_approval(db, context=requester, policy_code="PO-HIGH",
            source_type="PURCHASE_ORDER", source_id=source_id, source_version=4, snapshot=snapshot)
        assert decide_approval(db, context=approver, approval_request_id=approval_id,
            decision="APPROVED", idempotency_key="decision-1") == "APPROVED"
        assert decide_approval(db, context=approver, approval_request_id=approval_id,
            decision="APPROVED", idempotency_key="decision-1") == "APPROVED"
        require_approved_snapshot(db, context=requester, approval_request_id=approval_id,
            source_type="PURCHASE_ORDER", source_id=source_id, source_version=4, snapshot=snapshot)
        mark_executed(db, context=requester, approval_request_id=approval_id,
            execution_reference="PO-2026-000001")
        row = db.execute(text("SELECT status FROM approval_requests WHERE id=:id"),
                         {"id": approval_id}).scalar_one()
        assert row == "EXECUTED"
        assert db.execute(text("SELECT count(*) FROM approval_decisions WHERE approval_request_id=:id"),
                          {"id": approval_id}).scalar_one() == 1


def test_self_approval_and_missing_policy_permission_are_denied(engine):
    tenant, *_ = seed(engine)
    admin = approval_ctx(engine, tenant, {"approval.policy.manage"}, "admin2")
    actor = approval_ctx(engine, tenant, {"approval.request", "approval.decide", "purchase_order.approve"}, "actor")
    weak = approval_ctx(engine, tenant, {"approval.decide"}, "weak")
    with engine.begin() as db:
        create_policy(db, context=admin, code="SOD", name="SoD", request_type="PURCHASE_ORDER",
            required_permission="purchase_order.approve", prohibit_self_approval=True)
        first = request_approval(db, context=actor, policy_code="SOD", source_type="PURCHASE_ORDER",
            source_id=uuid4(), source_version=1, snapshot={"version": 1})
        with pytest.raises(ApprovalError, match="self approval"):
            decide_approval(db, context=actor, approval_request_id=first,
                decision="APPROVED", idempotency_key="self")
        second = request_approval(db, context=actor, policy_code="SOD", source_type="PURCHASE_ORDER",
            source_id=uuid4(), source_version=1, snapshot={"version": 1})
        with pytest.raises(HTTPException):
            decide_approval(db, context=weak, approval_request_id=second,
                decision="APPROVED", idempotency_key="weak")


def test_changed_source_version_or_fingerprint_is_stale(engine):
    tenant, *_ = seed(engine)
    admin = approval_ctx(engine, tenant, {"approval.policy.manage"}, "admin3")
    requester = approval_ctx(engine, tenant, {"approval.request"}, "requester3")
    approver = approval_ctx(engine, tenant, {"approval.decide", "sales.override"}, "approver3")
    source_id = uuid4()
    with engine.begin() as db:
        create_policy(db, context=admin, code="SALES-EX", name="Sales exception",
            request_type="SALES_EXCEPTION", required_permission="sales.override")
        approval_id = request_approval(db, context=requester, policy_code="SALES-EX",
            source_type="SALES_ORDER", source_id=source_id, source_version=2,
            snapshot={"version": 2, "discount": "10.00"})
        decide_approval(db, context=approver, approval_request_id=approval_id,
            decision="APPROVED", idempotency_key="approve")
        with pytest.raises(ApprovalStale, match="version"):
            require_approved_snapshot(db, context=requester, approval_request_id=approval_id,
                source_type="SALES_ORDER", source_id=source_id, source_version=3,
                snapshot={"version": 2, "discount": "10.00"})
        with pytest.raises(ApprovalStale, match="changed"):
            require_approved_snapshot(db, context=requester, approval_request_id=approval_id,
                source_type="SALES_ORDER", source_id=source_id, source_version=2,
                snapshot={"version": 2, "discount": "11.00"})


def test_expiry_cancel_and_cross_tenant_isolation(engine):
    tenant, *_ = seed(engine)
    other, *_ = seed(engine)
    admin = approval_ctx(engine, tenant, {"approval.policy.manage"}, "admin4")
    requester = approval_ctx(engine, tenant, {"approval.request"}, "requester4")
    approver = approval_ctx(engine, tenant, {"approval.decide", "inventory.adjust"}, "approver4")
    foreign = approval_ctx(engine, other, {"approval.decide", "inventory.adjust"}, "foreign4")
    with engine.begin() as db:
        create_policy(db, context=admin, code="INV-ADJ", name="Inventory adjustment",
            request_type="INVENTORY_ADJUSTMENT", required_permission="inventory.adjust",
            expires_after_hours=1)
        expired = request_approval(db, context=requester, policy_code="INV-ADJ",
            source_type="INVENTORY_ADJUSTMENT", source_id=uuid4(), source_version=1,
            snapshot={"quantity": "100"})
        db.execute(text("UPDATE approval_requests SET expires_at=:past WHERE id=:id"),
                   {"past": datetime.now(UTC)-timedelta(minutes=1), "id": expired})
        with pytest.raises(ApprovalError, match="expired"):
            decide_approval(db, context=approver, approval_request_id=expired,
                decision="APPROVED", idempotency_key="expired")
        pending = request_approval(db, context=requester, policy_code="INV-ADJ",
            source_type="INVENTORY_ADJUSTMENT", source_id=uuid4(), source_version=1,
            snapshot={"quantity": "1"})
        with pytest.raises(ApprovalError, match="not found"):
            decide_approval(db, context=foreign, approval_request_id=pending,
                decision="APPROVED", idempotency_key="foreign")
        cancel_approval(db, context=requester, approval_request_id=pending)
        assert db.execute(text("SELECT status FROM approval_requests WHERE id=:id"),
                          {"id": pending}).scalar_one() == "CANCELLED"
