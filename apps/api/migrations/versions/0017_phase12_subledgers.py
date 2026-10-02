from alembic import op
import sqlalchemy as sa

revision="0017_phase12_subledgers"
down_revision="0016_phase12_finance_foundation"
M=sa.Numeric(24,8)

def upgrade():
    op.create_table("tax_codes",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),sa.Column("legal_entity_id",sa.Uuid(),nullable=False),
      sa.Column("code",sa.String(40),nullable=False),sa.Column("name",sa.String(120),nullable=False),sa.Column("rate",M,nullable=False),
      sa.Column("effective_from",sa.Date(),nullable=False),sa.Column("effective_to",sa.Date()),sa.Column("status",sa.String(24),nullable=False),
      sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
      sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","legal_entity_id","code","effective_from"),
      sa.CheckConstraint("rate>=0",name="ck_tax_rate"))
    op.create_table("exchange_rates",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),sa.Column("legal_entity_id",sa.Uuid(),nullable=False),
      sa.Column("rate_date",sa.Date(),nullable=False),sa.Column("from_currency",sa.CHAR(3),nullable=False),sa.Column("to_currency",sa.CHAR(3),nullable=False),
      sa.Column("rate",M,nullable=False),sa.Column("source",sa.String(120),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
      sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","legal_entity_id","rate_date","from_currency","to_currency","source"),
      sa.CheckConstraint("rate>0",name="ck_fx_rate"))
    op.create_table("finance_invoices",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),sa.Column("legal_entity_id",sa.Uuid(),nullable=False),
      sa.Column("invoice_type",sa.String(16),nullable=False),sa.Column("invoice_number",sa.String(80),nullable=False),
      sa.Column("partner_id",sa.Uuid(),nullable=False),sa.Column("invoice_date",sa.Date(),nullable=False),sa.Column("due_date",sa.Date(),nullable=False),
      sa.Column("currency_code",sa.CHAR(3),nullable=False),sa.Column("exchange_rate",M,nullable=False,server_default="1"),
      sa.Column("net_amount",M,nullable=False),sa.Column("tax_amount",M,nullable=False,server_default="0"),sa.Column("total_amount",M,nullable=False),
      sa.Column("settled_amount",M,nullable=False,server_default="0"),sa.Column("status",sa.String(24),nullable=False),
      sa.Column("source_type",sa.String(80)),sa.Column("source_id",sa.Uuid()),sa.Column("source_number",sa.String(120)),
      sa.Column("journal_entry_id",sa.Uuid()),sa.Column("posted_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
      sa.ForeignKeyConstraint(["tenant_id","partner_id"],["business_partners.tenant_id","business_partners.id"]),
      sa.ForeignKeyConstraint(["tenant_id","journal_entry_id"],["journal_entries.tenant_id","journal_entries.id"]),
      sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","legal_entity_id","invoice_type","invoice_number"),
      sa.CheckConstraint("invoice_type IN ('CUSTOMER','SUPPLIER')",name="ck_invoice_type"),
      sa.CheckConstraint("status IN ('POSTED','PARTIALLY_SETTLED','SETTLED','CREDITED','DEBITED','VOID')",name="ck_invoice_status"),
      sa.CheckConstraint("net_amount>=0 AND tax_amount>=0 AND total_amount=net_amount+tax_amount AND settled_amount>=0 AND settled_amount<=total_amount",name="ck_invoice_amounts"))
    op.create_table("finance_payments",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),sa.Column("legal_entity_id",sa.Uuid(),nullable=False),
      sa.Column("payment_type",sa.String(16),nullable=False),sa.Column("payment_number",sa.String(80),nullable=False),
      sa.Column("partner_id",sa.Uuid(),nullable=False),sa.Column("payment_date",sa.Date(),nullable=False),sa.Column("currency_code",sa.CHAR(3),nullable=False),
      sa.Column("amount",M,nullable=False),sa.Column("allocated_amount",M,nullable=False,server_default="0"),sa.Column("status",sa.String(24),nullable=False),
      sa.Column("journal_entry_id",sa.Uuid(),nullable=False),sa.Column("reversal_journal_id",sa.Uuid()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
      sa.ForeignKeyConstraint(["tenant_id","partner_id"],["business_partners.tenant_id","business_partners.id"]),
      sa.ForeignKeyConstraint(["tenant_id","journal_entry_id"],["journal_entries.tenant_id","journal_entries.id"]),
      sa.ForeignKeyConstraint(["tenant_id","reversal_journal_id"],["journal_entries.tenant_id","journal_entries.id"]),
      sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","legal_entity_id","payment_type","payment_number"),
      sa.CheckConstraint("payment_type IN ('RECEIPT','PAYMENT')",name="ck_payment_type"),
      sa.CheckConstraint("status IN ('POSTED','PARTIALLY_ALLOCATED','ALLOCATED','REVERSED')",name="ck_payment_status"),
      sa.CheckConstraint("amount>0 AND allocated_amount>=0 AND allocated_amount<=amount",name="ck_payment_amounts"))
    op.create_table("finance_allocations",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
      sa.Column("payment_id",sa.Uuid(),nullable=False),sa.Column("invoice_id",sa.Uuid(),nullable=False),sa.Column("amount",M,nullable=False),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(["tenant_id","payment_id"],["finance_payments.tenant_id","finance_payments.id"]),
      sa.ForeignKeyConstraint(["tenant_id","invoice_id"],["finance_invoices.tenant_id","finance_invoices.id"]),
      sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","payment_id","invoice_id"),
      sa.CheckConstraint("amount>0",name="ck_allocation_amount"))
    op.create_index("ix_finance_invoices_open","finance_invoices",["tenant_id","legal_entity_id","invoice_type","status","due_date"])

def downgrade():
    for t in ["finance_allocations","finance_payments","finance_invoices","exchange_rates","tax_codes"]: op.drop_table(t)
