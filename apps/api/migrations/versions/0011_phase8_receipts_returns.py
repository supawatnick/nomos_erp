from alembic import op
import sqlalchemy as sa

revision = "0011_phase8_receipts_returns"
down_revision = "0010_phase8_purchase_orders"


def upgrade():
    op.create_table(
        "goods_receipts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("receipt_number", sa.String(80), nullable=False),
        sa.Column("purchase_order_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("inventory_transaction_id", sa.Uuid()),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","purchase_order_id"],["purchase_orders.tenant_id","purchase_orders.id"]),
        sa.ForeignKeyConstraint(["tenant_id","location_id"],["warehouse_locations.tenant_id","warehouse_locations.id"]),
        sa.ForeignKeyConstraint(["tenant_id","inventory_transaction_id"],["inventory_transactions.tenant_id","inventory_transactions.id"]),
        sa.UniqueConstraint("tenant_id","id"),
        sa.UniqueConstraint("tenant_id","receipt_number"),
        sa.UniqueConstraint("tenant_id","idempotency_key"),
        sa.CheckConstraint("status IN ('DRAFT','POSTED','REVERSED')", name="ck_goods_receipt_status"),
    )
    op.create_table(
        "goods_receipt_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("goods_receipt_id", sa.Uuid(), nullable=False),
        sa.Column("purchase_order_line_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(24,8), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","goods_receipt_id"],["goods_receipts.tenant_id","goods_receipts.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id","purchase_order_line_id"],["purchase_order_lines.tenant_id","purchase_order_lines.id"]),
        sa.UniqueConstraint("tenant_id","id"),
        sa.UniqueConstraint("tenant_id","goods_receipt_id","purchase_order_line_id"),
        sa.CheckConstraint("quantity > 0", name="ck_goods_receipt_line_quantity"),
    )
    op.create_table(
        "purchase_returns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("return_number", sa.String(80), nullable=False),
        sa.Column("purchase_order_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("inventory_transaction_id", sa.Uuid()),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","purchase_order_id"],["purchase_orders.tenant_id","purchase_orders.id"]),
        sa.ForeignKeyConstraint(["tenant_id","location_id"],["warehouse_locations.tenant_id","warehouse_locations.id"]),
        sa.ForeignKeyConstraint(["tenant_id","inventory_transaction_id"],["inventory_transactions.tenant_id","inventory_transactions.id"]),
        sa.UniqueConstraint("tenant_id","id"),
        sa.UniqueConstraint("tenant_id","return_number"),
        sa.UniqueConstraint("tenant_id","idempotency_key"),
        sa.CheckConstraint("status IN ('DRAFT','POSTED','REVERSED')", name="ck_purchase_return_status"),
    )
    op.create_table(
        "purchase_return_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("purchase_return_id", sa.Uuid(), nullable=False),
        sa.Column("purchase_order_line_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(24,8), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","purchase_return_id"],["purchase_returns.tenant_id","purchase_returns.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id","purchase_order_line_id"],["purchase_order_lines.tenant_id","purchase_order_lines.id"]),
        sa.UniqueConstraint("tenant_id","id"),
        sa.UniqueConstraint("tenant_id","purchase_return_id","purchase_order_line_id"),
        sa.CheckConstraint("quantity > 0", name="ck_purchase_return_line_quantity"),
    )


def downgrade():
    op.drop_table("purchase_return_lines")
    op.drop_table("purchase_returns")
    op.drop_table("goods_receipt_lines")
    op.drop_table("goods_receipts")
