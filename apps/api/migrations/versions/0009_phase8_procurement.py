from alembic import op
import sqlalchemy as sa

revision = "0009_phase8_procurement"
down_revision = "0008_phase0_7_remediation"


def upgrade():
    op.create_table(
        "purchase_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("request_number", sa.String(80), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("requested_by_tenant_user_id", sa.Uuid()),
        sa.Column("needed_by", sa.Date()),
        sa.Column("reason", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "requested_by_tenant_user_id"], ["tenant_users.tenant_id", "tenant_users.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "request_number"),
        sa.CheckConstraint("status IN ('DRAFT','PENDING_APPROVAL','APPROVED','REJECTED','SOURCING','CONVERTED','CANCELLED')", name="ck_purchase_request_status"),
    )
    op.create_table(
        "purchase_request_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("purchase_request_id", sa.Uuid(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 8), nullable=False),
        sa.Column("note", sa.Text()),
        sa.ForeignKeyConstraint(["tenant_id", "purchase_request_id"], ["purchase_requests.tenant_id", "purchase_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "unit_id"], ["units.tenant_id", "units.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "purchase_request_id", "line_number"),
        sa.CheckConstraint("quantity > 0", name="ck_purchase_request_line_quantity"),
    )
    op.create_table(
        "procurement_rfqs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("rfq_number", sa.String(80), nullable=False),
        sa.Column("purchase_request_id", sa.Uuid()),
        sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="THB"),
        sa.Column("response_due_date", sa.Date()),
        sa.Column("awarded_supplier_id", sa.Uuid()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "purchase_request_id"], ["purchase_requests.tenant_id", "purchase_requests.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "awarded_supplier_id"], ["business_partners.tenant_id", "business_partners.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "rfq_number"),
        sa.CheckConstraint("status IN ('DRAFT','SENT','RESPONSES_RECEIVED','AWARDED','CLOSED','CANCELLED')", name="ck_procurement_rfq_status"),
    )
    op.create_table(
        "procurement_rfq_suppliers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("rfq_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="INVITED"),
        sa.Column("quoted_total", sa.Numeric(24, 8)),
        sa.Column("quoted_at", sa.DateTime(timezone=True)),
        sa.Column("note", sa.Text()),
        sa.ForeignKeyConstraint(["tenant_id", "rfq_id"], ["procurement_rfqs.tenant_id", "procurement_rfqs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "supplier_id"], ["business_partners.tenant_id", "business_partners.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "rfq_id", "supplier_id"),
        sa.CheckConstraint("status IN ('INVITED','RESPONDED','DECLINED','AWARDED','NOT_SELECTED')", name="ck_rfq_supplier_status"),
        sa.CheckConstraint("quoted_total IS NULL OR quoted_total >= 0", name="ck_rfq_supplier_total"),
    )
    op.execute(
        "INSERT INTO permissions (id,code,description,risk_level,created_at) VALUES "
        "(gen_random_uuid(),'procurement.read','Read procurement documents','LOW',now()),"
        "(gen_random_uuid(),'purchase_request.manage','Manage purchase requests','MEDIUM',now()),"
        "(gen_random_uuid(),'rfq.manage','Manage RFQ and supplier responses','MEDIUM',now()),"
        "(gen_random_uuid(),'purchase_order.manage','Manage purchase orders','MEDIUM',now()),"
        "(gen_random_uuid(),'purchase_order.approve','Approve purchase orders','HIGH',now()),"
        "(gen_random_uuid(),'purchase_order.override','Hold or cancel purchase orders','HIGH',now()),"
        "(gen_random_uuid(),'procurement.receive','Post procurement receipt and return','MEDIUM',now()) "
        "ON CONFLICT (code) DO NOTHING"
    )


def downgrade():
    op.drop_table("procurement_rfq_suppliers")
    op.drop_table("procurement_rfqs")
    op.drop_table("purchase_request_lines")
    op.drop_table("purchase_requests")
