from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from test_phase4_inventory import ctx, seed

from app.application.commercial import (
    EntitlementDenied,
    provision_tenant,
    request_tenant_export,
    require_entitlement,
    transition_subscription,
)
from app.core.config import get_settings


@pytest.fixture
def engine():
    url=get_settings().database_url
    if not url.startswith("postgresql"): pytest.skip("Phase 14 acceptance requires PostgreSQL")
    value=create_engine(url,pool_pre_ping=True)
    try: yield value
    finally: value.dispose()


def commercial_setup(engine):
    tenant,*_=seed(engine);base=ctx(tenant);plan=uuid4()
    with engine.begin() as db:
        db.execute(text("INSERT INTO users (id,email,password_hash,display_name,status,created_at,updated_at) VALUES (:u,:e,'x','Owner','ACTIVE',now(),now())"),{"u":base.actor_user_id,"e":base.actor_user_id.hex+"@commercial.test"})
        db.execute(text("INSERT INTO tenant_users (id,tenant_id,user_id,status,joined_at,created_at,updated_at) VALUES (:tu,:t,:u,'ACTIVE',now(),now(),now())"),{"tu":base.tenant_user_id,"t":tenant,"u":base.actor_user_id})
        db.execute(text("INSERT INTO saas_plans (id,code,name,status,trial_days,retention_days,created_at) VALUES (:id,:code,'Starter','ACTIVE',14,30,now())"),{"id":plan,"code":"STARTER-"+tenant.hex[:8]})
        db.execute(text("INSERT INTO saas_plan_entitlements (id,plan_id,feature_code,limit_value,created_at) VALUES (gen_random_uuid(),:p,'inventory.core',2,now())"),{"p":plan})
    return tenant,base,"STARTER-"+tenant.hex[:8]


def test_repeatable_provisioning_and_limit(engine):
    tenant,_,plan=commercial_setup(engine)
    with engine.begin() as db:
        first=provision_tenant(db,tenant_id=tenant,plan_code=plan);second=provision_tenant(db,tenant_id=tenant,plan_code=plan)
        assert first==second
        require_entitlement(db,tenant_id=tenant,feature_code="inventory.core",period_key="2026-10",increment=2)
        with pytest.raises(EntitlementDenied): require_entitlement(db,tenant_id=tenant,feature_code="inventory.core",period_key="2026-10",increment=1)


def test_entitlement_is_separate_from_rbac(engine):
    tenant,base,plan=commercial_setup(engine)
    allowed=type(base)(request_id=base.request_id,actor_user_id=base.actor_user_id,tenant_id=tenant,
      tenant_user_id=base.tenant_user_id,permissions=frozenset({"inventory.read"}))
    with engine.begin() as db:
        provision_tenant(db,tenant_id=tenant,plan_code=plan)
        require_entitlement(db,tenant_id=tenant,feature_code="inventory.core")
        assert "inventory.read" in allowed.permissions
        db.execute(text("UPDATE saas_subscriptions SET status='SUSPENDED' WHERE tenant_id=:t"),{"t":tenant})
        with pytest.raises(EntitlementDenied): require_entitlement(db,tenant_id=tenant,feature_code="inventory.core")
    no_rbac=type(base)(request_id=base.request_id,actor_user_id=base.actor_user_id,tenant_id=tenant,
      tenant_user_id=base.tenant_user_id,permissions=frozenset())
    with pytest.raises(HTTPException): request_tenant_export_context(no_rbac)


def request_tenant_export_context(context):
    from app.domain.security import require_permission
    require_permission(context,"tenant.export")


def test_cancel_sets_retention_and_export_is_tenant_scoped(engine):
    tenant,base,plan=commercial_setup(engine)
    context=type(base)(request_id=base.request_id,actor_user_id=base.actor_user_id,tenant_id=tenant,
      tenant_user_id=base.tenant_user_id,permissions=frozenset({"subscription.manage","tenant.export"}))
    with engine.begin() as db:
        provision_tenant(db,tenant_id=tenant,plan_code=plan)
        export=request_tenant_export(db,context=context)
        transition_subscription(db,context=context,status="CANCELLED")
        row=db.execute(text("SELECT status,retention_until FROM saas_subscriptions WHERE tenant_id=:t"),{"t":tenant}).one()
        assert row.status=="CANCELLED" and row.retention_until is not None
        assert db.execute(text("SELECT tenant_id FROM saas_exports WHERE id=:id"),{"id":export}).scalar_one()==tenant
