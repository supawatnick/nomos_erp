from alembic import op
import sqlalchemy as sa

revision = "0002_phase2_saas_core"
down_revision = "0001_phase1_baseline"

def upgrade():
    op.create_table("tenants",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), sa.Column("status", sa.String(24), nullable=False),
        sa.Column("default_locale", sa.String(16), nullable=False), sa.Column("default_timezone", sa.String(64), nullable=False),
        sa.Column("base_currency", sa.CHAR(3), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("uq_tenants_slug_lower","tenants",[sa.text("lower(slug)")],unique=True)
    op.create_table("users",
        sa.Column("id",sa.Uuid(),primary_key=True), sa.Column("email",sa.String(320),nullable=False),
        sa.Column("password_hash",sa.Text(),nullable=False), sa.Column("display_name",sa.String(200),nullable=False),
        sa.Column("status",sa.String(24),nullable=False), sa.Column("locale",sa.String(16)),
        sa.Column("last_login_at",sa.DateTime(timezone=True)), sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("uq_users_email_lower","users",[sa.text("lower(email)")],unique=True)
    op.create_table("legal_entities",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("code",sa.String(40),nullable=False),sa.Column("legal_name",sa.String(240),nullable=False),
        sa.Column("display_name",sa.String(240)),sa.Column("tax_id",sa.String(64)),sa.Column("registration_number",sa.String(80)),
        sa.Column("country_code",sa.CHAR(2),nullable=False),sa.Column("base_currency",sa.CHAR(3),nullable=False),
        sa.Column("timezone",sa.String(64),nullable=False),sa.Column("status",sa.String(24),nullable=False),
        sa.Column("archived_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]),sa.UniqueConstraint("tenant_id","id"),
        sa.UniqueConstraint("tenant_id","code"))
    op.create_table("branches",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("legal_entity_id",sa.Uuid(),nullable=False),sa.Column("code",sa.String(40),nullable=False),
        sa.Column("name",sa.String(200),nullable=False),sa.Column("timezone",sa.String(64)),
        sa.Column("status",sa.String(24),nullable=False),sa.Column("archived_at",sa.DateTime(timezone=True)),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","legal_entity_id"],["legal_entities.tenant_id","legal_entities.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","legal_entity_id","id"),
        sa.UniqueConstraint("tenant_id","legal_entity_id","code"))
    op.create_table("tenant_users",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("user_id",sa.Uuid(),nullable=False),sa.Column("employee_code",sa.String(64)),
        sa.Column("default_branch_id",sa.Uuid()),sa.Column("status",sa.String(24),nullable=False),
        sa.Column("joined_at",sa.DateTime(timezone=True),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]),sa.ForeignKeyConstraint(["user_id"],["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id","default_branch_id"],["branches.tenant_id","branches.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","user_id"))
    op.create_table("permissions",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("code",sa.String(120),nullable=False,unique=True),
        sa.Column("description",sa.String(300),nullable=False),sa.Column("risk_level",sa.String(16),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("roles",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("code",sa.String(80),nullable=False),sa.Column("name",sa.String(120),nullable=False),
        sa.Column("description",sa.String(300)),sa.Column("is_system",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("status",sa.String(24),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","code"))
    op.create_table("role_permissions",
        sa.Column("tenant_id",sa.Uuid(),nullable=False),sa.Column("role_id",sa.Uuid(),nullable=False),
        sa.Column("permission_id",sa.Uuid(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.PrimaryKeyConstraint("tenant_id","role_id","permission_id"),
        sa.ForeignKeyConstraint(["tenant_id","role_id"],["roles.tenant_id","roles.id"]),
        sa.ForeignKeyConstraint(["permission_id"],["permissions.id"]))
    op.create_table("tenant_user_roles",
        sa.Column("tenant_id",sa.Uuid(),nullable=False),sa.Column("tenant_user_id",sa.Uuid(),nullable=False),
        sa.Column("role_id",sa.Uuid(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.PrimaryKeyConstraint("tenant_id","tenant_user_id","role_id"),
        sa.ForeignKeyConstraint(["tenant_id","tenant_user_id"],["tenant_users.tenant_id","tenant_users.id"]),
        sa.ForeignKeyConstraint(["tenant_id","role_id"],["roles.tenant_id","roles.id"]))
    op.create_table("sessions",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("user_id",sa.Uuid(),nullable=False),
        sa.Column("token_hash",sa.Text(),nullable=False,unique=True),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("revoked_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("last_seen_at",sa.DateTime(timezone=True)),sa.Column("ip_hash",sa.Text()),
        sa.Column("user_agent_summary",sa.String(300)),sa.ForeignKeyConstraint(["user_id"],["users.id"]))
    op.create_table("idempotency_keys",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("scope",sa.String(120),nullable=False),sa.Column("idempotency_key",sa.String(200),nullable=False),
        sa.Column("request_fingerprint",sa.CHAR(64),nullable=False),sa.Column("status",sa.String(24),nullable=False),
        sa.Column("resource_type",sa.String(80)),sa.Column("resource_id",sa.Uuid()),sa.Column("response_code",sa.Integer()),
        sa.Column("response_body",sa.JSON()),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]),sa.UniqueConstraint("tenant_id","scope","idempotency_key"))
    op.create_table("audit_logs",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("occurred_at",sa.DateTime(timezone=True),nullable=False),sa.Column("actor_user_id",sa.Uuid()),
        sa.Column("actor_tenant_user_id",sa.Uuid()),sa.Column("action",sa.String(160),nullable=False),
        sa.Column("target_type",sa.String(100)),sa.Column("target_id",sa.Uuid()),sa.Column("channel",sa.String(16),nullable=False),
        sa.Column("request_id",sa.Uuid(),nullable=False),sa.Column("result",sa.String(24),nullable=False),
        sa.Column("metadata",sa.JSON(),nullable=False,server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]))
    op.create_table("outbox_events",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("aggregate_type",sa.String(100),nullable=False),sa.Column("aggregate_id",sa.Uuid(),nullable=False),
        sa.Column("event_type",sa.String(160),nullable=False),sa.Column("payload",sa.JSON(),nullable=False),
        sa.Column("occurred_at",sa.DateTime(timezone=True),nullable=False),sa.Column("available_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("published_at",sa.DateTime(timezone=True)),sa.Column("attempt_count",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("last_error",sa.Text()),sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]))
    op.create_index("ix_audit_tenant_time","audit_logs",["tenant_id","occurred_at"])
    op.create_index("ix_outbox_unpublished","outbox_events",["available_at"],postgresql_where=sa.text("published_at IS NULL"))

def downgrade():
    for table in ["outbox_events","audit_logs","idempotency_keys","sessions","tenant_user_roles","role_permissions","roles","permissions","tenant_users","branches","legal_entities","users","tenants"]:
        op.drop_table(table)
