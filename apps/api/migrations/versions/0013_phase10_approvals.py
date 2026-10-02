from alembic import op
import sqlalchemy as sa

revision = "0013_phase10_approvals"
down_revision = "0012_phase9_sales"


def upgrade():
    op.create_table("approval_policies",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("code",sa.String(80),nullable=False),sa.Column("name",sa.String(160),nullable=False),
        sa.Column("request_type",sa.String(80),nullable=False),sa.Column("required_permission",sa.String(120),nullable=False),
        sa.Column("steps_required",sa.Integer(),nullable=False,server_default="1"),
        sa.Column("prohibit_self_approval",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column("expires_after_hours",sa.Integer()),sa.Column("status",sa.String(16),nullable=False,server_default="ACTIVE"),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","code"),
        sa.CheckConstraint("steps_required > 0",name="ck_approval_policy_steps"),
        sa.CheckConstraint("expires_after_hours IS NULL OR expires_after_hours > 0",name="ck_approval_policy_expiry"),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')",name="ck_approval_policy_status"))

    op.create_table("approval_requests",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("policy_id",sa.Uuid(),nullable=False),sa.Column("request_type",sa.String(80),nullable=False),
        sa.Column("source_type",sa.String(80),nullable=False),sa.Column("source_id",sa.Uuid(),nullable=False),
        sa.Column("source_version",sa.Integer()),sa.Column("source_fingerprint",sa.String(64),nullable=False),
        sa.Column("request_snapshot",sa.JSON(),nullable=False),sa.Column("status",sa.String(16),nullable=False,server_default="PENDING"),
        sa.Column("requester_tenant_user_id",sa.Uuid(),nullable=False),sa.Column("current_step",sa.Integer(),nullable=False,server_default="1"),
        sa.Column("expires_at",sa.DateTime(timezone=True)),sa.Column("approved_at",sa.DateTime(timezone=True)),
        sa.Column("executed_at",sa.DateTime(timezone=True)),sa.Column("execution_reference",sa.String(200)),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","policy_id"],["approval_policies.tenant_id","approval_policies.id"]),
        sa.ForeignKeyConstraint(["tenant_id","requester_tenant_user_id"],["tenant_users.tenant_id","tenant_users.id"]),
        sa.UniqueConstraint("tenant_id","id"),
        sa.CheckConstraint("status IN ('PENDING','APPROVED','REJECTED','CANCELLED','EXPIRED','EXECUTED')",name="ck_approval_request_status"),
        sa.CheckConstraint("current_step > 0",name="ck_approval_request_step"))

    op.create_table("approval_decisions",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("approval_request_id",sa.Uuid(),nullable=False),sa.Column("step_number",sa.Integer(),nullable=False),
        sa.Column("decided_by_tenant_user_id",sa.Uuid(),nullable=False),sa.Column("decision",sa.String(16),nullable=False),
        sa.Column("reason",sa.Text()),sa.Column("idempotency_key",sa.String(200),nullable=False),
        sa.Column("decided_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","approval_request_id"],["approval_requests.tenant_id","approval_requests.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id","decided_by_tenant_user_id"],["tenant_users.tenant_id","tenant_users.id"]),
        sa.UniqueConstraint("tenant_id","id"),sa.UniqueConstraint("tenant_id","approval_request_id","idempotency_key"),
        sa.UniqueConstraint("tenant_id","approval_request_id","step_number"),
        sa.CheckConstraint("decision IN ('APPROVED','REJECTED')",name="ck_approval_decision_value"),
        sa.CheckConstraint("step_number > 0",name="ck_approval_decision_step"))

    op.create_index("ix_approval_requests_inbox","approval_requests",["tenant_id","status","created_at"])
    op.create_index("ix_approval_requests_source","approval_requests",["tenant_id","source_type","source_id"])

    op.execute("""INSERT INTO permissions (id,code,description,risk_level,created_at) VALUES
      (gen_random_uuid(),'approval.read','Read approval requests and decisions','LOW',now()),
      (gen_random_uuid(),'approval.request','Create and cancel approval requests','MEDIUM',now()),
      (gen_random_uuid(),'approval.decide','Approve or reject eligible approval requests','HIGH',now()),
      (gen_random_uuid(),'approval.policy.manage','Manage approval policies','HIGH',now())
      ON CONFLICT (code) DO NOTHING""")


def downgrade():
    op.drop_index("ix_approval_requests_source",table_name="approval_requests")
    op.drop_index("ix_approval_requests_inbox",table_name="approval_requests")
    op.drop_table("approval_decisions")
    op.drop_table("approval_requests")
    op.drop_table("approval_policies")
