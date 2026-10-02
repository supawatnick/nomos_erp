from alembic import op
import sqlalchemy as sa

revision="0019_phase14_commercial_saas"
down_revision="0018_phase12_posting_rules"

def upgrade():
    op.create_table("saas_plans",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("code",sa.String(40),nullable=False,unique=True),
      sa.Column("name",sa.String(120),nullable=False),sa.Column("status",sa.String(24),nullable=False),
      sa.Column("trial_days",sa.Integer(),nullable=False,server_default="0"),sa.Column("retention_days",sa.Integer(),nullable=False,server_default="30"),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.CheckConstraint("status IN ('ACTIVE','ARCHIVED')",name="ck_saas_plan_status"),
      sa.CheckConstraint("trial_days>=0 AND retention_days>=0",name="ck_saas_plan_days"))
    op.create_table("saas_plan_entitlements",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("plan_id",sa.Uuid(),nullable=False),
      sa.Column("feature_code",sa.String(100),nullable=False),sa.Column("limit_value",sa.BigInteger()),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(["plan_id"],["saas_plans.id"]),sa.UniqueConstraint("plan_id","feature_code"),
      sa.CheckConstraint("limit_value IS NULL OR limit_value>=0",name="ck_saas_entitlement_limit"))
    op.create_table("saas_subscriptions",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False,unique=True),
      sa.Column("plan_id",sa.Uuid(),nullable=False),sa.Column("status",sa.String(24),nullable=False),
      sa.Column("trial_ends_at",sa.DateTime(timezone=True)),sa.Column("current_period_ends_at",sa.DateTime(timezone=True)),
      sa.Column("cancelled_at",sa.DateTime(timezone=True)),sa.Column("retention_until",sa.DateTime(timezone=True)),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]),sa.ForeignKeyConstraint(["plan_id"],["saas_plans.id"]),
      sa.CheckConstraint("status IN ('TRIAL','ACTIVE','SUSPENDED','CANCELLED')",name="ck_saas_subscription_status"))
    op.create_table("saas_usage_counters",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
      sa.Column("feature_code",sa.String(100),nullable=False),sa.Column("period_key",sa.String(32),nullable=False),
      sa.Column("usage_value",sa.BigInteger(),nullable=False,server_default="0"),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
      sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]),sa.UniqueConstraint("tenant_id","feature_code","period_key"),
      sa.CheckConstraint("usage_value>=0",name="ck_saas_usage_nonnegative"))
    op.create_table("saas_exports",
      sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
      sa.Column("requested_by_tenant_user_id",sa.Uuid(),nullable=False),sa.Column("status",sa.String(24),nullable=False),
      sa.Column("requested_at",sa.DateTime(timezone=True),nullable=False),sa.Column("completed_at",sa.DateTime(timezone=True)),
      sa.Column("expires_at",sa.DateTime(timezone=True)),sa.Column("object_key",sa.String(500)),
      sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]),
      sa.ForeignKeyConstraint(["tenant_id","requested_by_tenant_user_id"],["tenant_users.tenant_id","tenant_users.id"]),
      sa.UniqueConstraint("tenant_id","id"),
      sa.CheckConstraint("status IN ('REQUESTED','PROCESSING','READY','EXPIRED','FAILED')",name="ck_saas_export_status"))
    op.execute("""INSERT INTO permissions (id,code,description,risk_level,created_at) VALUES
      (gen_random_uuid(),'subscription.read','Read tenant subscription and entitlements','LOW',now()),
      (gen_random_uuid(),'subscription.manage','Manage tenant commercial lifecycle','HIGH',now()),
      (gen_random_uuid(),'tenant.export','Request tenant data export','HIGH',now())
      ON CONFLICT (code) DO NOTHING""")

def downgrade():
    for t in ["saas_exports","saas_usage_counters","saas_subscriptions","saas_plan_entitlements","saas_plans"]: op.drop_table(t)
