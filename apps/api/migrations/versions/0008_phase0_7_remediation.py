from alembic import op
import sqlalchemy as sa

revision = "0008_phase0_7_remediation"
down_revision = "0007_phase7_crm"


def upgrade():
    op.create_table(
        "import_batches",
        sa.Column("id",sa.Uuid(),primary_key=True),
        sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("import_type",sa.String(32),nullable=False),
        sa.Column("status",sa.String(32),nullable=False),
        sa.Column("source_name",sa.String(240),nullable=False),
        sa.Column("created_by_user_id",sa.Uuid(),nullable=False),
        sa.Column("total_rows",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("valid_rows",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("error_rows",sa.Integer(),nullable=False,server_default="0"),
        sa.Column("committed_transaction_id",sa.Uuid()),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("committed_at",sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"],["users.id"]),
        sa.UniqueConstraint("tenant_id","id"),
        sa.CheckConstraint("import_type IN ('PRODUCT','OPENING_STOCK')",name="ck_import_batch_type"),
    )
    op.create_table(
        "import_rows",
        sa.Column("id",sa.Uuid(),primary_key=True),
        sa.Column("tenant_id",sa.Uuid(),nullable=False),
        sa.Column("batch_id",sa.Uuid(),nullable=False),
        sa.Column("row_number",sa.Integer(),nullable=False),
        sa.Column("source_data",sa.JSON(),nullable=False),
        sa.Column("normalized_data",sa.JSON(),nullable=False,server_default=sa.text("'{}'::jsonb")),
        sa.Column("errors",sa.JSON(),nullable=False,server_default=sa.text("'[]'::jsonb")),
        sa.Column("target_id",sa.Uuid()),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id","batch_id"],["import_batches.tenant_id","import_batches.id"],ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id","batch_id","row_number"),
    )
    op.create_index("ix_import_batches_tenant_status","import_batches",["tenant_id","status"])


def downgrade():
    op.drop_index("ix_import_batches_tenant_status",table_name="import_batches")
    op.drop_table("import_rows")
    op.drop_table("import_batches")
