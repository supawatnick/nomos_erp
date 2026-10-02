from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from test_phase4_inventory import ctx, seed

from app.application.crm import CRMError, add_activity, add_address, add_contact, create_lead, create_opportunity, create_partner, transition_lead
from app.core.config import get_settings

@pytest.fixture
def engine():
    url=get_settings().database_url
    if not url.startswith("postgresql"): pytest.skip("Phase 7 acceptance requires PostgreSQL")
    value=create_engine(url,pool_pre_ping=True)
    try: yield value
    finally: value.dispose()

def crm_ctx(tenant):
    base=ctx(tenant)
    return type(base)(request_id=base.request_id,actor_user_id=base.actor_user_id,tenant_id=base.tenant_id,
        tenant_user_id=base.tenant_user_id,permissions=base.permissions|frozenset({"partner.read","partner.manage","crm.read","crm.manage"}))

def test_partner_can_be_customer_and_supplier_with_contact_address(engine):
    tenant,*_=seed(engine);context=crm_ctx(tenant)
    with engine.begin() as db:
        pid=create_partner(db,context=context,code="BP-"+uuid4().hex[:8],name="Dual Partner",is_customer=True,is_supplier=True)
        cid=add_contact(db,context=context,partner_id=pid,name="Primary",email="primary@example.test",is_primary=True)
        aid=add_address(db,context=context,partner_id=pid,address_type="BILLING",line1="1 Test Road",is_primary=True)
    with engine.connect() as db:
        p=db.execute(text("SELECT is_customer,is_supplier FROM business_partners WHERE tenant_id=:t AND id=:id"),{"t":tenant,"id":pid}).mappings().one()
        assert p["is_customer"] and p["is_supplier"]
        assert db.execute(text("SELECT count(*) FROM partner_contacts WHERE tenant_id=:t AND id=:id"),{"t":tenant,"id":cid}).scalar_one()==1
        assert db.execute(text("SELECT count(*) FROM partner_addresses WHERE tenant_id=:t AND id=:id"),{"t":tenant,"id":aid}).scalar_one()==1

def test_partner_requires_role(engine):
    tenant,*_=seed(engine);context=crm_ctx(tenant)
    with engine.begin() as db,pytest.raises(CRMError):
        create_partner(db,context=context,code="NONE-"+uuid4().hex[:8],name="No Role",is_customer=False,is_supplier=False)

def test_cross_tenant_partner_contact_is_hidden(engine):
    t1,*_=seed(engine);t2,*_=seed(engine);c1=crm_ctx(t1);c2=crm_ctx(t2)
    with engine.begin() as db: pid=create_partner(db,context=c1,code="T1-"+uuid4().hex[:8],name="Tenant One",is_customer=True,is_supplier=False)
    with engine.begin() as db,pytest.raises(CRMError):
        add_contact(db,context=c2,partner_id=pid,name="Leak")

def test_lead_lifecycle_opportunity_activity_and_no_sales_documents(engine):
    tenant,*_=seed(engine);context=crm_ctx(tenant)
    with engine.begin() as db:
        lead=create_lead(db,context=context,lead_number="LD-"+uuid4().hex[:8],name="Prospect",company_name="Prospect Co")
        transition_lead(db,context=context,lead_id=lead,status="QUALIFIED")
        opp=create_opportunity(db,context=context,opportunity_number="OP-"+uuid4().hex[:8],name="ERP Opportunity",
            lead_id=lead,estimated_amount=Decimal("250000.00"),currency_code="THB")
        activity=add_activity(db,context=context,activity_type="NOTE",subject="Discovery",note="Needs inventory and purchasing",lead_id=lead,opportunity_id=opp)
    with engine.connect() as db:
        assert db.execute(text("SELECT status FROM crm_leads WHERE tenant_id=:t AND id=:id"),{"t":tenant,"id":lead}).scalar_one()=="QUALIFIED"
        assert db.execute(text("SELECT estimated_amount FROM crm_opportunities WHERE tenant_id=:t AND id=:id"),{"t":tenant,"id":opp}).scalar_one()==Decimal("250000.00000000")
        assert db.execute(text("SELECT count(*) FROM crm_activities WHERE tenant_id=:t AND id=:id"),{"t":tenant,"id":activity}).scalar_one()==1
        # Phase 7 has CRM intent only; no QT/SO/PO tables are introduced by migration 0007.
        tables=set(db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'")).scalars())
        assert "quotations" not in tables and "sales_orders" not in tables and "purchase_orders" not in tables
