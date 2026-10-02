from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from test_phase12_finance import setup_finance

from app.application.finance import create_account
from app.application.finance_reports import reconcile_subledgers, trial_balance
from app.application.finance_subledger import allocate_payment, post_invoice, post_payment
from app.core.config import get_settings


@pytest.fixture
def engine():
    url=get_settings().database_url
    if not url.startswith("postgresql"): pytest.skip("Phase 12 acceptance requires PostgreSQL")
    value=create_engine(url,pool_pre_ping=True)
    try: yield value
    finally: value.dispose()


def test_ar_invoice_receipt_allocation_reconciles_to_gl(engine):
    tenant,entity,cash,revenue,base=setup_finance(engine)
    context=type(base)(request_id=base.request_id,actor_user_id=base.actor_user_id,tenant_id=tenant,
      tenant_user_id=base.tenant_user_id,permissions=frozenset({"accounting.configure","ar.post","payment.post","payment.manage","financial_report.read","accounting.read"}))
    with engine.begin() as db:
        ar=create_account(db,context=context,legal_entity_id=entity,code="1100",name="AR",account_type="ASSET",is_control=True)
        tax=create_account(db,context=context,legal_entity_id=entity,code="2100",name="VAT Payable",account_type="LIABILITY",is_control=True)
        partner=uuid4()
        db.execute(text("""INSERT INTO business_partners (id,tenant_id,code,name,is_customer,is_supplier,status,created_at,updated_at)
          VALUES (:id,:t,:code,'Customer',true,false,'ACTIVE',now(),now())"""),{"id":partner,"t":tenant,"code":"C-"+partner.hex[:8]})
        for dtype,prefix in [("CINV","CINV-"),("RCT","RCT-")]:
            db.execute(text("""INSERT INTO document_sequences
              (id,tenant_id,document_type,legal_entity_id,branch_id,period_key,prefix,next_value,padding,updated_at)
              VALUES (gen_random_uuid(),:t,:d,:e,NULL,'2026-10',:p,1,6,now())"""),{"t":tenant,"d":dtype,"e":entity,"p":prefix})
        invoice=post_invoice(db,context=context,invoice_type="CUSTOMER",legal_entity_id=entity,partner_id=partner,
          invoice_date=date(2026,10,2),due_date=date(2026,10,31),currency_code="THB",net_amount=Decimal(100),
          tax_amount=Decimal(7),control_account_id=ar,counter_account_id=revenue,tax_account_id=tax,period_key="2026-10",
          source_type="SALES_ORDER",source_id=uuid4(),source_number="SO-1",idempotency_key="cinv-1")
        receipt=post_payment(db,context=context,payment_type="RECEIPT",legal_entity_id=entity,partner_id=partner,
          payment_date=date(2026,10,3),currency_code="THB",amount=Decimal(107),cash_account_id=cash,
          control_account_id=ar,period_key="2026-10",idempotency_key="rct-1")
        before=reconcile_subledgers(db,context=context,legal_entity_id=entity,ar_control_account_id=ar,ap_control_account_id=tax)
        assert before["ar_difference"]==0 and before["ar_subledger"]==Decimal(107)
        allocate_payment(db,context=context,payment_id=receipt,invoice_id=invoice,amount=Decimal(107))
        after=reconcile_subledgers(db,context=context,legal_entity_id=entity,ar_control_account_id=ar,ap_control_account_id=tax)
        assert after["ar_difference"]==0 and after["ar_subledger"]==0
        assert len(trial_balance(db,context=context,legal_entity_id=entity))>=4
