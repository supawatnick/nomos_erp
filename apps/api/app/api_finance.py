from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from app.api_master import trusted_context
from app.application.finance import (
    FinanceError,
    UnbalancedJournal,
    create_account,
    create_fiscal_period,
    post_journal,
    reverse_journal,
    set_fiscal_period_status,
)
from app.application.finance_subledger import allocate_payment, post_invoice, post_payment
from app.core.config import get_settings
from app.domain.security import require_permission

router=APIRouter(prefix="/api/v1/finance",tags=["finance"])
def _engine(): return create_engine(get_settings().database_url,pool_pre_ping=True)
def _ctx(r,a,t): return trusted_context(r,a,t)

class AccountIn(BaseModel):
    legal_entity_id: UUID;code:str=Field(min_length=1,max_length=40);name:str;account_type:str;currency_code:str|None=None;is_control:bool=False
class PeriodIn(BaseModel):
    legal_entity_id:UUID;period_key:str;start_date:date;end_date:date
class JournalLineIn(BaseModel):
    account_id:UUID;description:str|None=None;debit:Decimal=Decimal(0);credit:Decimal=Decimal(0)
class JournalIn(BaseModel):
    legal_entity_id:UUID;posting_date:date;currency_code:str;description:str;source_type:str="MANUAL_JOURNAL";source_id:UUID
    source_number:str|None=None;period_key:str;lines:list[JournalLineIn]
class InvoiceIn(BaseModel):
    invoice_type:str;legal_entity_id:UUID;partner_id:UUID;invoice_date:date;due_date:date;currency_code:str
    net_amount:Decimal;tax_amount:Decimal=Decimal(0);control_account_id:UUID;counter_account_id:UUID;tax_account_id:UUID|None=None
    period_key:str;source_type:str;source_id:UUID;source_number:str|None=None
class PaymentIn(BaseModel):
    payment_type:str;legal_entity_id:UUID;partner_id:UUID;payment_date:date;currency_code:str;amount:Decimal
    cash_account_id:UUID;control_account_id:UUID;period_key:str
class AllocationIn(BaseModel): invoice_id:UUID;amount:Decimal

def _key(value:str|None):
    if not value: raise HTTPException(422,detail={"code":"VALIDATION_FAILED","message":"Idempotency-Key required"})
    return value

@router.get("/accounts")
def accounts(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id);require_permission(c,"accounting.read")
    with _engine().connect() as db: rows=db.execute(text("SELECT id,legal_entity_id,code,name,account_type,currency_code,is_control,status FROM finance_accounts WHERE tenant_id=:t ORDER BY code"),{"t":c.tenant_id}).mappings().all()
    return {"data":[{**dict(x),"id":str(x["id"]),"legal_entity_id":str(x["legal_entity_id"])} for x in rows]}
@router.post("/accounts",status_code=201)
def account_create(payload:AccountIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    with _engine().begin() as db: value=create_account(db,context=c,**payload.model_dump())
    return {"data":{"id":str(value)}}
@router.get("/periods")
def periods(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id);require_permission(c,"accounting.read")
    with _engine().connect() as db: rows=db.execute(text("SELECT id,legal_entity_id,period_key,start_date,end_date,status FROM fiscal_periods WHERE tenant_id=:t ORDER BY start_date DESC"),{"t":c.tenant_id}).mappings().all()
    return {"data":[{**dict(x),"id":str(x["id"]),"legal_entity_id":str(x["legal_entity_id"]),"start_date":x["start_date"].isoformat(),"end_date":x["end_date"].isoformat()} for x in rows]}

@router.get("/journals")
def journals(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id);require_permission(c,"accounting.read")
    with _engine().connect() as db: rows=db.execute(text("SELECT id,journal_number,legal_entity_id,posting_date,currency_code,description,status,source_type,source_number FROM journal_entries WHERE tenant_id=:t ORDER BY posting_date DESC,created_at DESC LIMIT 200"),{"t":c.tenant_id}).mappings().all()
    return {"data":[{**dict(x),"id":str(x["id"]),"legal_entity_id":str(x["legal_entity_id"]),"posting_date":x["posting_date"].isoformat()} for x in rows]}

@router.get("/invoices")
def invoices(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id);require_permission(c,"accounting.read")
    with _engine().connect() as db: rows=db.execute(text("SELECT id,invoice_number,invoice_type,partner_id,invoice_date,due_date,currency_code,total_amount,(total_amount-settled_amount) AS open_amount,status FROM finance_invoices WHERE tenant_id=:t ORDER BY invoice_date DESC,created_at DESC LIMIT 200"),{"t":c.tenant_id}).mappings().all()
    return {"data":[{**dict(x),"id":str(x["id"]),"partner_id":str(x["partner_id"]),"invoice_date":x["invoice_date"].isoformat(),"due_date":x["due_date"].isoformat(),"total_amount":str(x["total_amount"]),"open_amount":str(x["open_amount"])} for x in rows]}

@router.get("/payments")
def payments(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id);require_permission(c,"accounting.read")
    with _engine().connect() as db: rows=db.execute(text("SELECT id,payment_number,payment_type,partner_id,payment_date,currency_code,amount,(amount-allocated_amount) AS unallocated_amount,status FROM finance_payments WHERE tenant_id=:t ORDER BY payment_date DESC,created_at DESC LIMIT 200"),{"t":c.tenant_id}).mappings().all()
    return {"data":[{**dict(x),"id":str(x["id"]),"partner_id":str(x["partner_id"]),"payment_date":x["payment_date"].isoformat(),"amount":str(x["amount"]),"unallocated_amount":str(x["unallocated_amount"])} for x in rows]}

@router.post("/periods",status_code=201)
def period_create(payload:PeriodIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    with _engine().begin() as db: value=create_fiscal_period(db,context=c,**payload.model_dump())
    return {"data":{"id":str(value),"status":"OPEN"}}
@router.post("/periods/{period_id}/{status}")
def period_status(period_id:UUID,status:str,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    with _engine().begin() as db: set_fiscal_period_status(db,context=c,period_id=period_id,status=status.upper())
    return {"data":{"id":str(period_id),"status":status.upper()}}
@router.post("/journals",status_code=201)
def journal_post(payload:JournalIn,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    try:
      with _engine().begin() as db: value=post_journal(db,context=c,source_module="FINANCE",source_effect="PRIMARY",idempotency_key=_key(idempotency_key),lines=[x.model_dump() for x in payload.lines],**payload.model_dump(exclude={"lines"}))
    except UnbalancedJournal as e: raise HTTPException(422,detail={"code":"UNBALANCED_JOURNAL","message":str(e)}) from e
    except FinanceError as e: raise HTTPException(409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(e)}) from e
    return {"data":{"id":str(value),"status":"POSTED"}}
@router.post("/journals/{journal_id}/reverse",status_code=201)
def journal_reverse(journal_id:UUID,posting_date:date,period_key:str,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    with _engine().begin() as db: value=reverse_journal(db,context=c,journal_id=journal_id,posting_date=posting_date,period_key=period_key,idempotency_key=_key(idempotency_key))
    return {"data":{"id":str(value),"status":"POSTED"}}
@router.post("/invoices",status_code=201)
def invoice_post(payload:InvoiceIn,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    with _engine().begin() as db: value=post_invoice(db,context=c,idempotency_key=_key(idempotency_key),**payload.model_dump())
    return {"data":{"id":str(value),"status":"POSTED"}}
@router.post("/payments",status_code=201)
def payment_post(payload:PaymentIn,request:Request,idempotency_key:str|None=Header(default=None,alias="Idempotency-Key"),authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    with _engine().begin() as db: value=post_payment(db,context=c,idempotency_key=_key(idempotency_key),**payload.model_dump())
    return {"data":{"id":str(value),"status":"POSTED"}}
@router.post("/payments/{payment_id}/allocations")
def payment_allocate(payment_id:UUID,payload:AllocationIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    with _engine().begin() as db: allocate_payment(db,context=c,payment_id=payment_id,**payload.model_dump())
    return {"data":{"id":str(payment_id)}}
