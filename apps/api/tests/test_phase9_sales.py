from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from test_phase4_inventory import ctx, seed
from test_phase8_procurement import _seed_sequence

from app.application.crm import create_partner
from app.application.inventory import StockLine, post_inventory
from app.application.sales import (
    SalesError,
    accept_quotation,
    confirm_order,
    create_quotation,
    post_delivery,
    post_sales_return,
    reserve_order,
    revise_quotation,
    send_quotation,
)
from app.core.config import get_settings


@pytest.fixture
def engine():
    url=get_settings().database_url
    if not url.startswith("postgresql"):pytest.skip("Phase 9 acceptance requires PostgreSQL")
    value=create_engine(url,pool_pre_ping=True)
    try:yield value
    finally:value.dispose()


def sales_ctx(engine,tenant):
    base=ctx(tenant);now=__import__("datetime").datetime.now(__import__("datetime").UTC)
    with engine.begin() as db:
        db.execute(text("INSERT INTO users (id,email,password_hash,display_name,status,created_at,updated_at) VALUES (:id,:email,'x','Sales User','ACTIVE',:now,:now)"),
            {"id":base.actor_user_id,"email":f"s9-{base.actor_user_id.hex}@example.test","now":now})
        db.execute(text("INSERT INTO tenant_users (id,tenant_id,user_id,status,joined_at,created_at,updated_at) VALUES (:id,:t,:u,'ACTIVE',:now,:now,:now)"),
            {"id":base.tenant_user_id,"t":tenant,"u":base.actor_user_id,"now":now})
    permissions=base.permissions|frozenset({"partner.manage","sales.read","quotation.manage","quotation.transition","sales_order.manage","sales_order.override","sales.reserve","sales.fulfill","sales.override","inventory.receive"})
    return type(base)(request_id=base.request_id,actor_user_id=base.actor_user_id,tenant_id=base.tenant_id,tenant_user_id=base.tenant_user_id,permissions=permissions)


def _qt(db,context,tenant,entity,branch,unit,product,customer,qty=Decimal(10)):
    _seed_sequence(db,tenant,"QT","QT-",entity=entity,branch=branch)
    return create_quotation(db,context=context,legal_entity_id=entity,branch_id=branch,customer_id=customer,
        valid_until=datetime.now(UTC).date()+timedelta(days=7),period_key="2026",
        lines=[{"product_id":product,"unit_id":unit,"quantity":qty,"unit_price":Decimal("100.25"),"discount_amount":Decimal("2.50"),"tax_amount":Decimal("7.00")}])


def test_quotation_revision_acceptance_preserves_snapshot_and_has_no_stock_effect(engine):
    tenant,entity,branch,unit,product,_location,*_=seed(engine);context=sales_ctx(engine,tenant)
    with engine.begin() as db:
        customer=create_partner(db,context=context,code="CUS-"+uuid4().hex[:8],name="Customer",is_customer=True,is_supplier=False)
        _seed_sequence(db,tenant,"SO","SO-",entity=entity,branch=branch)
        before=db.execute(text("SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t"),{"t":tenant}).scalar_one()
        qid=_qt(db,context,tenant,entity,branch,unit,product,customer)
        send_quotation(db,context=context,quotation_id=qid)
        revise_quotation(db,context=context,quotation_id=qid,valid_until=datetime.now(UTC).date()+timedelta(days=10),
            lines=[{"product_id":product,"unit_id":unit,"quantity":Decimal(8),"unit_price":Decimal(110)}])
        send_quotation(db,context=context,quotation_id=qid)
        so=accept_quotation(db,context=context,quotation_id=qid,accepted_by="Customer Buyer")
        after=db.execute(text("SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t"),{"t":tenant}).scalar_one()
        assert before==after
        q=db.execute(text("SELECT status,current_revision,accepted_revision FROM sales_quotations WHERE id=:id"),{"id":qid}).mappings().one()
        order=db.execute(text("SELECT source_quotation_id,source_quotation_revision,status FROM sales_orders WHERE id=:id"),{"id":so}).mappings().one()
        assert (q["status"],q["current_revision"],q["accepted_revision"])==("ACCEPTED",2,2)
        assert order["source_quotation_id"]==qid and order["source_quotation_revision"]==2 and order["status"]=="DRAFT"
        assert db.execute(text("SELECT count(*) FROM sales_quotation_revisions WHERE quotation_id=:id"),{"id":qid}).scalar_one()==2


def test_expired_quotation_cannot_be_accepted(engine):
    tenant,entity,branch,unit,product,*_=seed(engine);context=sales_ctx(engine,tenant)
    with engine.begin() as db:
        customer=create_partner(db,context=context,code="EXP-"+uuid4().hex[:8],name="Expired Customer",is_customer=True,is_supplier=False)
        _seed_sequence(db,tenant,"QT","QT-E-",entity=entity,branch=branch)
        qid=create_quotation(db,context=context,legal_entity_id=entity,branch_id=branch,customer_id=customer,
            valid_until=datetime.now(UTC).date()-timedelta(days=1),period_key="2026",
            lines=[{"product_id":product,"unit_id":unit,"quantity":Decimal(1),"unit_price":Decimal(1)}])
        with pytest.raises(SalesError,match="expired"):send_quotation(db,context=context,quotation_id=qid)


def test_reservation_available_partial_delivery_retry_return_and_status(engine):
    tenant,entity,branch,unit,product,location,*_=seed(engine);context=sales_ctx(engine,tenant)
    with engine.begin() as db:
        customer=create_partner(db,context=context,code="FUL-"+uuid4().hex[:8],name="Fulfillment Customer",is_customer=True,is_supplier=False)
        _seed_sequence(db,tenant,"SO","SO-F-",entity=entity,branch=branch);_seed_sequence(db,tenant,"DL","DL-",entity=entity,branch=branch);_seed_sequence(db,tenant,"SRT","SRT-",entity=entity,branch=branch)
        qid=_qt(db,context,tenant,entity,branch,unit,product,customer);send_quotation(db,context=context,quotation_id=qid)
        so=accept_quotation(db,context=context,quotation_id=qid,accepted_by="Buyer");confirm_order(db,context=context,order_id=so)
        post_inventory(db,context=context,transaction_type="RECEIVE",legal_entity_id=entity,branch_id=branch,
            lines=[StockLine(product,unit,location,Decimal(10))],idempotency_key="sales-seed")
        line=db.execute(text("SELECT id FROM sales_order_lines WHERE sales_order_id=:so"),{"so":so}).scalar_one()
        reserve_order(db,context=context,order_id=so,location_id=location,lines=[{"sales_order_line_id":line,"quantity":Decimal(6)}])
        on_hand=db.execute(text("SELECT on_hand FROM inventory_balances WHERE tenant_id=:t AND product_id=:p AND location_id=:l"),{"t":tenant,"p":product,"l":location}).scalar_one()
        assert Decimal(on_hand)==Decimal(10)
        first=post_delivery(db,context=context,order_id=so,location_id=location,idempotency_key="delivery-1",period_key="2026",
            lines=[{"sales_order_line_id":line,"quantity":Decimal(4)}])
        replay=post_delivery(db,context=context,order_id=so,location_id=location,idempotency_key="delivery-1",period_key="2026",
            lines=[{"sales_order_line_id":line,"quantity":Decimal(4)}])
        assert first==replay
        progress=db.execute(text("SELECT reserved_quantity,delivered_quantity FROM sales_order_lines WHERE id=:id"),{"id":line}).mappings().one()
        assert Decimal(progress["reserved_quantity"])==Decimal(2) and Decimal(progress["delivered_quantity"])==Decimal(4)
        assert db.execute(text("SELECT status FROM sales_orders WHERE id=:id"),{"id":so}).scalar_one()=="PARTIALLY_FULFILLED"
        returned=post_sales_return(db,context=context,order_id=so,location_id=location,idempotency_key="return-1",period_key="2026",
            lines=[{"sales_order_line_id":line,"quantity":Decimal(1)}])
        assert returned
        balance=db.execute(text("SELECT on_hand FROM inventory_balances WHERE tenant_id=:t AND product_id=:p AND location_id=:l"),{"t":tenant,"p":product,"l":location}).scalar_one()
        assert Decimal(balance)==Decimal(7)
        assert db.execute(text("SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t AND source_type='SALES_DELIVERY'"),{"t":tenant}).scalar_one()==1


def test_reservation_rejects_over_available_and_cross_tenant_customer(engine):
    t1,e1,b1,u1,p1,l1,*_=seed(engine);t2,*_=seed(engine);c1=sales_ctx(engine,t1);c2=sales_ctx(engine,t2)
    with engine.begin() as db:
        foreign=create_partner(db,context=c2,code="FOREIGN-"+uuid4().hex[:8],name="Foreign",is_customer=True,is_supplier=False)
        _seed_sequence(db,t1,"QT","QT-X-",entity=e1,branch=b1)
        with pytest.raises(SalesError,match="not found"):
            create_quotation(db,context=c1,legal_entity_id=e1,branch_id=b1,customer_id=foreign,period_key="2026",
                lines=[{"product_id":p1,"unit_id":u1,"quantity":Decimal(1),"unit_price":Decimal(1)}])
        local=create_partner(db,context=c1,code="LOCAL-"+uuid4().hex[:8],name="Local",is_customer=True,is_supplier=False)
        _seed_sequence(db,t1,"SO","SO-X-",entity=e1,branch=b1)
        qid=create_quotation(db,context=c1,legal_entity_id=e1,branch_id=b1,customer_id=local,period_key="2026",
            lines=[{"product_id":p1,"unit_id":u1,"quantity":Decimal(2),"unit_price":Decimal(1)}])
        send_quotation(db,context=c1,quotation_id=qid);so=accept_quotation(db,context=c1,quotation_id=qid,accepted_by="Buyer");confirm_order(db,context=c1,order_id=so)
        line=db.execute(text("SELECT id FROM sales_order_lines WHERE sales_order_id=:so"),{"so":so}).scalar_one()
        with pytest.raises(SalesError,match="insufficient available"):
            reserve_order(db,context=c1,order_id=so,location_id=l1,lines=[{"sales_order_line_id":line,"quantity":Decimal(1)}])


def test_release_reservation_restores_available_and_records_timeline(engine):
    tenant,entity,branch,unit,product,location,*_=seed(engine);context=sales_ctx(engine,tenant)
    with engine.begin() as db:
        customer=create_partner(db,context=context,code="REL-"+uuid4().hex[:8],name="Release Customer",is_customer=True,is_supplier=False)
        _seed_sequence(db,tenant,"SO","SO-REL-",entity=entity,branch=branch)
        qid=_qt(db,context,tenant,entity,branch,unit,product,customer,Decimal(3));send_quotation(db,context=context,quotation_id=qid)
        so=accept_quotation(db,context=context,quotation_id=qid,accepted_by="Buyer");confirm_order(db,context=context,order_id=so)
        post_inventory(db,context=context,transaction_type="RECEIVE",legal_entity_id=entity,branch_id=branch,
            lines=[StockLine(product,unit,location,Decimal(3))],idempotency_key="release-seed")
        line=db.execute(text("SELECT id FROM sales_order_lines WHERE sales_order_id=:so"),{"so":so}).scalar_one()
        reserve_order(db,context=context,order_id=so,location_id=location,lines=[{"sales_order_line_id":line,"quantity":Decimal(2)}])
        release_reservations(db,context=context,order_id=so)
        assert Decimal(db.execute(text("SELECT reserved_quantity FROM sales_order_lines WHERE id=:id"),{"id":line}).scalar_one())==Decimal(0)
        assert db.execute(text("SELECT status FROM sales_orders WHERE id=:id"),{"id":so}).scalar_one()=="CONFIRMED"
        events=db.execute(text("SELECT event_type FROM sales_order_events WHERE sales_order_id=:so ORDER BY occurred_at,id"),{"so":so}).scalars().all()
        assert "CONFIRMED" in events and "RESERVATION" in events and "RESERVATION_RELEASED" in events
