from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text

from app.application.imports import ImportError, commit_batch, create_batch, validate_batch
from app.application.inventory import StockLine, post_inventory
from app.core.config import get_settings
from app.domain.security import RequestContext


@pytest.fixture
def engine():
    url=get_settings().database_url
    if not url.startswith("postgresql"): pytest.skip("remediation acceptance requires PostgreSQL")
    return create_engine(url)


def seed_product_import(engine):
    now=datetime.now(UTC);tenant,user,membership,unit=uuid4(),uuid4(),uuid4(),uuid4()
    with engine.begin() as db:
        db.execute(text("INSERT INTO tenants(id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at) VALUES(:id,:slug,'T','ACTIVE','th-TH','Asia/Bangkok','THB',:now,:now)"),{"id":tenant,"slug":"rem-"+tenant.hex,"now":now})
        db.execute(text("INSERT INTO users(id,email,password_hash,display_name,status,created_at,updated_at) VALUES(:id,:email,'x','Importer','ACTIVE',:now,:now)"),{"id":user,"email":user.hex+"@example.invalid","now":now})
        db.execute(text("INSERT INTO tenant_users(id,tenant_id,user_id,status,joined_at,created_at,updated_at) VALUES(:id,:t,:u,'ACTIVE',:now,:now,:now)"),{"id":membership,"t":tenant,"u":user,"now":now})
        db.execute(text("INSERT INTO units(id,tenant_id,code,name,precision,status,created_at,updated_at) VALUES(:id,:t,'EA','Each',0,'ACTIVE',:now,:now)"),{"id":unit,"t":tenant,"now":now})
    return tenant,user,membership


def ctx(tenant,user,membership,permissions):
    return RequestContext(uuid4(),user,tenant,membership,frozenset(permissions))


def test_product_import_validate_is_side_effect_free_and_commit_is_replay_safe(engine):
    tenant,user,membership=seed_product_import(engine);context=ctx(tenant,user,membership,{"product.manage"})
    with engine.begin() as db:
        batch=create_batch(db,context=context,import_type="PRODUCT",source_name="products.json",
                           rows=[{"sku":"IMP-1","name":"Imported","base_unit_code":"EA"}])
        result=validate_batch(db,context=context,batch_id=batch)
        assert result=={"valid_rows":1,"error_rows":0}
        assert db.execute(text("SELECT count(*) FROM products WHERE tenant_id=:t AND sku='IMP-1'"),{"t":tenant}).scalar_one()==0
    with engine.begin() as db:
        first=commit_batch(db,context=context,batch_id=batch)
    with engine.begin() as db:
        replay=commit_batch(db,context=context,batch_id=batch)
        assert replay==first
        assert db.execute(text("SELECT count(*) FROM products WHERE tenant_id=:t AND sku='IMP-1'"),{"t":tenant}).scalar_one()==1
        assert db.execute(text("SELECT count(*) FROM audit_logs WHERE tenant_id=:t AND action='import.batch.committed'"),{"t":tenant}).scalar_one()==1
        assert db.execute(text("SELECT count(*) FROM outbox_events WHERE tenant_id=:t AND event_type='import.batch.committed'"),{"t":tenant}).scalar_one()==1


def test_import_batch_is_tenant_hidden(engine):
    t1,u1,m1=seed_product_import(engine);t2,u2,m2=seed_product_import(engine)
    with engine.begin() as db:
        batch=create_batch(db,context=ctx(t1,u1,m1,{"product.manage"}),import_type="PRODUCT",source_name="x.json",
                           rows=[{"sku":"IMP-X","name":"X","base_unit_code":"EA"}])
    with engine.begin() as db, pytest.raises(ImportError):
        validate_batch(db,context=ctx(t2,u2,m2,{"product.manage"}),batch_id=batch)


def test_opening_stock_requires_adjust_not_receive():
    context=RequestContext(uuid4(),uuid4(),uuid4(),uuid4(),frozenset({"inventory.receive"}))
    with pytest.raises(HTTPException) as exc:
        post_inventory(None,context=context,transaction_type="OPENING",legal_entity_id=uuid4(),branch_id=None,
                       lines=[StockLine(uuid4(),uuid4(),uuid4(),__import__("decimal").Decimal("1"))],
                       idempotency_key="permission-only")
    assert exc.value.status_code==403
