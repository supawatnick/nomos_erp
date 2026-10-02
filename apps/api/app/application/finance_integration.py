from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.application.finance import FinanceError, post_journal
from app.domain.security import RequestContext, require_permission


def configure_posting_rule(db: Connection, *, context: RequestContext, legal_entity_id: UUID,
                           source_type: str, debit_account_id: UUID, credit_account_id: UUID) -> UUID:
    require_permission(context,"accounting.configure")
    count: int=db.execute(text("""SELECT count(*) FROM finance_accounts WHERE tenant_id=:t AND legal_entity_id=:e
      AND id=ANY(:ids) AND status='ACTIVE'"""),{"t":context.tenant_id,"e":legal_entity_id,
      "ids":[debit_account_id,credit_account_id]}).scalar_one()
    if count!=2: raise FinanceError("posting rule accounts must belong to legal entity")
    rule=uuid4()
    db.execute(text("""INSERT INTO finance_posting_rules
      (id,tenant_id,legal_entity_id,source_type,debit_account_id,credit_account_id,status,created_at)
      VALUES (:id,:t,:e,:type,:d,:c,'ACTIVE',now())"""),{"id":rule,"t":context.tenant_id,"e":legal_entity_id,
      "type":source_type,"d":debit_account_id,"c":credit_account_id})
    return rule


def set_standard_cost(db: Connection, *, context: RequestContext, legal_entity_id: UUID,
                      product_id: UUID, unit_cost: Decimal, effective_from: date) -> UUID:
    require_permission(context,"accounting.configure")
    if unit_cost<0: raise FinanceError("standard cost cannot be negative")
    value=uuid4()
    db.execute(text("""INSERT INTO product_standard_costs
      (id,tenant_id,legal_entity_id,product_id,unit_cost,effective_from,created_at)
      VALUES (:id,:t,:e,:p,:cost,:date,now())"""),{"id":value,"t":context.tenant_id,"e":legal_entity_id,
      "p":product_id,"cost":unit_cost,"date":effective_from})
    return value


def post_inventory_valuation(db: Connection, *, context: RequestContext, inventory_transaction_id: UUID,
                             posting_date: date, period_key: str, idempotency_key: str) -> UUID:
    require_permission(context,"journal.post")
    existing=db.execute(text("SELECT journal_entry_id FROM inventory_valuation_entries WHERE tenant_id=:t AND inventory_transaction_id=:id"),
                        {"t":context.tenant_id,"id":inventory_transaction_id}).scalar_one_or_none()
    if existing: return existing
    tx=db.execute(text("""SELECT id,legal_entity_id,transaction_number,transaction_type,status FROM inventory_transactions
      WHERE tenant_id=:t AND id=:id"""),{"t":context.tenant_id,"id":inventory_transaction_id}).mappings().first()
    if not tx or tx["status"]!="POSTED": raise FinanceError("inventory source is not posted")
    rule=db.execute(text("""SELECT debit_account_id,credit_account_id FROM finance_posting_rules
      WHERE tenant_id=:t AND legal_entity_id=:e AND source_type=:type AND status='ACTIVE'"""),
      {"t":context.tenant_id,"e":tx["legal_entity_id"],"type":"INVENTORY_"+tx["transaction_type"]}).mappings().first()
    if not rule: raise FinanceError("inventory posting rule not configured")
    amount=Decimal(db.execute(text("""SELECT COALESCE(sum(abs(l.base_quantity)*c.unit_cost),0)
      FROM inventory_transaction_lines l JOIN product_standard_costs c ON c.tenant_id=l.tenant_id
       AND c.legal_entity_id=:e AND c.product_id=l.product_id AND c.effective_from<=:date
      WHERE l.tenant_id=:t AND l.transaction_id=:id
       AND c.effective_from=(SELECT max(c2.effective_from) FROM product_standard_costs c2 WHERE c2.tenant_id=c.tenant_id
         AND c2.legal_entity_id=c.legal_entity_id AND c2.product_id=c.product_id AND c2.effective_from<=:date)"""),
      {"t":context.tenant_id,"e":tx["legal_entity_id"],"id":inventory_transaction_id,"date":posting_date}).scalar_one())
    if amount<=0: raise FinanceError("inventory valuation amount is zero or cost missing")
    journal=post_journal(db,context=context,legal_entity_id=tx["legal_entity_id"],posting_date=posting_date,
      currency_code="THB",description=f"Inventory valuation {tx['transaction_number']}",source_module="INVENTORY",
      source_type="INVENTORY_"+tx["transaction_type"],source_id=inventory_transaction_id,source_number=tx["transaction_number"],
      source_effect="VALUATION",idempotency_key=idempotency_key,period_key=period_key,
      lines=[{"account_id":rule["debit_account_id"],"debit":amount},{"account_id":rule["credit_account_id"],"credit":amount}])
    db.execute(text("""INSERT INTO inventory_valuation_entries
      (id,tenant_id,legal_entity_id,inventory_transaction_id,journal_entry_id,valuation_method,amount,created_at)
      VALUES (:id,:t,:e,:tx,:journal,'STANDARD',:amount,now())"""),{"id":uuid4(),"t":context.tenant_id,
      "e":tx["legal_entity_id"],"tx":inventory_transaction_id,"journal":journal,"amount":amount})
    return journal
