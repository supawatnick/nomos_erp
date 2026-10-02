from alembic import op

revision = "0015_phase11_reporting"
down_revision = "0014_phase10_approval_steps"


def upgrade():
    op.execute("""INSERT INTO permissions (id,code,description,risk_level,created_at) VALUES
      (gen_random_uuid(),'report.read','Read bounded operational reports','LOW',now()),
      (gen_random_uuid(),'report.export','Export bounded operational reports','MEDIUM',now())
      ON CONFLICT (code) DO UPDATE SET description=EXCLUDED.description,risk_level=EXCLUDED.risk_level""")


def downgrade():
    op.execute("DELETE FROM permissions WHERE code IN ('report.read','report.export')")
