from alembic import op
import sqlalchemy as sa
revision = '0001_phase1_baseline'
down_revision = None
def upgrade():
    op.create_table('system_metadata', sa.Column('key', sa.String(100), primary_key=True), sa.Column('value', sa.Text(), nullable=False))
def downgrade():
    op.drop_table('system_metadata')
