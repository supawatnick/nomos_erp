from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from test_phase4_inventory import balance, ctx, seed
from test_phase4_inventory import engine as postgres_engine

from app.application.inventory import StockLine, post_inventory, reconcile_inventory
from app.application.inventory_operations import (
    InventoryOperationsError,
    create_stock_count,
    post_stock_count,
    record_count,
    reorder_status,
    upsert_reorder_policy,
)


def phase6_ctx(tenant):
    base=ctx(tenant)
    return type(base)(request_id=base.request_id,actor_user_id=base.actor_user_id,tenant_id=base.tenant_id,
        tenant_user_id=base.tenant_user_id,permissions=base.permissions | frozenset({
            "inventory.count","inventory.count.post","inventory.reorder.manage","inventory.report"
        }))


def opening(engine,context,entity,branch,product,unit,location,qty):
    with engine.begin() as db:
        post_inventory(db,context=context,transaction_type="OPENING",legal_entity_id=entity,branch_id=branch,
            lines=[StockLine(product,unit,location,Decimal(qty))],idempotency_key="p6-open-"+uuid4().hex)


def warehouse_for(engine,tenant,location):
    with engine.connect() as db:
        return db.execute(text("SELECT warehouse_id FROM warehouse_locations WHERE tenant_id=:t AND id=:l"),
                          {"t":tenant,"l":location}).scalar_one()


def test_stock_count_variance_posts_through_inventory_and_reconciles(postgres_engine):
    engine=postgres_engine
    tenant,entity,branch,unit,product,a,_=seed(engine);context=phase6_ctx(tenant)
    opening(engine,context,entity,branch,product,unit,a,10);warehouse=warehouse_for(engine,tenant,a)
    with engine.begin() as db:
        count_id=create_stock_count(db,context=context,legal_entity_id=entity,warehouse_id=warehouse,count_number="COUNT-"+uuid4().hex[:8])
    with engine.connect() as db:
        line=db.execute(text("SELECT id,system_quantity FROM stock_count_lines WHERE tenant_id=:t AND stock_count_id=:c"),
                        {"t":tenant,"c":count_id}).mappings().one()
    assert Decimal(line["system_quantity"])==10
    with engine.begin() as db:
        record_count(db,context=context,count_id=count_id,lines=[(line["id"],Decimal(7))])
        tx=post_stock_count(db,context=context,count_id=count_id,idempotency_key="count-post-"+uuid4().hex)
    assert tx is not None and balance(engine,tenant,product,a)==7
    with engine.connect() as db:
        source=db.execute(text("SELECT source_type,source_id,transaction_type FROM inventory_transactions WHERE tenant_id=:t AND id=:id"),
                          {"t":tenant,"id":tx}).mappings().one()
        assert source["source_type"]=="STOCK_COUNT" and source["source_id"]==count_id and source["transaction_type"]=="ADJUST"
        assert reconcile_inventory(db,tenant)==[]


def test_stock_count_post_is_replay_safe_and_history_is_locked(postgres_engine):
    engine=postgres_engine
    tenant,entity,branch,unit,product,a,_=seed(engine);context=phase6_ctx(tenant)
    opening(engine,context,entity,branch,product,unit,a,4);warehouse=warehouse_for(engine,tenant,a)
    with engine.begin() as db:
        cid=create_stock_count(db,context=context,legal_entity_id=entity,warehouse_id=warehouse,count_number="COUNT-"+uuid4().hex[:8])
        line=db.execute(text("SELECT id FROM stock_count_lines WHERE tenant_id=:t AND stock_count_id=:c"),{"t":tenant,"c":cid}).scalar_one()
        record_count(db,context=context,count_id=cid,lines=[(line,Decimal(5))])
        first=post_stock_count(db,context=context,count_id=cid,idempotency_key="count-replay")
    with engine.begin() as db:
        replay=post_stock_count(db,context=context,count_id=cid,idempotency_key="count-replay")
        with pytest.raises(InventoryOperationsError):
            record_count(db,context=context,count_id=cid,lines=[(line,Decimal(9))])
    assert first==replay and balance(engine,tenant,product,a)==5


def test_reorder_signal_does_not_create_procurement_document(postgres_engine):
    engine=postgres_engine
    tenant,entity,branch,unit,product,a,_=seed(engine);context=phase6_ctx(tenant)
    opening(engine,context,entity,branch,product,unit,a,2)
    with engine.begin() as db:
        policy=upsert_reorder_policy(db,context=context,product_id=product,location_id=a,reorder_point=Decimal(3),target_quantity=Decimal(10))
        rows=reorder_status(db,tenant)
    row=next(x for x in rows if x["id"]==policy)
    assert Decimal(row["on_hand"])==2 and Decimal(row["suggested_quantity"])==8
    with engine.connect() as db:
        assert db.execute(text("SELECT count(*) FROM inventory_transactions WHERE tenant_id=:t"),{"t":tenant}).scalar_one()==1


def test_cross_tenant_reorder_reference_is_rejected(postgres_engine):
    engine=postgres_engine
    t1,_,_,_,p1,a1,_=seed(engine);t2,_,_,_,_,a2,_=seed(engine);context=phase6_ctx(t1)
    assert t1!=t2 and a1!=a2
    with engine.begin() as db, pytest.raises(InventoryOperationsError):
        upsert_reorder_policy(db,context=context,product_id=p1,location_id=a2,reorder_point=Decimal(1),target_quantity=Decimal(2))
