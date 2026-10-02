from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from test_phase4_inventory import ctx, seed

from app.application.crm import create_partner
from app.application.procurement import (
    ProcurementError,
    approve_purchase_order,
    award_rfq,
    create_purchase_order,
    create_purchase_request,
    create_rfq,
    post_goods_receipt,
    post_purchase_return,
    record_supplier_quote,
    send_purchase_order,
    send_rfq,
    submit_purchase_order,
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
        rfq_line = db.execute(text("""SELECT id FROM procurement_rfq_lines
            WHERE tenant_id=:t AND rfq_id=:rfq"""), {"t": tenant, "rfq": rfq}).scalar_one()
        send_rfq(db, context=context, rfq_id=rfq)
        record_supplier_quote(db, context=context, rfq_id=rfq, supplier_id=s1,
            lines=[{"rfq_line_id": rfq_line, "offered_quantity": Decimal("2.5"),
                    "unit_price": Decimal("500.10"), "discount_amount": Decimal("0"),
                    "tax_amount": Decimal("0")}])
        record_supplier_quote(db, context=context, rfq_id=rfq, supplier_id=s2,
            lines=[{"rfq_line_id": rfq_line, "offered_quantity": Decimal("2.5"),
                    "unit_price": Decimal("520.00")}])
        award_rfq(db, context=context, rfq_id=rfq, supplier_id=s1)
        after = db.execute(text("SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t"), {"t": tenant}).scalar_one()
        assert after == before
    with engine.connect() as db:
        row = db.execute(text("SELECT status,awarded_supplier_id FROM procurement_rfqs WHERE tenant_id=:t AND id=:id"),
                         {"t": tenant, "id": rfq}).mappings().one()
        assert row["status"] == "AWARDED" and row["awarded_supplier_id"] == s1
        assert db.execute(text("""SELECT count(*) FROM procurement_rfq_suppliers
            WHERE tenant_id=:t AND rfq_id=:id AND status='AWARDED'"""), {"t": tenant, "id": rfq}).scalar_one() == 1
        comparison = db.execute(text("""SELECT l.line_total FROM procurement_rfq_supplier_lines l
            JOIN procurement_rfq_suppliers s ON s.tenant_id=l.tenant_id AND s.id=l.rfq_supplier_id
            WHERE l.tenant_id=:t AND s.rfq_id=:rfq AND s.supplier_id=:supplier"""),
            {"t": tenant, "rfq": rfq, "supplier": s1}).scalar_one()
        assert Decimal(comparison) == Decimal("1250.25000000")


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


def _seed_sequence(db, tenant, document_type, prefix, *, entity=None, branch=None, period="2026"):
    db.execute(text("""INSERT INTO document_sequences
        (id,tenant_id,document_type,legal_entity_id,branch_id,period_key,prefix,next_value,padding,updated_at)
        VALUES (:id,:tenant,:type,:entity,:branch,:period,:prefix,1,6,now())"""),
        {"id": uuid4(), "tenant": tenant, "type": document_type, "entity": entity,
         "branch": branch, "period": period, "prefix": prefix})


def test_po_approval_and_send_do_not_change_inventory(engine):
    tenant, entity, branch, unit, product, *_ = seed(engine)
    context = procurement_ctx(engine, tenant)
    with engine.begin() as db:
        supplier = create_partner(db, context=context, code="PO-SUP-"+uuid4().hex[:8],
            name="PO Supplier", is_customer=False, is_supplier=True)
        _seed_sequence(db, tenant, "PO", "PO-2026-", entity=entity, branch=branch)
        before = db.execute(text("SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t"),
                            {"t": tenant}).scalar_one()
        order_id = create_purchase_order(
            db, context=context, legal_entity_id=entity, branch_id=branch, supplier_id=supplier,
            currency_code="THB", period_key="2026",
            lines=[{"product_id": product, "unit_id": unit, "quantity": Decimal(5),
                    "unit_price": Decimal("100.25"), "discount_amount": Decimal("1.25"),
                    "tax_amount": Decimal("35.00")}],
        )
        submit_purchase_order(db, context=context, order_id=order_id)
        approve_purchase_order(db, context=context, order_id=order_id)
        send_purchase_order(db, context=context, order_id=order_id)
        after = db.execute(text("SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t"),
                           {"t": tenant}).scalar_one()
        assert before == after
        row = db.execute(text("""SELECT order_number,status,approval_fingerprint,approved_version
            FROM purchase_orders WHERE tenant_id=:t AND id=:id"""),
            {"t": tenant, "id": order_id}).mappings().one()
        assert row["order_number"] == "PO-2026-000001"
        assert row["status"] == "SENT"
        assert row["approval_fingerprint"] and row["approved_version"] == 2
        total = db.execute(text("""SELECT line_total FROM purchase_order_lines
            WHERE tenant_id=:t AND purchase_order_id=:id"""),
            {"t": tenant, "id": order_id}).scalar_one()
        assert Decimal(total) == Decimal("535.00")


def test_po_rejects_cross_tenant_supplier(engine):
    t1, e1, b1, unit1, product1, *_ = seed(engine)
    t2, *_ = seed(engine)
    c1, c2 = procurement_ctx(engine, t1), procurement_ctx(engine, t2)
    with engine.begin() as db:
        foreign_supplier = create_partner(db, context=c2, code="XPO-"+uuid4().hex[:8],
            name="Foreign PO Supplier", is_customer=False, is_supplier=True)
        _seed_sequence(db, t1, "PO", "PO-X-", entity=e1, branch=b1)
        with pytest.raises(ProcurementError, match="supplier not found"):
            create_purchase_order(db, context=c1, legal_entity_id=e1, branch_id=b1,
                supplier_id=foreign_supplier, period_key="2026",
                lines=[{"product_id": product1, "unit_id": unit1, "quantity": Decimal(1),
                        "unit_price": Decimal(10)}])


def test_po_approval_requires_high_risk_permission(engine):
    tenant, entity, branch, unit, product, *_ = seed(engine)
    context = procurement_ctx(engine, tenant)
    with engine.begin() as db:
        supplier = create_partner(db, context=context, code="APP-"+uuid4().hex[:8],
            name="Approval Supplier", is_customer=False, is_supplier=True)
        _seed_sequence(db, tenant, "PO", "PO-A-", entity=entity, branch=branch)
        order_id = create_purchase_order(db, context=context, legal_entity_id=entity, branch_id=branch,
            supplier_id=supplier, period_key="2026",
            lines=[{"product_id": product, "unit_id": unit, "quantity": Decimal(1), "unit_price": Decimal(1)}])
        submit_purchase_order(db, context=context, order_id=order_id)
        denied = type(context)(request_id=context.request_id, actor_user_id=context.actor_user_id,
            tenant_id=context.tenant_id, tenant_user_id=context.tenant_user_id,
            permissions=context.permissions - {"purchase_order.approve"})
        with pytest.raises(Exception) as exc:
            approve_purchase_order(db, context=denied, order_id=order_id)
        assert getattr(exc.value, "status_code", None) == 403


def _create_sent_po(db, context, tenant, entity, branch, unit, product, supplier, quantity=Decimal(10)):
    _seed_sequence(db, tenant, "PO", "PO-R-", entity=entity, branch=branch)
    order_id = create_purchase_order(db, context=context, legal_entity_id=entity, branch_id=branch,
        supplier_id=supplier, period_key="2026",
        lines=[{"product_id": product, "unit_id": unit, "quantity": quantity, "unit_price": Decimal(10)}])
    submit_purchase_order(db, context=context, order_id=order_id)
    approve_purchase_order(db, context=context, order_id=order_id)
    send_purchase_order(db, context=context, order_id=order_id)
    return order_id


def test_partial_receipt_retry_full_receipt_and_return_reconcile(engine):
    tenant, entity, branch, unit, product, location, *_ = seed(engine)
    context = procurement_ctx(engine, tenant)
    with engine.begin() as db:
        supplier = create_partner(db, context=context, code="GR-"+uuid4().hex[:8],
            name="Receipt Supplier", is_customer=False, is_supplier=True)
        _seed_sequence(db, tenant, "GR", "GR-", entity=entity, branch=branch)
        _seed_sequence(db, tenant, "PRT", "PRT-", entity=entity, branch=branch)
        order_id = _create_sent_po(db, context, tenant, entity, branch, unit, product, supplier)
        line_id = db.execute(text("""SELECT id FROM purchase_order_lines
            WHERE tenant_id=:t AND purchase_order_id=:po"""), {"t": tenant, "po": order_id}).scalar_one()
        first = post_goods_receipt(db, context=context, order_id=order_id, location_id=location,
            idempotency_key="gr-partial", period_key="2026",
            lines=[{"purchase_order_line_id": line_id, "quantity": Decimal(4)}])
        replay = post_goods_receipt(db, context=context, order_id=order_id, location_id=location,
            idempotency_key="gr-partial", period_key="2026",
            lines=[{"purchase_order_line_id": line_id, "quantity": Decimal(4)}])
        assert first == replay
        assert db.execute(text("SELECT status FROM purchase_orders WHERE id=:id"), {"id": order_id}).scalar_one() == "PARTIALLY_RECEIVED"
        post_goods_receipt(db, context=context, order_id=order_id, location_id=location,
            idempotency_key="gr-final", period_key="2026",
            lines=[{"purchase_order_line_id": line_id, "quantity": Decimal(6)}])
        assert db.execute(text("SELECT status FROM purchase_orders WHERE id=:id"), {"id": order_id}).scalar_one() == "RECEIVED"
        returned = post_purchase_return(db, context=context, order_id=order_id, location_id=location,
            idempotency_key="return-1", period_key="2026",
            lines=[{"purchase_order_line_id": line_id, "quantity": Decimal(3)}])
        assert returned
        progress = db.execute(text("""SELECT received_quantity,returned_quantity FROM purchase_order_lines
            WHERE tenant_id=:t AND id=:id"""), {"t": tenant, "id": line_id}).mappings().one()
        assert Decimal(progress["received_quantity"]) == Decimal(10)
        assert Decimal(progress["returned_quantity"]) == Decimal(3)
        assert Decimal(db.execute(text("""SELECT on_hand FROM inventory_balances
            WHERE tenant_id=:t AND product_id=:p AND location_id=:l"""),
            {"t": tenant, "p": product, "l": location}).scalar_one()) == Decimal(7)
        assert db.execute(text("""SELECT count(*) FROM inventory_transactions
            WHERE tenant_id=:t AND source_type='GOODS_RECEIPT'"""), {"t": tenant}).scalar_one() == 2
        assert db.execute(text("""SELECT count(*) FROM inventory_transactions
            WHERE tenant_id=:t AND source_type='PURCHASE_RETURN'"""), {"t": tenant}).scalar_one() == 1


def test_receipt_cannot_exceed_order_and_return_cannot_exceed_received(engine):
    tenant, entity, branch, unit, product, location, *_ = seed(engine)
    context = procurement_ctx(engine, tenant)
    with engine.begin() as db:
        supplier = create_partner(db, context=context, code="CAP-"+uuid4().hex[:8],
            name="Cap Supplier", is_customer=False, is_supplier=True)
        _seed_sequence(db, tenant, "GR", "GR-C-", entity=entity, branch=branch)
        _seed_sequence(db, tenant, "PRT", "PRT-C-", entity=entity, branch=branch)
        order_id = _create_sent_po(db, context, tenant, entity, branch, unit, product, supplier, Decimal(5))
        line_id = db.execute(text("SELECT id FROM purchase_order_lines WHERE purchase_order_id=:po"),
                             {"po": order_id}).scalar_one()
        with pytest.raises(ProcurementError, match="exceeds ordered"):
            post_goods_receipt(db, context=context, order_id=order_id, location_id=location,
                idempotency_key="too-many", period_key="2026",
                lines=[{"purchase_order_line_id": line_id, "quantity": Decimal(6)}])
        post_goods_receipt(db, context=context, order_id=order_id, location_id=location,
            idempotency_key="valid", period_key="2026",
            lines=[{"purchase_order_line_id": line_id, "quantity": Decimal(2)}])
        with pytest.raises(ProcurementError, match="exceeds received"):
            post_purchase_return(db, context=context, order_id=order_id, location_id=location,
                idempotency_key="return-too-many", period_key="2026",
                lines=[{"purchase_order_line_id": line_id, "quantity": Decimal(3)}])
