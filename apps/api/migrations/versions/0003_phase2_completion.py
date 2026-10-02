from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "0003_phase2_completion"
down_revision = "0002_phase2_saas_core"

PERMISSIONS = [
    ("tenant.read", "Read tenant settings", "LOW"),
    ("tenant.manage", "Manage tenant settings", "HIGH"),
    ("organization.read", "Read organization", "LOW"),
    ("organization.manage", "Manage organization", "HIGH"),
    ("user.read", "Read tenant users", "LOW"),
    ("user.manage", "Manage tenant users", "HIGH"),
    ("role.read", "Read roles", "LOW"),
    ("role.manage", "Manage roles and permissions", "HIGH"),
    ("audit.read", "Read audit log", "HIGH"),
]


def upgrade():
    op.create_table(
        "tenant_settings",
        sa.Column("tenant_id", sa.Uuid(), primary_key=True),
        sa.Column("settings_version", sa.Integer(), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index(
        "ix_sessions_active",
        "sessions",
        ["user_id", "expires_at"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("description", sa.String()),
        sa.column("risk_level", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    from datetime import UTC, datetime
    now = datetime.now(UTC)
    op.bulk_insert(
        permissions,
        [
            {
                "id": uuid4(),
                "code": code,
                "description": description,
                "risk_level": risk,
                "created_at": now,
            }
            for code, description, risk in PERMISSIONS
        ],
    )


def downgrade():
    op.drop_index("ix_sessions_active", table_name="sessions")
    op.drop_table("tenant_settings")
