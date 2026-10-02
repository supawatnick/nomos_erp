from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from test_phase4_inventory import ctx, seed

from app.application.crm import create_partner
from app.application.procurement import (
    ProcurementError,
    award_rfq,
    create_purchase_request,
    create_rfq,
    record_supplier_quote,
    send_rfq,
    transition_purchase_request,
)
from app.core.config import get_settings


@pytest.fixture
def engine():
    url = get_settings().database_url
    if not url.startswith("postgresql"):
        pytest.skip("Phase 8 acceptance requires PostgreSQL")
    value = create_engine(url, pool_pre_ping=True)
    try:
        yield value
    finally:
        value.dispose()


def procurement_ctx(engine, tenant):
    base = ctx(tenant)
    now = __import__("datetime").datetime.now(__import__("datetime").UTC)
    with engine.begin() as db:
        db.execute(text("""INSERT INTO users
            (id,email,password_hash,display_name,status,created_at,updated_at)
            VALUES (:id,:email,'test','Phase 8 User','ACTIVE',:now,:now)"""),
            {"id": base.actor_user_id, "email": f"p8-{base.actor_user_id.hex}@example.test", "now": now})
        db.execute(text("""INSERT INTO tenant_users
            (id,tenant_id,user_id,status,joined_at,created_at,updated_at)
            VALUES (:id,:tenant,:user,'ACTIVE',:now,:now,:now)"""),
            {"id": base.tenant_user_id, "tenant": tenant, "user": base.actor_user_id, "now": now})
    permissions = base.permissions | frozenset({
        "partner.manage", "procurement.read", "purchase_request.manage", "rfq.manage",
        "purchase_order.manage", "purchase_order.approve", "purchase_order.override", "procurement.receive",
    })
    return type(base)(request_id=base.request_id, actor_user_id=base.actor_user_id, tenant_id=base.tenant_id,
        tenant_user_id=base.tenant_user_id, permissions=permissions)


def _master_ids(engine, tenant):
    with engine.connect() as db:
        product = db.execute(text("SELECT id,base_unit_id FROM products WHERE tenant_id=:t AND status='ACTIVE' LIMIT 1"),
                             {"t": tenant}).mappings().one()
    return product["id"], product["base_unit_id"]


def test_pr_rfq_quote_award_has_no_inventory_side_effect(engine):
    tenant, *_ = seed(engine)
    context = procurement_ctx(engine, tenant)
    product_id, unit_id = _master_ids(engine, tenant)
    with engine.begin() as db:
        s1 = create_partner(db, context=context, code="SUP-"+uuid4().hex[:8], name="Supplier A", is_customer=False, is_supplier=True)
        s2 = create_partner(db, context=context, code="SUP-"+uuid4().hex[:8], name="Supplier B", is_customer=False, is_supplier=True)
        before = db.execute(text("SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t"), {"t": tenant}).scalar_one()
        pr = create_purchase_request(db, context=context, request_number="PR-"+uuid4().hex[:8],
            lines=[{"product_id": product_id, "unit_id": unit_id, "quantity": Decimal("2.50000000")}])
        transition_purchase_request(db, context=context, request_id=pr, status="PENDING_APPROVAL")
        transition_purchase_request(db, context=context, request_id=pr, status="APPROVED")
        rfq = create_rfq(db, context=context, rfq_number="RFQ-"+uuid4().hex[:8], purchase_request_id=pr,
                         supplier_ids=[s1, s2], currency_code="THB")
        send_rfq(db, context=context, rfq_id=rfq)
        record_supplier_quote(db, context=context, rfq_id=rfq, supplier_id=s1, quoted_total=Decimal("1250.25"))
        record_supplier_quote(db, context=context, rfq_id=rfq, supplier_id=s2, quoted_total=Decimal("1300.00"))
        award_rfq(db, context=context, rfq_id=rfq, supplier_id=s1)
        after = db.execute(text("SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t"), {"t": tenant}).scalar_one()
        assert after == before
    with engine.connect() as db:
        row = db.execute(text("SELECT status,awarded_supplier_id FROM procurement_rfqs WHERE tenant_id=:t AND id=:id"),
                         {"t": tenant, "id": rfq}).mappings().one()
        assert row["status"] == "AWARDED" and row["awarded_supplier_id"] == s1
        assert db.execute(text("""SELECT count(*) FROM procurement_rfq_suppliers
            WHERE tenant_id=:t AND rfq_id=:id AND status='AWARDED'"""), {"t": tenant, "id": rfq}).scalar_one() == 1


def test_cross_tenant_supplier_cannot_be_invited(engine):
    t1, *_ = seed(engine)
    t2, *_ = seed(engine)
    c1, c2 = procurement_ctx(engine, t1), procurement_ctx(engine, t2)
    with engine.begin() as db:
        foreign_supplier = create_partner(db, context=c2, code="FOREIGN-"+uuid4().hex[:8],
            name="Foreign Supplier", is_customer=False, is_supplier=True)
    with engine.begin() as db, pytest.raises(ProcurementError, match="supplier not found"):
        create_rfq(db, context=c1, rfq_number="RFQ-"+uuid4().hex[:8], supplier_ids=[foreign_supplier])


def test_rfq_cannot_award_unanswered_supplier(engine):
    tenant, *_ = seed(engine)
    context = procurement_ctx(engine, tenant)
    with engine.begin() as db:
        s1 = create_partner(db, context=context, code="S1-"+uuid4().hex[:8], name="Supplier A", is_customer=False, is_supplier=True)
        s2 = create_partner(db, context=context, code="S2-"+uuid4().hex[:8], name="Supplier B", is_customer=False, is_supplier=True)
        rfq = create_rfq(db, context=context, rfq_number="RFQ-"+uuid4().hex[:8], supplier_ids=[s1, s2])
        send_rfq(db, context=context, rfq_id=rfq)
        record_supplier_quote(db, context=context, rfq_id=rfq, supplier_id=s1, quoted_total=Decimal(10))
        with pytest.raises(ProcurementError, match="responding supplier not found"):
            award_rfq(db, context=context, rfq_id=rfq, supplier_id=s2)


def test_pr_invalid_transition_rejected(engine):
    tenant, *_ = seed(engine)
    context = procurement_ctx(engine, tenant)
    product_id, unit_id = _master_ids(engine, tenant)
    with engine.begin() as db:
        pr = create_purchase_request(db, context=context, request_number="PR-"+uuid4().hex[:8],
            lines=[{"product_id": product_id, "unit_id": unit_id, "quantity": Decimal(1)}])
        with pytest.raises(ProcurementError, match="invalid purchase request transition"):
            transition_purchase_request(db, context=context, request_id=pr, status="APPROVED")
