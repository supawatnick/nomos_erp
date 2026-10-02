from alembic import op
import sqlalchemy as sa

revision = "0016_phase12_finance_foundation"
down_revision = "0015_phase11_reporting"

MONEY = sa.Numeric(24, 8)

def upgrade():
    op.create_table("finance_accounts",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("legal_entity_id",sa.Uuid(),nullable=False),sa.Column("code",sa.String(40),nullable=False),
        sa.Column("name",sa.String(200),nullable=False),sa.Column("account_type",sa.String(24),nullable=False),
        sa.Column("currency_code",sa.CHAR(3)),sa.Column("is_control",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("status",sa.String(24),nullable=False,server_default="ACTIVE"),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","legal_entity_id","code"),
        sa.CheckConstraint("account_type IN ('ASSET','LIABILITY','EQUITY','REVENUE','EXPENSE')",name="ck_fin_account_type"))
    op.create_table("fiscal_periods",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("legal_entity_id",sa.Uuid(),nullable=False),sa.Column("period_key",sa.String(16),nullable=False),
        sa.Column("start_date",sa.Date(),nullable=False),sa.Column("end_date",sa.Date(),nullable=False),
        sa.Column("status",sa.String(24),nullable=False,server_default="OPEN"),
        sa.Column("closed_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","legal_entity_id","period_key"),
        sa.CheckConstraint("end_date >= start_date",name="ck_fiscal_period_dates"),
        sa.CheckConstraint("status IN ('OPEN','SOFT_CLOSED','CLOSED')",name="ck_fiscal_period_status"))
    op.create_table("journal_entries",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("legal_entity_id",sa.Uuid(),nullable=False),sa.Column("journal_number",sa.String(80),nullable=False),
        sa.Column("posting_date",sa.Date(),nullable=False),sa.Column("currency_code",sa.CHAR(3),nullable=False),
        sa.Column("exchange_rate",MONEY,nullable=False,server_default="1"),sa.Column("description",sa.String(500),nullable=False),
        sa.Column("source_module",sa.String(40),nullable=False),sa.Column("source_type",sa.String(80),nullable=False),
        sa.Column("source_id",sa.Uuid(),nullable=False),sa.Column("source_number",sa.String(120)),
        sa.Column("source_effect",sa.String(80),nullable=False,server_default="PRIMARY"),
        sa.Column("idempotency_key",sa.String(200),nullable=False),sa.Column("status",sa.String(24),nullable=False),
        sa.Column("reversal_of_id",sa.Uuid()),sa.Column("posted_at",sa.DateTime(timezone=True)),
        sa.Column("created_by_tenant_user_id",sa.Uuid(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
        sa.ForeignKeyConstraint(["tenant_id","created_by_tenant_user_id"],["tenant_users.tenant_id","tenant_users.id"]),
        sa.ForeignKeyConstraint(["tenant_id","reversal_of_id"],["journal_entries.tenant_id","journal_entries.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","legal_entity_id","journal_number"),
        sa.UniqueConstraint("tenant_id","legal_entity_id","source_module","source_type","source_id","source_effect"),
        sa.UniqueConstraint("tenant_id","idempotency_key"),
        sa.CheckConstraint("status IN ('POSTED','REVERSED')",name="ck_journal_status"),
        sa.CheckConstraint("exchange_rate > 0",name="ck_journal_rate"))
    op.create_table("journal_lines",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("journal_entry_id",sa.Uuid(),nullable=False),sa.Column("line_number",sa.Integer(),nullable=False),
        sa.Column("account_id",sa.Uuid(),nullable=False),sa.Column("description",sa.String(500)),
        sa.Column("debit",MONEY,nullable=False,server_default="0"),sa.Column("credit",MONEY,nullable=False,server_default="0"),
        sa.Column("base_debit",MONEY,nullable=False,server_default="0"),sa.Column("base_credit",MONEY,nullable=False,server_default="0"),
        sa.ForeignKeyConstraint(["tenant_id","journal_entry_id"],["journal_entries.tenant_id","journal_entries.id"]),
        sa.ForeignKeyConstraint(["tenant_id","account_id"],["finance_accounts.tenant_id","finance_accounts.id"]),
        sa.UniqueConstraint("tenant_id","journal_entry_id","line_number"),
        sa.CheckConstraint("debit >= 0 AND credit >= 0 AND base_debit >= 0 AND base_credit >= 0",name="ck_journal_line_nonnegative"),
        sa.CheckConstraint("(debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)",name="ck_journal_line_side"))
    op.create_index("ix_journal_gl","journal_entries",["tenant_id","legal_entity_id","posting_date","status"])
    op.execute("""INSERT INTO permissions (id,code,description,risk_level,created_at) VALUES
      (gen_random_uuid(),'accounting.read','Read accounting and general ledger','LOW',now()),
      (gen_random_uuid(),'accounting.configure','Manage chart of accounts and posting configuration','HIGH',now()),
      (gen_random_uuid(),'journal.manage','Create journal entries','MEDIUM',now()),
      (gen_random_uuid(),'journal.post','Post journal entries','HIGH',now()),
      (gen_random_uuid(),'journal.reverse','Reverse posted journal entries','HIGH',now()),
      (gen_random_uuid(),'fiscal_period.close','Close fiscal periods','HIGH',now()),
      (gen_random_uuid(),'fiscal_period.reopen','Reopen fiscal periods','HIGH',now()),
      (gen_random_uuid(),'ar.read','Read accounts receivable','LOW',now()),(gen_random_uuid(),'ar.manage','Manage AR documents','MEDIUM',now()),
      (gen_random_uuid(),'ar.post','Post AR documents','HIGH',now()),(gen_random_uuid(),'ap.read','Read accounts payable','LOW',now()),
      (gen_random_uuid(),'ap.manage','Manage AP documents','MEDIUM',now()),(gen_random_uuid(),'ap.post','Post AP documents','HIGH',now()),
      (gen_random_uuid(),'payment.manage','Manage receipts and payments','MEDIUM',now()),(gen_random_uuid(),'payment.post','Post receipts and payments','HIGH',now()),
      (gen_random_uuid(),'tax.manage','Manage tax configuration','HIGH',now()),(gen_random_uuid(),'fx.manage','Manage exchange rates','HIGH',now()),
      (gen_random_uuid(),'financial_report.read','Read financial statements','LOW',now()),(gen_random_uuid(),'financial_report.export','Export financial statements','HIGH',now())
      ON CONFLICT (code) DO NOTHING""")

def downgrade():
    for table in ["journal_lines","journal_entries","fiscal_periods","finance_accounts"]:
        op.drop_table(table)
