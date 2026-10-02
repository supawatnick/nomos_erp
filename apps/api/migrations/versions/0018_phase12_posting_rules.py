from alembic import op
import sqlalchemy as sa

revision="0018_phase12_posting_rules"
down_revision="0017_phase12_subledgers"

def upgrade():
    op.create_table("finance_posting_rules",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),sa.Column("legal_entity_id",sa.Uuid(),nullable=False),
      sa.Column("source_type",sa.String(80),nullable=False),sa.Column("debit_account_id",sa.Uuid(),nullable=False),sa.Column("credit_account_id",sa.Uuid(),nullable=False),
      sa.Column("status",sa.String(24),nullable=False,server_default="ACTIVE"),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
      sa.ForeignKeyConstraint(["tenant_id","debit_account_id"],["finance_accounts.tenant_id","finance_accounts.id"]),
      sa.ForeignKeyConstraint(["tenant_id","credit_account_id"],["finance_accounts.tenant_id","finance_accounts.id"]),
      sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","legal_entity_id","source_type"))
    op.create_table("inventory_valuation_entries",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),sa.Column("legal_entity_id",sa.Uuid(),nullable=False),
      sa.Column("inventory_transaction_id",sa.Uuid(),nullable=False),sa.Column("journal_entry_id",sa.Uuid(),nullable=False),
      sa.Column("valuation_method",sa.String(24),nullable=False),sa.Column("amount",sa.Numeric(24,8),nullable=False),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
      sa.ForeignKeyConstraint(["tenant_id","inventory_transaction_id"],["inventory_transactions.tenant_id","inventory_transactions.id"]),
      sa.ForeignKeyConstraint(["tenant_id","journal_entry_id"],["journal_entries.tenant_id","journal_entries.id"]),
      sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","inventory_transaction_id"),
      sa.CheckConstraint("valuation_method IN ('STANDARD')",name="ck_valuation_method"),
      sa.CheckConstraint("amount>=0",name="ck_valuation_amount"))
    op.create_table("product_standard_costs",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),sa.Column("legal_entity_id",sa.Uuid(),nullable=False),
      sa.Column("product_id",sa.Uuid(),nullable=False),sa.Column("unit_cost",sa.Numeric(24,8),nullable=False),sa.Column("effective_from",sa.Date(),nullable=False),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
      sa.ForeignKeyConstraint(["tenant_id","product_id"],["products.tenant_id","products.id"]),
      sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","legal_entity_id","product_id","effective_from"),
      sa.CheckConstraint("unit_cost>=0",name="ck_standard_cost"))

def downgrade():
    for t in ["product_standard_costs","inventory_valuation_entries","finance_posting_rules"]: op.drop_table(t)
