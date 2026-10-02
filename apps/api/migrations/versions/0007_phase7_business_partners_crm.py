from alembic import op
import sqlalchemy as sa

revision="0007_phase7_crm"
down_revision="0006_phase6_inventory_operations"


def upgrade():
    op.create_table("business_partners",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("code",sa.String(64),nullable=False),sa.Column("name",sa.String(240),nullable=False),
        sa.Column("legal_name",sa.String(240)),sa.Column("tax_id",sa.String(64)),
        sa.Column("is_customer",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("is_supplier",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("status",sa.String(16),nullable=False,server_default="ACTIVE"),
        sa.Column("owner_tenant_user_id",sa.Uuid()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","owner_tenant_user_id"],["tenant_users.tenant_id","tenant_users.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","code"),
        sa.CheckConstraint("is_customer OR is_supplier",name="ck_partner_has_role"),
        sa.CheckConstraint("status IN ('ACTIVE','ARCHIVED')",name="ck_partner_status"))
    op.create_table("partner_contacts",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("partner_id",sa.Uuid(),nullable=False),sa.Column("name",sa.String(200),nullable=False),
        sa.Column("email",sa.String(320)),sa.Column("phone",sa.String(64)),sa.Column("position",sa.String(120)),
        sa.Column("is_primary",sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","partner_id"],["business_partners.tenant_id","business_partners.id"],ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id","id"))
    op.create_table("partner_addresses",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("partner_id",sa.Uuid(),nullable=False),sa.Column("address_type",sa.String(24),nullable=False),
        sa.Column("line1",sa.String(240),nullable=False),sa.Column("line2",sa.String(240)),
        sa.Column("district",sa.String(160)),sa.Column("province",sa.String(160)),sa.Column("postal_code",sa.String(32)),
        sa.Column("country_code",sa.String(2),nullable=False,server_default="TH"),sa.Column("is_primary",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","partner_id"],["business_partners.tenant_id","business_partners.id"],ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id","id"),sa.CheckConstraint("address_type IN ('BILLING','SHIPPING','OFFICE','OTHER')",name="ck_partner_address_type"))
    op.create_table("crm_leads",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("lead_number",sa.String(80),nullable=False),sa.Column("name",sa.String(240),nullable=False),
        sa.Column("company_name",sa.String(240)),sa.Column("email",sa.String(320)),sa.Column("phone",sa.String(64)),
        sa.Column("status",sa.String(24),nullable=False,server_default="OPEN"),sa.Column("partner_id",sa.Uuid()),
        sa.Column("owner_tenant_user_id",sa.Uuid()),sa.Column("source",sa.String(120)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","partner_id"],["business_partners.tenant_id","business_partners.id"]),
        sa.ForeignKeyConstraint(["tenant_id","owner_tenant_user_id"],["tenant_users.tenant_id","tenant_users.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","lead_number"),
        sa.CheckConstraint("status IN ('OPEN','QUALIFIED','WON','LOST','CANCELLED')",name="ck_crm_lead_status"))
    op.create_table("crm_opportunities",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("opportunity_number",sa.String(80),nullable=False),sa.Column("name",sa.String(240),nullable=False),
        sa.Column("lead_id",sa.Uuid()),sa.Column("partner_id",sa.Uuid()),sa.Column("owner_tenant_user_id",sa.Uuid()),
        sa.Column("status",sa.String(24),nullable=False,server_default="OPEN"),sa.Column("currency_code",sa.String(3),nullable=False,server_default="THB"),
        sa.Column("estimated_amount",sa.Numeric(24,8),nullable=False,server_default="0"),sa.Column("expected_close_date",sa.Date()),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","lead_id"],["crm_leads.tenant_id","crm_leads.id"]),
        sa.ForeignKeyConstraint(["tenant_id","partner_id"],["business_partners.tenant_id","business_partners.id"]),
        sa.ForeignKeyConstraint(["tenant_id","owner_tenant_user_id"],["tenant_users.tenant_id","tenant_users.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","opportunity_number"),
        sa.CheckConstraint("status IN ('OPEN','QUALIFIED','WON','LOST','CANCELLED')",name="ck_crm_opportunity_status"),
        sa.CheckConstraint("estimated_amount >= 0",name="ck_crm_opportunity_amount"))
    op.create_table("crm_activities",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("partner_id",sa.Uuid()),sa.Column("lead_id",sa.Uuid()),sa.Column("opportunity_id",sa.Uuid()),
        sa.Column("activity_type",sa.String(24),nullable=False),sa.Column("subject",sa.String(240),nullable=False),
        sa.Column("note",sa.Text()),sa.Column("owner_tenant_user_id",sa.Uuid()),sa.Column("occurred_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","partner_id"],["business_partners.tenant_id","business_partners.id"]),
        sa.ForeignKeyConstraint(["tenant_id","lead_id"],["crm_leads.tenant_id","crm_leads.id"]),
        sa.ForeignKeyConstraint(["tenant_id","opportunity_id"],["crm_opportunities.tenant_id","crm_opportunities.id"]),
        sa.ForeignKeyConstraint(["tenant_id","owner_tenant_user_id"],["tenant_users.tenant_id","tenant_users.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.CheckConstraint("activity_type IN ('NOTE','CALL','EMAIL','MEETING','TASK')",name="ck_crm_activity_type"),
        sa.CheckConstraint("(partner_id IS NOT NULL) OR (lead_id IS NOT NULL) OR (opportunity_id IS NOT NULL)",name="ck_crm_activity_target"))
    op.execute("INSERT INTO permissions (id,code,description,risk_level,created_at) VALUES "
      "(gen_random_uuid(),'partner.read','Read business partners','LOW',now()),"
      "(gen_random_uuid(),'partner.manage','Manage business partners','MEDIUM',now()),"
      "(gen_random_uuid(),'crm.read','Read CRM','LOW',now()),"
      "(gen_random_uuid(),'crm.manage','Manage CRM','MEDIUM',now()) ON CONFLICT (code) DO NOTHING")


def downgrade():
    op.drop_table("crm_activities");op.drop_table("crm_opportunities");op.drop_table("crm_leads")
    op.drop_table("partner_addresses");op.drop_table("partner_contacts");op.drop_table("business_partners")
