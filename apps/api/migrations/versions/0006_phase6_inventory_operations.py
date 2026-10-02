from alembic import op
import sqlalchemy as sa

revision = "0006_phase6_inventory_operations"
down_revision = "0005_phase4_inventory_engine"


def upgrade():
    op.create_table(
        "stock_counts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("legal_entity_id", sa.Uuid(), nullable=False),
        sa.Column("warehouse_id", sa.Uuid(), nullable=False),
        sa.Column("count_number", sa.String(80), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("reference", sa.String(240)),
        sa.Column("counted_at", sa.DateTime(timezone=True)),
        sa.Column("posted_transaction_id", sa.Uuid()),
        sa.Column("created_by_user_id", sa.Uuid()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
        sa.ForeignKeyConstraint(["tenant_id","warehouse_id"],["warehouses.tenant_id","warehouses.id"]),
        sa.ForeignKeyConstraint(["tenant_id","posted_transaction_id"],["inventory_transactions.tenant_id","inventory_transactions.id"]),
        sa.UniqueConstraint("tenant_id","id"),
        sa.UniqueConstraint("tenant_id","count_number"),
        sa.CheckConstraint("status IN ('DRAFT','COUNTED','POSTED','CANCELLED')",name="ck_stock_count_status"),
    )
    op.create_table(
        "stock_count_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("stock_count_id", sa.Uuid(), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("system_quantity", sa.Numeric(24,8), nullable=False),
        sa.Column("counted_quantity", sa.Numeric(24,8)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","stock_count_id"],["stock_counts.tenant_id","stock_counts.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id","product_id"],["products.tenant_id","products.id"]),
        sa.ForeignKeyConstraint(["tenant_id","location_id"],["warehouse_locations.tenant_id","warehouse_locations.id"]),
        sa.ForeignKeyConstraint(["tenant_id","unit_id"],["units.tenant_id","units.id"]),
        sa.UniqueConstraint("tenant_id","stock_count_id","line_no"),
        sa.UniqueConstraint("tenant_id","stock_count_id","product_id","location_id"),
        sa.CheckConstraint("system_quantity >= 0 AND (counted_quantity IS NULL OR counted_quantity >= 0)",name="ck_stock_count_quantities"),
    )
    op.create_table(
        "reorder_policies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("reorder_point", sa.Numeric(24,8), nullable=False),
        sa.Column("target_quantity", sa.Numeric(24,8), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","product_id"],["products.tenant_id","products.id"]),
        sa.ForeignKeyConstraint(["tenant_id","location_id"],["warehouse_locations.tenant_id","warehouse_locations.id"]),
        sa.UniqueConstraint("tenant_id","id"),
        sa.UniqueConstraint("tenant_id","product_id","location_id"),
        sa.CheckConstraint("reorder_point >= 0 AND target_quantity >= reorder_point",name="ck_reorder_policy_quantities"),
    )
    op.execute(
        "INSERT INTO permissions (id,code,description,risk_level,created_at) VALUES "
        "(gen_random_uuid(),'inventory.count','Create and update stock counts','MEDIUM',now()),"
        "(gen_random_uuid(),'inventory.count.post','Post stock-count variance adjustments','HIGH',now()),"
        "(gen_random_uuid(),'inventory.reorder.manage','Manage reorder policies','MEDIUM',now()),"
        "(gen_random_uuid(),'inventory.report','Read inventory operational reports','LOW',now()) "
        "ON CONFLICT (code) DO NOTHING"
    )


def downgrade():
    op.drop_table("reorder_policies")
    op.drop_table("stock_count_lines")
    op.drop_table("stock_counts")
