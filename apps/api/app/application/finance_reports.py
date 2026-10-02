from decimal import Decimal
from uuid import UUID

from sqlalchemy import Connection, text

from app.domain.security import RequestContext, require_permission


def trial_balance(db: Connection, *, context: RequestContext, legal_entity_id: UUID) -> list[dict[str, object]]:
    require_permission(context,"financial_report.read")
    rows=db.execute(text("""SELECT a.code,a.name,a.account_type,
      COALESCE(sum(l.base_debit),0) debit,COALESCE(sum(l.base_credit),0) credit,
      COALESCE(sum(l.base_debit-l.base_credit),0) balance
      FROM finance_accounts a LEFT JOIN journal_lines l ON l.tenant_id=a.tenant_id AND l.account_id=a.id
      LEFT JOIN journal_entries j ON j.tenant_id=l.tenant_id AND j.id=l.journal_entry_id AND j.status IN ('POSTED','REVERSED')
      WHERE a.tenant_id=:t AND a.legal_entity_id=:e
      GROUP BY a.id ORDER BY a.code"""),{"t":context.tenant_id,"e":legal_entity_id}).mappings().all()
    return [dict(x) for x in rows]


def reconcile_subledgers(db: Connection, *, context: RequestContext, legal_entity_id: UUID,
                         ar_control_account_id: UUID, ap_control_account_id: UUID) -> dict[str, Decimal]:
    require_permission(context,"accounting.read")
    ar=Decimal(db.execute(text("""SELECT COALESCE(sum(total_amount-settled_amount),0) FROM finance_invoices
      WHERE tenant_id=:t AND legal_entity_id=:e AND invoice_type='CUSTOMER' AND status NOT IN ('VOID','CREDITED')"""),
      {"t":context.tenant_id,"e":legal_entity_id}).scalar_one())
    ap=Decimal(db.execute(text("""SELECT COALESCE(sum(total_amount-settled_amount),0) FROM finance_invoices
      WHERE tenant_id=:t AND legal_entity_id=:e AND invoice_type='SUPPLIER' AND status NOT IN ('VOID','DEBITED')"""),
      {"t":context.tenant_id,"e":legal_entity_id}).scalar_one())
    def gl(account:UUID)->Decimal:
        return Decimal(db.execute(text("""SELECT COALESCE(sum(l.base_debit-l.base_credit),0)
          FROM journal_lines l JOIN journal_entries j ON j.tenant_id=l.tenant_id AND j.id=l.journal_entry_id
          WHERE l.tenant_id=:t AND j.legal_entity_id=:e AND l.account_id=:a"""),
          {"t":context.tenant_id,"e":legal_entity_id,"a":account}).scalar_one())
    ar_gl,ap_gl=gl(ar_control_account_id),-gl(ap_control_account_id)
    return {"ar_subledger":ar,"ar_gl":ar_gl,"ar_difference":ar-ar_gl,
            "ap_subledger":ap,"ap_gl":ap_gl,"ap_difference":ap-ap_gl}
