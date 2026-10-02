from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.application.finance import FinanceError, post_journal
from app.application.numbering import allocate_document_number
from app.domain.security import RequestContext, require_permission


def post_invoice(db: Connection, *, context: RequestContext, invoice_type: str, legal_entity_id: UUID,
                 partner_id: UUID, invoice_date: date, due_date: date, currency_code: str,
                 net_amount: Decimal, tax_amount: Decimal, control_account_id: UUID,
                 counter_account_id: UUID, tax_account_id: UUID | None, period_key: str,
                 source_type: str, source_id: UUID, source_number: str | None,
                 idempotency_key: str) -> UUID:
    permission="ar.post" if invoice_type=="CUSTOMER" else "ap.post";require_permission(context,permission)
    if net_amount<0 or tax_amount<0 or (tax_amount>0 and tax_account_id is None):
        raise FinanceError("invalid invoice amounts or tax account")
    role="is_customer" if invoice_type=="CUSTOMER" else "is_supplier"
    if not db.execute(text(f"SELECT 1 FROM business_partners WHERE tenant_id=:t AND id=:p AND {role}=true AND status='ACTIVE'"),
                      {"t":context.tenant_id,"p":partner_id}).first():
        raise FinanceError("eligible partner not found")
    total=net_amount+tax_amount
    doc_type="CINV" if invoice_type=="CUSTOMER" else "SINV"
    number=allocate_document_number(db,tenant_id=context.tenant_id,document_type=doc_type,period_key=period_key,legal_entity_id=legal_entity_id)
    invoice_id=uuid4()
    if invoice_type=="CUSTOMER":
        lines=[{"account_id":control_account_id,"debit":total},{"account_id":counter_account_id,"credit":net_amount}]
        if tax_amount: lines.append({"account_id":tax_account_id,"credit":tax_amount})
    else:
        lines=[{"account_id":counter_account_id,"debit":net_amount},{"account_id":control_account_id,"credit":total}]
        if tax_amount: lines.append({"account_id":tax_account_id,"debit":tax_amount})
    journal=post_journal(db,context=context,legal_entity_id=legal_entity_id,posting_date=invoice_date,currency_code=currency_code,
        description=f"{invoice_type.title()} invoice {number}",source_module="FINANCE",source_type=doc_type,source_id=invoice_id,
        source_number=number,source_effect="PRIMARY",idempotency_key=idempotency_key,period_key=period_key,lines=lines,permission=permission)
    db.execute(text("""INSERT INTO finance_invoices
      (id,tenant_id,legal_entity_id,invoice_type,invoice_number,partner_id,invoice_date,due_date,currency_code,exchange_rate,
       net_amount,tax_amount,total_amount,settled_amount,status,source_type,source_id,source_number,journal_entry_id,posted_at,created_at)
      VALUES (:id,:t,:e,:type,:number,:partner,:date,:due,:currency,1,:net,:tax,:total,0,'POSTED',:source_type,:source_id,:source_number,:journal,now(),now())"""),
      {"id":invoice_id,"t":context.tenant_id,"e":legal_entity_id,"type":invoice_type,"number":number,"partner":partner_id,
       "date":invoice_date,"due":due_date,"currency":currency_code,"net":net_amount,"tax":tax_amount,"total":total,
       "source_type":source_type,"source_id":source_id,"source_number":source_number,"journal":journal})
    return invoice_id


def post_payment(db: Connection, *, context: RequestContext, payment_type: str, legal_entity_id: UUID,
                 partner_id: UUID, payment_date: date, currency_code: str, amount: Decimal,
                 cash_account_id: UUID, control_account_id: UUID, period_key: str,
                 idempotency_key: str) -> UUID:
    require_permission(context,"payment.post")
    if amount<=0: raise FinanceError("payment amount must be positive")
    number=allocate_document_number(db,tenant_id=context.tenant_id,document_type="RCT" if payment_type=="RECEIPT" else "PAY",
                                    period_key=period_key,legal_entity_id=legal_entity_id)
    payment_id=uuid4()
    lines=([{"account_id":cash_account_id,"debit":amount},{"account_id":control_account_id,"credit":amount}]
           if payment_type=="RECEIPT" else
           [{"account_id":control_account_id,"debit":amount},{"account_id":cash_account_id,"credit":amount}])
    journal=post_journal(db,context=context,legal_entity_id=legal_entity_id,posting_date=payment_date,currency_code=currency_code,
        description=f"{payment_type.title()} {number}",source_module="FINANCE",source_type=payment_type,source_id=payment_id,
        source_number=number,source_effect="PRIMARY",idempotency_key=idempotency_key,period_key=period_key,lines=lines,permission="payment.post")
    db.execute(text("""INSERT INTO finance_payments
      (id,tenant_id,legal_entity_id,payment_type,payment_number,partner_id,payment_date,currency_code,amount,allocated_amount,status,journal_entry_id,created_at)
      VALUES (:id,:t,:e,:type,:number,:partner,:date,:currency,:amount,0,'POSTED',:journal,now())"""),
      {"id":payment_id,"t":context.tenant_id,"e":legal_entity_id,"type":payment_type,"number":number,"partner":partner_id,
       "date":payment_date,"currency":currency_code,"amount":amount,"journal":journal})
    return payment_id


def allocate_payment(db: Connection, *, context: RequestContext, payment_id: UUID, invoice_id: UUID,
                     amount: Decimal) -> None:
    require_permission(context,"payment.manage")
    if amount<=0: raise FinanceError("allocation must be positive")
    payment=db.execute(text("SELECT * FROM finance_payments WHERE tenant_id=:t AND id=:id FOR UPDATE"),
                       {"t":context.tenant_id,"id":payment_id}).mappings().first()
    invoice=db.execute(text("SELECT * FROM finance_invoices WHERE tenant_id=:t AND id=:id FOR UPDATE"),
                       {"t":context.tenant_id,"id":invoice_id}).mappings().first()
    if not payment or not invoice or payment["legal_entity_id"]!=invoice["legal_entity_id"] or payment["partner_id"]!=invoice["partner_id"]:
        raise FinanceError("payment and invoice do not share owner scope")
    expected="CUSTOMER" if payment["payment_type"]=="RECEIPT" else "SUPPLIER"
    if invoice["invoice_type"]!=expected: raise FinanceError("payment type does not match invoice")
    if Decimal(payment["allocated_amount"])+amount>Decimal(payment["amount"]) or Decimal(invoice["settled_amount"])+amount>Decimal(invoice["total_amount"]):
        raise FinanceError("allocation exceeds open amount")
    db.execute(text("INSERT INTO finance_allocations (id,tenant_id,payment_id,invoice_id,amount,created_at) VALUES (:id,:t,:p,:i,:a,now())"),
               {"id":uuid4(),"t":context.tenant_id,"p":payment_id,"i":invoice_id,"a":amount})
    new_p=Decimal(payment["allocated_amount"])+amount;new_i=Decimal(invoice["settled_amount"])+amount
    pstatus="ALLOCATED" if new_p==Decimal(payment["amount"]) else "PARTIALLY_ALLOCATED"
    istatus="SETTLED" if new_i==Decimal(invoice["total_amount"]) else "PARTIALLY_SETTLED"
    db.execute(text("UPDATE finance_payments SET allocated_amount=:a,status=:s WHERE tenant_id=:t AND id=:id"),
               {"a":new_p,"s":pstatus,"t":context.tenant_id,"id":payment_id})
    db.execute(text("UPDATE finance_invoices SET settled_amount=:a,status=:s WHERE tenant_id=:t AND id=:id"),
               {"a":new_i,"s":istatus,"t":context.tenant_id,"id":invoice_id})
