from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text

from app.application.master_data import archive_master
from app.application.inventory import (
    IdempotencyConflict,
    InsufficientStock,
    StockLine,
    post_inventory,
    reconcile_inventory,
    reverse_inventory,
)
from app.core.config import get_settings
from app.domain.security import RequestContext


@pytest.fixture
def engine():
    url=get_settings().database_url
    if not url.startswith("postgresql"):
        pytest.skip("Phase 4 acceptance requires PostgreSQL")
    value=create_engine(url,pool_pre_ping=True)
    try:
        yield value
    finally:
        value.dispose()


def seed(engine):
    now=datetime.now(UTC)
    tenant_id,entity_id,branch_id,unit_id,product_id=uuid4(),uuid4(),uuid4(),uuid4(),uuid4()
    warehouse_id,location_a,location_b=uuid4(),uuid4(),uuid4()
    with engine.begin() as db:
        db.execute(text("INSERT INTO tenants (id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at) VALUES (:id,:slug,'P4','ACTIVE','th-TH','Asia/Bangkok','THB',:now,:now)"),
                   {"id":tenant_id,"slug":"p4-"+tenant_id.hex,"now":now})
        db.execute(text("INSERT INTO legal_entities (id,tenant_id,code,legal_name,country_code,base_currency,timezone,status,created_at,updated_at) VALUES (:id,:tenant,:code,'P4 Legal','TH','THB','Asia/Bangkok','ACTIVE',:now,:now)"),
                   {"id":entity_id,"tenant":tenant_id,"code":"LE-"+entity_id.hex[:8],"now":now})
        db.execute(text("INSERT INTO branches (id,tenant_id,legal_entity_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:entity,:code,'Main','ACTIVE',:now,:now)"),
                   {"id":branch_id,"tenant":tenant_id,"entity":entity_id,"code":"B-"+branch_id.hex[:8],"now":now})
        db.execute(text("INSERT INTO units (id,tenant_id,code,name,precision,status,created_at,updated_at) VALUES (:id,:tenant,'EA','Each',0,'ACTIVE',:now,:now)"),
                   {"id":unit_id,"tenant":tenant_id,"now":now})
        db.execute(text("INSERT INTO products (id,tenant_id,sku,name,product_type,base_unit_id,tracking_type,status,created_at,updated_at) VALUES (:id,:tenant,:sku,'Stock','STOCKABLE',:unit,'NONE','ACTIVE',:now,:now)"),
                   {"id":product_id,"tenant":tenant_id,"sku":"SKU-"+product_id.hex[:8],"unit":unit_id,"now":now})
        db.execute(text("INSERT INTO warehouses (id,tenant_id,legal_entity_id,branch_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:entity,:branch,:code,'WH','ACTIVE',:now,:now)"),
                   {"id":warehouse_id,"tenant":tenant_id,"entity":entity_id,"branch":branch_id,"code":"WH-"+warehouse_id.hex[:8],"now":now})
        for loc,code in ((location_a,"A"),(location_b,"B")):
            db.execute(text("INSERT INTO warehouse_locations (id,tenant_id,warehouse_id,code,name,allow_stock,status,created_at,updated_at) VALUES (:id,:tenant,:wh,:code,:code,true,'ACTIVE',:now,:now)"),
                       {"id":loc,"tenant":tenant_id,"wh":warehouse_id,"code":code+"-"+loc.hex[:6],"now":now})
    return tenant_id,entity_id,branch_id,unit_id,product_id,location_a,location_b


def ctx(tenant_id: UUID) -> RequestContext:
    return RequestContext(request_id=uuid4(),actor_user_id=uuid4(),tenant_id=tenant_id,tenant_user_id=uuid4(),
                          permissions=frozenset({"inventory.read","inventory.receive","inventory.issue","inventory.transfer","inventory.adjust"}))


def post(engine, context, entity, branch, kind, line, key):
    with engine.begin() as db:
        return post_inventory(db,context=context,transaction_type=kind,legal_entity_id=entity,branch_id=branch,
                              lines=[line],idempotency_key=key,reference="phase4-test",reason="acceptance")


def balance(engine, tenant, product, location):
    with engine.connect() as db:
        return Decimal(db.execute(text("SELECT on_hand FROM inventory_balances WHERE tenant_id=:t AND product_id=:p AND location_id=:l"),
                                  {"t":tenant,"p":product,"l":location}).scalar_one())


def test_receive_issue_idempotency_conflict_and_reconciliation(engine):
    tenant,entity,branch,unit,product,a,_=seed(engine)
    context=ctx(tenant)
    line=StockLine(product,unit,a,Decimal(10))
    first=post(engine,context,entity,branch,"RECEIVE",line,"receive-1")
    replay=post(engine,context,entity,branch,"RECEIVE",line,"receive-1")
    assert first==replay and balance(engine,tenant,product,a)==10
    with pytest.raises(IdempotencyConflict):
        post(engine,context,entity,branch,"RECEIVE",StockLine(product,unit,a,Decimal(11)),"receive-1")
    post(engine,context,entity,branch,"ISSUE",StockLine(product,unit,a,Decimal(4)),"issue-1")
    assert balance(engine,tenant,product,a)==6
    with engine.connect() as db:
        assert reconcile_inventory(db,tenant)==[]
        assert db.execute(text("SELECT count(*) FROM audit_logs WHERE tenant_id=:t AND action='inventory.transaction.posted'"),{"t":tenant}).scalar_one()==2
        assert db.execute(text("SELECT count(*) FROM outbox_events WHERE tenant_id=:t AND event_type='inventory.transaction.posted'"),{"t":tenant}).scalar_one()==2


def test_no_negative_stock_and_transfer_atomic(engine):
    tenant,entity,branch,unit,product,a,b=seed(engine)
    context=ctx(tenant)
    post(engine,context,entity,branch,"OPENING",StockLine(product,unit,a,Decimal(8)),"opening-1")
    with pytest.raises(InsufficientStock):
        post(engine,context,entity,branch,"ISSUE",StockLine(product,unit,a,Decimal(9)),"issue-too-much")
    assert balance(engine,tenant,product,a)==8
    post(engine,context,entity,branch,"TRANSFER",StockLine(product,unit,a,Decimal(3),destination_location_id=b),"transfer-1")
    assert balance(engine,tenant,product,a)==5
    assert balance(engine,tenant,product,b)==3


def test_adjustment_and_reversal_are_linked_and_reconcile(engine):
    tenant,entity,branch,unit,product,a,_=seed(engine)
    context=ctx(tenant)
    original=post(engine,context,entity,branch,"RECEIVE",StockLine(product,unit,a,Decimal(7)),"receive-reverse")
    with engine.begin() as db:
        reversal=reverse_inventory(db,context=context,transaction_id=original,idempotency_key="reverse-1",reason="mistake")
    assert balance(engine,tenant,product,a)==0
    with engine.connect() as db:
        row=db.execute(text("SELECT reversed_by_id FROM inventory_transactions WHERE tenant_id=:t AND id=:id"),
                       {"t":tenant,"id":original}).scalar_one()
        linked=db.execute(text("SELECT reversal_of_id FROM inventory_transactions WHERE tenant_id=:t AND id=:id"),
                          {"t":tenant,"id":reversal}).scalar_one()
        assert row==reversal and linked==original
        assert reconcile_inventory(db,tenant)==[]
    post(engine,context,entity,branch,"ADJUST",StockLine(product,unit,a,Decimal(2),adjustment_direction=1),"adjust-plus")
    post(engine,context,entity,branch,"ADJUST",StockLine(product,unit,a,Decimal(1),adjustment_direction=-1),"adjust-minus")
    assert balance(engine,tenant,product,a)==1


def test_cross_tenant_location_reference_is_rejected(engine):
    t1,e1,b1,u1,p1,a1,_=seed(engine)
    t2,_,_,_,_,a2,_=seed(engine)
    assert t1!=t2
    with pytest.raises(ValueError):
        post(engine,ctx(t1),e1,b1,"RECEIVE",StockLine(p1,u1,a2,Decimal(1)),"cross-tenant")
    assert balance_missing(engine,t1,p1,a1)


def balance_missing(engine, tenant, product, location):
    with engine.connect() as db:
        return db.execute(text("SELECT count(*) FROM inventory_balances WHERE tenant_id=:t AND product_id=:p AND location_id=:l"),
                          {"t":tenant,"p":product,"l":location}).scalar_one()==0


def test_concurrent_issue_cannot_oversell(engine):
    tenant,entity,branch,unit,product,a,_=seed(engine)
    context=ctx(tenant)
    post(engine,context,entity,branch,"OPENING",StockLine(product,unit,a,Decimal(10)),"concurrent-opening")

    def issue(key):
        try:
            post(engine,context,entity,branch,"ISSUE",StockLine(product,unit,a,Decimal(7)),key)
            return "posted"
        except InsufficientStock:
            return "insufficient"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(issue,["concurrent-a","concurrent-b"]))
    assert sorted(results)==["insufficient","posted"]
    assert balance(engine,tenant,product,a)==3
    with engine.connect() as db:
        assert reconcile_inventory(db,tenant)==[]


def test_concurrent_same_idempotency_key_creates_one_effect(engine):
    tenant,entity,branch,unit,product,a,_=seed(engine)
    context=ctx(tenant)
    line=StockLine(product,unit,a,Decimal(5))

    def receive(_):
        try:
            return str(post(engine,context,entity,branch,"RECEIVE",line,"same-key"))
        except IdempotencyConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(receive,[1,2]))
    assert balance(engine,tenant,product,a)==5
    assert len([x for x in results if x!="conflict"])>=1
    with engine.connect() as db:
        count=db.execute(text("SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t AND idempotency_key='same-key'"),{"t":tenant}).scalar_one()
        assert count==1


def test_stock_bearing_location_cannot_archive(engine):
    tenant,entity,branch,unit,product,a,_=seed(engine)
    context=ctx(tenant)
    post(engine,context,entity,branch,"OPENING",StockLine(product,unit,a,Decimal(2)),"archive-opening")
    with engine.begin() as db, pytest.raises(ValueError, match="stock-bearing location"):
        archive_master(db,context=context,resource="location",resource_id=a)
