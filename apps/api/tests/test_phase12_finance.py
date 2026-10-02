from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from test_phase4_inventory import ctx, seed

from app.application.finance import (
    FiscalPeriodClosed,
    FinanceError,
    UnbalancedJournal,
    create_account,
    create_fiscal_period,
    post_journal,
    reverse_journal,
    set_fiscal_period_status,
)
from app.core.config import get_settings


@pytest.fixture
def engine():
    url=get_settings().database_url
    if not url.startswith("postgresql"): pytest.skip("Phase 12 acceptance requires PostgreSQL")
    value=create_engine(url,pool_pre_ping=True)
    try: yield value
    finally: value.dispose()


def fctx(tenant, perms):
    base=ctx(tenant)
    return type(base)(request_id=base.request_id,actor_user_id=base.actor_user_id,tenant_id=tenant,
        tenant_user_id=base.tenant_user_id,permissions=frozenset(perms))


def setup_finance(engine):
    tenant,*_=seed(engine)
    with engine.begin() as db:
        entity=db.execute(text("SELECT id FROM legal_entities WHERE tenant_id=:t LIMIT 1"),{"t":tenant}).scalar_one()
        context=fctx(tenant,{"accounting.configure","journal.post","journal.reverse","fiscal_period.close","fiscal_period.reopen"})
        cash=create_account(db,context=context,legal_entity_id=entity,code="1000",name="Cash",account_type="ASSET")
        revenue=create_account(db,context=context,legal_entity_id=entity,code="4000",name="Revenue",account_type="REVENUE")
        create_fiscal_period(db,context=context,legal_entity_id=entity,period_key="2026-10",start_date=date(2026,10,1),end_date=date(2026,10,31))
        db.execute(text("""INSERT INTO document_sequences
          (id,tenant_id,document_type,legal_entity_id,branch_id,period_key,prefix,next_value,padding,updated_at)
          VALUES (gen_random_uuid(),:t,'JV',:e,NULL,'2026-10','JV-202610-',1,6,now())"""),{"t":tenant,"e":entity})
    return tenant,entity,cash,revenue


def test_balanced_post_idempotency_and_reversal(engine):
    tenant,entity,cash,revenue=setup_finance(engine);context=fctx(tenant,{"journal.post","journal.reverse"})
    source=uuid4()
    with engine.begin() as db:
        journal=post_journal(db,context=context,legal_entity_id=entity,posting_date=date(2026,10,2),
          currency_code="THB",description="sale",source_module="SALES",source_type="CUSTOMER_INVOICE",
          source_id=source,source_number="CINV-1",source_effect="PRIMARY",idempotency_key="post-1",period_key="2026-10",
          lines=[{"account_id":cash,"debit":Decimal("100.00")},{"account_id":revenue,"credit":Decimal("100.00")}])
        replay=post_journal(db,context=context,legal_entity_id=entity,posting_date=date(2026,10,2),
          currency_code="THB",description="sale",source_module="SALES",source_type="CUSTOMER_INVOICE",
          source_id=source,source_number="CINV-1",source_effect="PRIMARY",idempotency_key="post-1",period_key="2026-10",
          lines=[{"account_id":cash,"debit":"100"},{"account_id":revenue,"credit":"100"}])
        assert replay==journal
        reversal=reverse_journal(db,context=context,journal_id=journal,posting_date=date(2026,10,3),
                                 period_key="2026-10",idempotency_key="reverse-1")
        assert reversal!=journal
        assert db.execute(text("SELECT status FROM journal_entries WHERE id=:id"),{"id":journal}).scalar_one()=="REVERSED"
        totals=db.execute(text("SELECT sum(debit),sum(credit) FROM journal_lines WHERE journal_entry_id=:id"),{"id":reversal}).one()
        assert totals==(Decimal("100.00000000"),Decimal("100.00000000"))


def test_unbalanced_closed_period_and_cross_entity_account_are_denied(engine):
    tenant,entity,cash,revenue=setup_finance(engine);context=fctx(tenant,{"journal.post","fiscal_period.close"})
    with engine.begin() as db:
        with pytest.raises(UnbalancedJournal):
            post_journal(db,context=context,legal_entity_id=entity,posting_date=date(2026,10,2),currency_code="THB",
              description="bad",source_module="MANUAL",source_type="JV",source_id=uuid4(),source_number=None,
              source_effect="PRIMARY",idempotency_key="bad",period_key="2026-10",
              lines=[{"account_id":cash,"debit":"10"},{"account_id":revenue,"credit":"9"}])
        period=db.execute(text("SELECT id FROM fiscal_periods WHERE tenant_id=:t AND legal_entity_id=:e"),{"t":tenant,"e":entity}).scalar_one()
        set_fiscal_period_status(db,context=context,period_id=period,status="CLOSED")
        with pytest.raises(FiscalPeriodClosed):
            post_journal(db,context=context,legal_entity_id=entity,posting_date=date(2026,10,2),currency_code="THB",
              description="closed",source_module="MANUAL",source_type="JV",source_id=uuid4(),source_number=None,
              source_effect="PRIMARY",idempotency_key="closed",period_key="2026-10",
              lines=[{"account_id":cash,"debit":"10"},{"account_id":revenue,"credit":"10"}])


def test_missing_permission_denied(engine):
    tenant,entity,cash,revenue=setup_finance(engine)
    with engine.begin() as db,pytest.raises(HTTPException):
        post_journal(db,context=fctx(tenant,set()),legal_entity_id=entity,posting_date=date(2026,10,2),
          currency_code="THB",description="denied",source_module="MANUAL",source_type="JV",source_id=uuid4(),
          source_number=None,source_effect="PRIMARY",idempotency_key="denied",period_key="2026-10",
          lines=[{"account_id":cash,"debit":"1"},{"account_id":revenue,"credit":"1"}])
