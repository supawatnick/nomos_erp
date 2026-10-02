from alembic import op
import sqlalchemy as sa

revision = "0010_phase8_purchase_orders"
down_revision = "0009_phase8_procurement"


def upgrade():
    op.create_table(
        "procurement_rfq_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("rfq_id", sa.Uuid(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("purchase_request_line_id", sa.Uuid()),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 8), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "rfq_id"], ["procurement_rfqs.tenant_id", "procurement_rfqs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "purchase_request_line_id"], ["purchase_request_lines.tenant_id", "purchase_request_lines.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "unit_id"], ["units.tenant_id", "units.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "rfq_id", "line_number"),
        sa.CheckConstraint("quantity > 0", name="ck_rfq_line_quantity"),
    )
    op.create_table(
        "procurement_rfq_supplier_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("rfq_supplier_id", sa.Uuid(), nullable=False),
        sa.Column("rfq_line_id", sa.Uuid(), nullable=False),
        sa.Column("offered_quantity", sa.Numeric(24, 8), nullable=False),
        sa.Column("unit_price", sa.Numeric(24, 8), nullable=False),
        sa.Column("discount_amount", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(24, 8), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "rfq_supplier_id"], ["procurement_rfq_suppliers.tenant_id", "procurement_rfq_suppliers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "rfq_line_id"], ["procurement_rfq_lines.tenant_id", "procurement_rfq_lines.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "rfq_supplier_id", "rfq_line_id"),
        sa.CheckConstraint("offered_quantity > 0", name="ck_rfq_supplier_line_quantity"),
        sa.CheckConstraint("unit_price >= 0 AND discount_amount >= 0 AND tax_amount >= 0 AND line_total >= 0", name="ck_rfq_supplier_line_amounts"),
    )
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("order_number", sa.String(80), nullable=False),
        sa.Column("legal_entity_id", sa.Uuid(), nullable=False),
        sa.Column("branch_id", sa.Uuid()),
        sa.Column("supplier_id", sa.Uuid(), nullable=False),
        sa.Column("source_rfq_id", sa.Uuid()),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("approval_fingerprint", sa.String(64)),
        sa.Column("approved_version", sa.Integer()),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by_tenant_user_id", sa.Uuid()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "legal_entity_id"], ["legal_entities.tenant_id", "legal_entities.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "legal_entity_id", "branch_id"], ["branches.tenant_id", "branches.legal_entity_id", "branches.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "supplier_id"], ["business_partners.tenant_id", "business_partners.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "source_rfq_id"], ["procurement_rfqs.tenant_id", "procurement_rfqs.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "approved_by_tenant_user_id"], ["tenant_users.tenant_id", "tenant_users.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "order_number"),
        sa.CheckConstraint("status IN ('DRAFT','PENDING_APPROVAL','APPROVED','SENT','PARTIALLY_RECEIVED','RECEIVED','CLOSED','ON_HOLD','CANCELLED')", name="ck_purchase_order_status"),
    )
    op.create_table(
        "purchase_order_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("purchase_order_id", sa.Uuid(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("ordered_quantity", sa.Numeric(24, 8), nullable=False),
        sa.Column("unit_price", sa.Numeric(24, 8), nullable=False),
        sa.Column("discount_amount", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(24, 8), nullable=False),
        sa.Column("received_quantity", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.Column("returned_quantity", sa.Numeric(24, 8), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["tenant_id", "purchase_order_id"], ["purchase_orders.tenant_id", "purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "unit_id"], ["units.tenant_id", "units.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "purchase_order_id", "line_number"),
        sa.CheckConstraint("ordered_quantity > 0", name="ck_po_line_ordered_quantity"),
        sa.CheckConstraint("unit_price >= 0 AND discount_amount >= 0 AND tax_amount >= 0 AND line_total >= 0", name="ck_po_line_amounts"),
        sa.CheckConstraint("received_quantity >= 0 AND returned_quantity >= 0 AND returned_quantity <= received_quantity AND received_quantity <= ordered_quantity", name="ck_po_line_progress"),
    )


def downgrade():
    op.drop_table("purchase_order_lines")
    op.drop_table("purchase_orders")
    op.drop_table("procurement_rfq_supplier_lines")
    op.drop_table("procurement_rfq_lines")
