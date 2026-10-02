from alembic import op
import sqlalchemy as sa

revision = "0012_phase9_sales"
down_revision = "0011_phase8_receipts_returns"


def upgrade():
    op.create_table("sales_quotations",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("quotation_number",sa.String(80),nullable=False),sa.Column("legal_entity_id",sa.Uuid(),nullable=False),
        sa.Column("branch_id",sa.Uuid()),sa.Column("customer_id",sa.Uuid(),nullable=False),
        sa.Column("opportunity_id",sa.Uuid()),sa.Column("owner_tenant_user_id",sa.Uuid()),
        sa.Column("currency_code",sa.String(3),nullable=False),sa.Column("status",sa.String(16),nullable=False,server_default="DRAFT"),
        sa.Column("current_revision",sa.Integer(),nullable=False,server_default="1"),sa.Column("valid_until",sa.Date()),
        sa.Column("accepted_revision",sa.Integer()),sa.Column("accepted_at",sa.DateTime(timezone=True)),
        sa.Column("accepted_by",sa.String(240)),sa.Column("version",sa.Integer(),nullable=False,server_default="1"),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id","branch_id"],["branches.tenant_id","branches.legal_entity_id","branches.id"]),
        sa.ForeignKeyConstraint(["tenant_id","customer_id"],["business_partners.tenant_id","business_partners.id"]),
        sa.ForeignKeyConstraint(["tenant_id","opportunity_id"],["crm_opportunities.tenant_id","crm_opportunities.id"]),
        sa.ForeignKeyConstraint(["tenant_id","owner_tenant_user_id"],["tenant_users.tenant_id","tenant_users.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","quotation_number"),
        sa.CheckConstraint("status IN ('DRAFT','SENT','ACCEPTED','REJECTED','EXPIRED','CANCELLED')",name="ck_sales_quotation_status"),
        sa.CheckConstraint("current_revision > 0",name="ck_sales_quotation_revision"))
    op.create_table("sales_quotation_revisions",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("quotation_id",sa.Uuid(),nullable=False),sa.Column("revision",sa.Integer(),nullable=False),
        sa.Column("customer_id",sa.Uuid(),nullable=False),sa.Column("currency_code",sa.String(3),nullable=False),
        sa.Column("valid_until",sa.Date()),sa.Column("terms",sa.Text()),sa.Column("total_amount",sa.Numeric(24,8),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","quotation_id"],["sales_quotations.tenant_id","sales_quotations.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id","customer_id"],["business_partners.tenant_id","business_partners.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","quotation_id","revision"),
        sa.CheckConstraint("revision > 0 AND total_amount >= 0",name="ck_sales_qt_revision_values"))
    op.create_table("sales_quotation_lines",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("quotation_revision_id",sa.Uuid(),nullable=False),sa.Column("line_number",sa.Integer(),nullable=False),
        sa.Column("product_id",sa.Uuid(),nullable=False),sa.Column("unit_id",sa.Uuid(),nullable=False),
        sa.Column("quantity",sa.Numeric(24,8),nullable=False),sa.Column("unit_price",sa.Numeric(24,8),nullable=False),
        sa.Column("discount_amount",sa.Numeric(24,8),nullable=False,server_default="0"),
        sa.Column("tax_amount",sa.Numeric(24,8),nullable=False,server_default="0"),sa.Column("line_total",sa.Numeric(24,8),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","quotation_revision_id"],["sales_quotation_revisions.tenant_id","sales_quotation_revisions.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id","product_id"],["products.tenant_id","products.id"]),
        sa.ForeignKeyConstraint(["tenant_id","unit_id"],["units.tenant_id","units.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","quotation_revision_id","line_number"),
        sa.CheckConstraint("quantity > 0 AND unit_price >= 0 AND discount_amount >= 0 AND tax_amount >= 0 AND line_total >= 0",name="ck_sales_qt_line_values"))
    op.create_table("sales_orders",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("order_number",sa.String(80),nullable=False),sa.Column("legal_entity_id",sa.Uuid(),nullable=False),
        sa.Column("branch_id",sa.Uuid()),sa.Column("customer_id",sa.Uuid(),nullable=False),
        sa.Column("source_quotation_id",sa.Uuid()),sa.Column("source_quotation_revision",sa.Integer()),
        sa.Column("currency_code",sa.String(3),nullable=False),sa.Column("status",sa.String(24),nullable=False,server_default="DRAFT"),
        sa.Column("version",sa.Integer(),nullable=False,server_default="1"),sa.Column("confirmed_at",sa.DateTime(timezone=True)),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id","branch_id"],["branches.tenant_id","branches.legal_entity_id","branches.id"]),
        sa.ForeignKeyConstraint(["tenant_id","customer_id"],["business_partners.tenant_id","business_partners.id"]),
        sa.ForeignKeyConstraint(["tenant_id","source_quotation_id"],["sales_quotations.tenant_id","sales_quotations.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","order_number"),
        sa.CheckConstraint("status IN ('DRAFT','CONFIRMED','RESERVED','PARTIALLY_RESERVED','PROCESSING','PARTIALLY_FULFILLED','FULFILLED','CLOSED','ON_HOLD','CANCELLED')",name="ck_sales_order_status"))
    op.create_table("sales_order_lines",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("sales_order_id",sa.Uuid(),nullable=False),sa.Column("line_number",sa.Integer(),nullable=False),
        sa.Column("product_id",sa.Uuid(),nullable=False),sa.Column("unit_id",sa.Uuid(),nullable=False),
        sa.Column("ordered_quantity",sa.Numeric(24,8),nullable=False),sa.Column("unit_price",sa.Numeric(24,8),nullable=False),
        sa.Column("discount_amount",sa.Numeric(24,8),nullable=False,server_default="0"),sa.Column("tax_amount",sa.Numeric(24,8),nullable=False,server_default="0"),
        sa.Column("line_total",sa.Numeric(24,8),nullable=False),sa.Column("reserved_quantity",sa.Numeric(24,8),nullable=False,server_default="0"),
        sa.Column("delivered_quantity",sa.Numeric(24,8),nullable=False,server_default="0"),sa.Column("returned_quantity",sa.Numeric(24,8),nullable=False,server_default="0"),
        sa.ForeignKeyConstraint(["tenant_id","sales_order_id"],["sales_orders.tenant_id","sales_orders.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id","product_id"],["products.tenant_id","products.id"]),
        sa.ForeignKeyConstraint(["tenant_id","unit_id"],["units.tenant_id","units.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","sales_order_id","line_number"),
        sa.CheckConstraint("ordered_quantity > 0 AND unit_price >= 0 AND discount_amount >= 0 AND tax_amount >= 0 AND line_total >= 0",name="ck_sales_order_line_values"),
        sa.CheckConstraint("reserved_quantity >= 0 AND delivered_quantity >= 0 AND returned_quantity >= 0 AND reserved_quantity <= ordered_quantity AND delivered_quantity <= ordered_quantity AND returned_quantity <= delivered_quantity",name="ck_sales_order_progress"))
    op.create_table("sales_reservations",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("sales_order_id",sa.Uuid(),nullable=False),sa.Column("sales_order_line_id",sa.Uuid(),nullable=False),
        sa.Column("location_id",sa.Uuid(),nullable=False),sa.Column("quantity",sa.Numeric(24,8),nullable=False),
        sa.Column("status",sa.String(16),nullable=False,server_default="ACTIVE"),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("released_at",sa.DateTime(timezone=True)),sa.ForeignKeyConstraint(["tenant_id","sales_order_id"],["sales_orders.tenant_id","sales_orders.id"]),
        sa.ForeignKeyConstraint(["tenant_id","sales_order_line_id"],["sales_order_lines.tenant_id","sales_order_lines.id"]),
        sa.ForeignKeyConstraint(["tenant_id","location_id"],["warehouse_locations.tenant_id","warehouse_locations.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.CheckConstraint("quantity > 0",name="ck_sales_reservation_quantity"),
        sa.CheckConstraint("status IN ('ACTIVE','RELEASED','FULFILLED')",name="ck_sales_reservation_status"))
    op.create_table("sales_deliveries",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("delivery_number",sa.String(80),nullable=False),sa.Column("sales_order_id",sa.Uuid(),nullable=False),
        sa.Column("location_id",sa.Uuid(),nullable=False),sa.Column("status",sa.String(16),nullable=False,server_default="POSTED"),
        sa.Column("inventory_transaction_id",sa.Uuid(),nullable=False),sa.Column("idempotency_key",sa.String(200),nullable=False),
        sa.Column("posted_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","sales_order_id"],["sales_orders.tenant_id","sales_orders.id"]),
        sa.ForeignKeyConstraint(["tenant_id","location_id"],["warehouse_locations.tenant_id","warehouse_locations.id"]),
        sa.ForeignKeyConstraint(["tenant_id","inventory_transaction_id"],["inventory_transactions.tenant_id","inventory_transactions.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","delivery_number"),sa.UniqueConstraint("tenant_id","idempotency_key"))
    op.create_table("sales_delivery_lines",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("delivery_id",sa.Uuid(),nullable=False),sa.Column("sales_order_line_id",sa.Uuid(),nullable=False),
        sa.Column("quantity",sa.Numeric(24,8),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","delivery_id"],["sales_deliveries.tenant_id","sales_deliveries.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id","sales_order_line_id"],["sales_order_lines.tenant_id","sales_order_lines.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.CheckConstraint("quantity > 0",name="ck_sales_delivery_quantity"))
    op.create_table("sales_returns",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("return_number",sa.String(80),nullable=False),sa.Column("sales_order_id",sa.Uuid(),nullable=False),
        sa.Column("location_id",sa.Uuid(),nullable=False),sa.Column("inventory_transaction_id",sa.Uuid(),nullable=False),
        sa.Column("idempotency_key",sa.String(200),nullable=False),sa.Column("posted_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","sales_order_id"],["sales_orders.tenant_id","sales_orders.id"]),
        sa.ForeignKeyConstraint(["tenant_id","location_id"],["warehouse_locations.tenant_id","warehouse_locations.id"]),
        sa.ForeignKeyConstraint(["tenant_id","inventory_transaction_id"],["inventory_transactions.tenant_id","inventory_transactions.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","return_number"),sa.UniqueConstraint("tenant_id","idempotency_key"))
    op.create_table("sales_return_lines",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("return_id",sa.Uuid(),nullable=False),sa.Column("sales_order_line_id",sa.Uuid(),nullable=False),sa.Column("quantity",sa.Numeric(24,8),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","return_id"],["sales_returns.tenant_id","sales_returns.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id","sales_order_line_id"],["sales_order_lines.tenant_id","sales_order_lines.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.CheckConstraint("quantity > 0",name="ck_sales_return_quantity"))
    op.execute("""INSERT INTO permissions (id,code,description,risk_level,created_at) VALUES
      (gen_random_uuid(),'sales.read','Read quotations, sales orders and tracking','LOW',now()),
      (gen_random_uuid(),'quotation.manage','Create, edit and send quotations','MEDIUM',now()),
      (gen_random_uuid(),'quotation.transition','Accept, reject, expire and cancel quotations','MEDIUM',now()),
      (gen_random_uuid(),'sales_order.manage','Create, edit and confirm sales orders','MEDIUM',now()),
      (gen_random_uuid(),'sales_order.override','Hold or cancel sales orders','HIGH',now()),
      (gen_random_uuid(),'sales.reserve','Reserve and release sales stock','MEDIUM',now()),
      (gen_random_uuid(),'sales.fulfill','Post sales delivery and return','MEDIUM',now()),
      (gen_random_uuid(),'sales.override','Override sales price, discount or credit exception','HIGH',now())
      ON CONFLICT (code) DO NOTHING""")


def downgrade():
    op.drop_table("sales_return_lines");op.drop_table("sales_returns");op.drop_table("sales_delivery_lines");op.drop_table("sales_deliveries")
    op.drop_table("sales_reservations");op.drop_table("sales_order_lines");op.drop_table("sales_orders")
    op.drop_table("sales_quotation_lines");op.drop_table("sales_quotation_revisions");op.drop_table("sales_quotations")
