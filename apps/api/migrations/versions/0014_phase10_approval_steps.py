from alembic import op
import sqlalchemy as sa

revision = "0014_phase10_approval_steps"
down_revision = "0013_phase10_approvals"


def upgrade():
    op.create_table("approval_policy_steps",
        sa.Column("id",sa.Uuid(),primary_key=True),
        sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("policy_id",sa.Uuid(),nullable=False),
        sa.Column("step_number",sa.Integer(),nullable=False),
        sa.Column("name",sa.String(160),nullable=False),
        sa.Column("required_permission",sa.String(120),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","policy_id"],["approval_policies.tenant_id","approval_policies.id"],ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id","id"),
        sa.UniqueConstraint("tenant_id","policy_id","step_number"),
        sa.CheckConstraint("step_number > 0",name="ck_approval_policy_step_number"))


def downgrade():
    op.drop_table("approval_policy_steps")
