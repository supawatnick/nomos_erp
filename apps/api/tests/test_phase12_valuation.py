from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from test_phase12_finance import setup_finance
from test_phase4_inventory import StockLine, post_inventory, seed

from app.application.finance import create_account
from app.application.finance_integration import configure_posting_rule, post_inventory_valuation, set_standard_cost
from app.core.config import get_settings


@pytest.fixture
def engine():
    url=get_settings().database_url
    if not url.startswith("postgresql"): pytest.skip("Phase 12 acceptance requires PostgreSQL")
    value=create_engine(url,pool_pre_ping=True)
    try: yield value
    finally: value.dispose()


def test_inventory_standard_cost_posts_once_and_reconciles(engine):
    tenant,entity,cash,_,base=setup_finance(engine)
    with engine.begin() as db:
        product,unit,location=db.execute(text("""SELECT p.id,p.base_unit_id,l.id FROM products p
          JOIN warehouse_locations l ON l.tenant_id=p.tenant_id JOIN warehouses w ON w.tenant_id=l.tenant_id AND w.id=l.warehouse_id
          WHERE p.tenant_id=:t AND w.legal_entity_id=:e LIMIT 1"""),{"t":tenant,"e":entity}).one()
        context=type(base)(request_id=base.request_id,actor_user_id=base.actor_user_id,tenant_id=tenant,
          tenant_user_id=base.tenant_user_id,permissions=frozenset({"accounting.configure","journal.post","inventory.receive"}))
        inventory=create_account(db,context=context,legal_entity_id=entity,code="1200",name="Inventory",account_type="ASSET",is_control=True)
        clearing=create_account(db,context=context,legal_entity_id=entity,code="2200",name="GR Clearing",account_type="LIABILITY",is_control=True)
        configure_posting_rule(db,context=context,legal_entity_id=entity,source_type="INVENTORY_RECEIVE",
                               debit_account_id=inventory,credit_account_id=clearing)
        set_standard_cost(db,context=context,legal_entity_id=entity,product_id=product,unit_cost=Decimal(25),effective_from=date(2026,10,1))
        tx=post_inventory(db,context=context,transaction_type="RECEIVE",legal_entity_id=entity,branch_id=None,
          lines=[StockLine(product,unit,location,Decimal(4))],idempotency_key="p12-receive",reference="GR-1",reason="valuation")
        journal=post_inventory_valuation(db,context=context,inventory_transaction_id=tx,posting_date=date(2026,10,2),
                                         period_key="2026-10",idempotency_key="p12-value")
        replay=post_inventory_valuation(db,context=context,inventory_transaction_id=tx,posting_date=date(2026,10,2),
                                         period_key="2026-10",idempotency_key="p12-value")
        assert replay==journal
        assert db.execute(text("SELECT amount FROM inventory_valuation_entries WHERE inventory_transaction_id=:id"),{"id":tx}).scalar_one()==Decimal("100.00000000")
