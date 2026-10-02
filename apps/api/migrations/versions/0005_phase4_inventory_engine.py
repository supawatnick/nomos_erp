from alembic import op
import sqlalchemy as sa

revision = "0005_phase4_inventory_engine"
down_revision = "0004_phase3_catalog_warehouse"


def upgrade():
    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("legal_entity_id", sa.Uuid(), nullable=False),
        sa.Column("branch_id", sa.Uuid()),
        sa.Column("transaction_type", sa.String(24), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("source_type", sa.String(80)),
        sa.Column("source_id", sa.Uuid()),
        sa.Column("source_number", sa.String(120)),
        sa.Column("reference", sa.String(240)),
        sa.Column("reason", sa.Text()),
        sa.Column("reversal_of_id", sa.Uuid()),
        sa.Column("reversed_by_id", sa.Uuid()),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("posted_by_user_id", sa.Uuid()),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"], ["legal_entities.tenant_id","legal_entities.id"]),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id","branch_id"], ["branches.tenant_id","branches.legal_entity_id","branches.id"]),
        sa.ForeignKeyConstraint(["tenant_id","reversal_of_id"], ["inventory_transactions.tenant_id","inventory_transactions.id"]),
        sa.ForeignKeyConstraint(["tenant_id","reversed_by_id"], ["inventory_transactions.tenant_id","inventory_transactions.id"]),
        sa.UniqueConstraint("tenant_id","id"),
        sa.UniqueConstraint("tenant_id","idempotency_key"),
        sa.UniqueConstraint("tenant_id","reversal_of_id"),
        sa.CheckConstraint("transaction_type IN ('RECEIVE','ISSUE','TRANSFER','ADJUST','REVERSAL','OPENING')", name="ck_inventory_tx_type"),
        sa.CheckConstraint("status = 'POSTED'", name="ck_inventory_tx_posted"),
        sa.CheckConstraint("(transaction_type='REVERSAL') = (reversal_of_id IS NOT NULL)", name="ck_inventory_tx_reversal"),
    )
    op.create_index("ix_inventory_tx_tenant_posted", "inventory_transactions", ["tenant_id","posted_at","id"])
    op.create_index("ix_inventory_tx_source", "inventory_transactions", ["tenant_id","source_type","source_id"])

    op.create_table(
        "inventory_transaction_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(24,8), nullable=False),
        sa.Column("base_quantity", sa.Numeric(24,8), nullable=False),
        sa.Column("direction", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","transaction_id"], ["inventory_transactions.tenant_id","inventory_transactions.id"]),
        sa.ForeignKeyConstraint(["tenant_id","product_id"], ["products.tenant_id","products.id"]),
        sa.ForeignKeyConstraint(["tenant_id","unit_id"], ["units.tenant_id","units.id"]),
        sa.ForeignKeyConstraint(["tenant_id","location_id"], ["warehouse_locations.tenant_id","warehouse_locations.id"]),
        sa.UniqueConstraint("tenant_id","transaction_id","line_no"),
        sa.CheckConstraint("quantity > 0 AND base_quantity > 0", name="ck_inventory_line_positive"),
        sa.CheckConstraint("direction IN (-1,1)", name="ck_inventory_line_direction"),
    )
    op.create_index("ix_inventory_lines_product_location", "inventory_transaction_lines", ["tenant_id","product_id","location_id"])

    op.create_table(
        "inventory_balances",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("on_hand", sa.Numeric(24,8), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id","product_id","location_id"),
        sa.ForeignKeyConstraint(["tenant_id","product_id"], ["products.tenant_id","products.id"]),
        sa.ForeignKeyConstraint(["tenant_id","location_id"], ["warehouse_locations.tenant_id","warehouse_locations.id"]),
        sa.CheckConstraint("on_hand >= 0", name="ck_inventory_balance_nonnegative"),
    )
    op.create_index("ix_inventory_balance_location", "inventory_balances", ["tenant_id","location_id","product_id"])

    op.execute(
        "INSERT INTO permissions (id,code,description,risk_level,created_at) VALUES "
        "(gen_random_uuid(),'inventory.read','Read inventory balances and movements','LOW',now()),"
        "(gen_random_uuid(),'inventory.receive','Post inventory receipts and opening stock','MEDIUM',now()),"
        "(gen_random_uuid(),'inventory.issue','Post inventory issues','MEDIUM',now()),"
        "(gen_random_uuid(),'inventory.transfer','Post inventory transfers','MEDIUM',now()),"
        "(gen_random_uuid(),'inventory.adjust','Post adjustments and reversals','HIGH',now()) "
        "ON CONFLICT (code) DO NOTHING"
    )


def downgrade():
    op.drop_table("inventory_balances")
    op.drop_table("inventory_transaction_lines")
    op.drop_table("inventory_transactions")
