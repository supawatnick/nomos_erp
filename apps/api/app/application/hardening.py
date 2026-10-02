from decimal import Decimal
from uuid import UUID

from sqlalchemy import Connection, text


def reconciliation_snapshot(db: Connection, *, tenant_id: UUID) -> dict[str, object]:
    inventory_variance = db.execute(text("""WITH ledger AS (
      SELECT l.tenant_id,l.product_id,l.location_id,sum(l.base_quantity) qty
      FROM inventory_transaction_lines l JOIN inventory_transactions t
        ON t.tenant_id=l.tenant_id AND t.id=l.transaction_id
      WHERE l.tenant_id=:t AND t.status='POSTED' GROUP BY l.tenant_id,l.product_id,l.location_id
    ), keys AS (
      SELECT product_id,location_id FROM ledger UNION
      SELECT product_id,location_id FROM inventory_balances WHERE tenant_id=:t
    )
    SELECT COALESCE(sum(abs(COALESCE(l.qty,0)-COALESCE(b.quantity,0))),0)
    FROM keys k LEFT JOIN ledger l ON l.product_id=k.product_id AND l.location_id=k.location_id
    LEFT JOIN inventory_balances b ON b.tenant_id=:t AND b.product_id=k.product_id AND b.location_id=k.location_id"""),
      {"t":tenant_id}).scalar_one()
    unbalanced = db.execute(text("""SELECT count(*) FROM (
      SELECT j.id FROM journal_entries j JOIN journal_lines l ON l.tenant_id=j.tenant_id AND l.journal_entry_id=j.id
      WHERE j.tenant_id=:t GROUP BY j.id HAVING sum(l.debit)<>sum(l.credit)
    ) x"""),{"t":tenant_id}).scalar_one()
    duplicate_sources = db.execute(text("""SELECT count(*) FROM (
      SELECT source_module,source_type,source_id,source_effect,count(*) FROM journal_entries
      WHERE tenant_id=:t AND reversal_of_id IS NULL GROUP BY source_module,source_type,source_id,source_effect HAVING count(*)>1
    ) x"""),{"t":tenant_id}).scalar_one()
    ar = db.execute(text("""SELECT COALESCE(sum(total_amount-paid_amount),0) FROM customer_invoices
      WHERE tenant_id=:t AND status IN ('POSTED','PARTIALLY_PAID')"""),{"t":tenant_id}).scalar_one()
    ap = db.execute(text("""SELECT COALESCE(sum(total_amount-paid_amount),0) FROM supplier_invoices
      WHERE tenant_id=:t AND status IN ('POSTED','PARTIALLY_PAID')"""),{"t":tenant_id}).scalar_one()
    return {"inventory_quantity_variance":str(Decimal(inventory_variance)),"unbalanced_journals":int(unbalanced),
            "duplicate_financial_sources":int(duplicate_sources),"ar_open_amount":str(Decimal(ar)),
            "ap_open_amount":str(Decimal(ap)),"healthy":Decimal(inventory_variance)==0 and unbalanced==0 and duplicate_sources==0}
