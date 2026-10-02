from alembic import op
import sqlalchemy as sa

revision = "0004_phase3_catalog_warehouse"
down_revision = "0003_phase2_completion"


def upgrade():
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid()),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.ForeignKeyConstraint(["tenant_id", "parent_id"], ["categories.tenant_id", "categories.id"]),
    )
    op.create_index("ix_categories_tenant_status", "categories", ["tenant_id", "status"])

    op.create_table(
        "units",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("symbol", sa.String(24)),
        sa.Column("precision", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.CheckConstraint("precision BETWEEN 0 AND 8", name="ck_units_precision"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category_id", sa.Uuid()),
        sa.Column("product_type", sa.String(24), nullable=False),
        sa.Column("base_unit_id", sa.Uuid(), nullable=False),
        sa.Column("tracking_type", sa.String(16), nullable=False, server_default="NONE"),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "category_id"], ["categories.tenant_id", "categories.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "base_unit_id"], ["units.tenant_id", "units.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "sku"),
        sa.CheckConstraint("product_type IN ('STOCKABLE','CONSUMABLE','SERVICE')", name="ck_products_type"),
        sa.CheckConstraint("tracking_type IN ('NONE','LOT','SERIAL')", name="ck_products_tracking"),
    )
    op.create_index("ix_products_tenant_status", "products", ["tenant_id", "status"])
    op.create_index("ix_products_tenant_category", "products", ["tenant_id", "category_id"])

    op.create_table(
        "product_units",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("factor_to_base", sa.Numeric(24, 8), nullable=False),
        sa.Column("is_purchase_unit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_sales_unit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "unit_id"], ["units.tenant_id", "units.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "product_id", "unit_id"),
        sa.CheckConstraint("factor_to_base > 0", name="ck_product_units_factor"),
    )
    op.create_table(
        "product_barcodes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("product_unit_id", sa.Uuid()),
        sa.Column("barcode", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "product_unit_id"], ["product_units.tenant_id", "product_units.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "barcode"),
    )

    op.create_table(
        "warehouses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("legal_entity_id", sa.Uuid(), nullable=False),
        sa.Column("branch_id", sa.Uuid()),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "legal_entity_id"], ["legal_entities.tenant_id", "legal_entities.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "legal_entity_id", "branch_id"],
            ["branches.tenant_id", "branches.legal_entity_id", "branches.id"],
        ),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "code"),
    )
    op.create_index("ix_warehouses_tenant_branch_status", "warehouses", ["tenant_id", "branch_id", "status"])

    op.create_table(
        "warehouse_locations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("warehouse_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid()),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("location_type", sa.String(24), nullable=False, server_default="STORAGE"),
        sa.Column("allow_stock", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "warehouse_id"], ["warehouses.tenant_id", "warehouses.id"]),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "warehouse_id", "id"),
        sa.UniqueConstraint("tenant_id", "warehouse_id", "code"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "warehouse_id", "parent_id"],
            ["warehouse_locations.tenant_id", "warehouse_locations.warehouse_id", "warehouse_locations.id"],
        ),
    )
    op.create_index("ix_locations_tenant_warehouse_status", "warehouse_locations", ["tenant_id", "warehouse_id", "status"])

    op.create_table(
        "document_sequences",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(64), nullable=False),
        sa.Column("legal_entity_id", sa.Uuid()),
        sa.Column("branch_id", sa.Uuid()),
        sa.Column("period_key", sa.String(32), nullable=False),
        sa.Column("prefix", sa.String(40), nullable=False),
        sa.Column("next_value", sa.BigInteger(), nullable=False),
        sa.Column("padding", sa.SmallInteger(), nullable=False, server_default="6"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "legal_entity_id"], ["legal_entities.tenant_id", "legal_entities.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "legal_entity_id", "branch_id"],
            ["branches.tenant_id", "branches.legal_entity_id", "branches.id"],
        ),
        sa.CheckConstraint("next_value > 0", name="ck_document_sequences_next"),
        sa.CheckConstraint("padding BETWEEN 1 AND 12", name="ck_document_sequences_padding"),
    )
    op.create_index(
        "uq_document_sequences_scope",
        "document_sequences",
        ["tenant_id", "document_type", "legal_entity_id", "branch_id", "period_key"],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )

    op.execute(
        "INSERT INTO permissions (id,code,description,risk_level,created_at) VALUES "
        "(gen_random_uuid(),'product.read','Read products categories and units','LOW',now()),"
        "(gen_random_uuid(),'product.manage','Manage products categories units and barcodes','MEDIUM',now()),"
        "(gen_random_uuid(),'warehouse.read','Read warehouses and locations','LOW',now()),"
        "(gen_random_uuid(),'warehouse.manage','Manage warehouses and locations','HIGH',now()) "
        "ON CONFLICT (code) DO NOTHING"
    )


def downgrade():
    for table in [
        "document_sequences",
        "warehouse_locations",
        "warehouses",
        "product_barcodes",
        "product_units",
        "products",
        "units",
        "categories",
    ]:
        op.drop_table(table)
