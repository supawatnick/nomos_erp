from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.application.catalog import CatalogRepository, validate_conversion
from app.application.numbering import allocate_document_number
from app.application.warehouse import validate_location_parent
from app.core.config import get_settings


@pytest.fixture
def db():
    engine = create_engine(get_settings().database_url)
    connection = engine.connect()
    tx = connection.begin()
    try:
        yield connection
    finally:
        tx.rollback()
        connection.close()
        engine.dispose()


def tenant(db, name: str):
    now, tenant_id = datetime.now(UTC), uuid4()
    db.execute(
        text("INSERT INTO tenants (id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at) VALUES (:id,:slug,:name,'ACTIVE','th-TH','Asia/Bangkok','THB',:now,:now)"),
        {"id": tenant_id, "slug": name + "-" + tenant_id.hex, "name": name, "now": now},
    )
    return tenant_id


def unit(db, tenant_id):
    now, unit_id = datetime.now(UTC), uuid4()
    db.execute(
        text("INSERT INTO units (id,tenant_id,code,name,precision,status,created_at,updated_at) VALUES (:id,:tenant,'EA','Each',0,'ACTIVE',:now,:now)"),
        {"id": unit_id, "tenant": tenant_id, "now": now},
    )
    return unit_id


def organization(db, tenant_id):
    now, entity_id, branch_id = datetime.now(UTC), uuid4(), uuid4()
    db.execute(
        text("INSERT INTO legal_entities (id,tenant_id,code,legal_name,country_code,base_currency,timezone,status,created_at,updated_at) VALUES (:id,:tenant,'LE','Legal','TH','THB','Asia/Bangkok','ACTIVE',:now,:now)"),
        {"id": entity_id, "tenant": tenant_id, "now": now},
    )
    db.execute(
        text("INSERT INTO branches (id,tenant_id,legal_entity_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:entity,'B','Branch','ACTIVE',:now,:now)"),
        {"id": branch_id, "tenant": tenant_id, "entity": entity_id, "now": now},
    )
    return entity_id, branch_id


def test_catalog_same_tenant_and_duplicate_constraints(db):
    now = datetime.now(UTC)
    a, b = tenant(db, "catalog-a"), tenant(db, "catalog-b")
    unit_a, unit_b = unit(db, a), unit(db, b)
    product_id = uuid4()
    db.execute(
        text("INSERT INTO products (id,tenant_id,sku,name,product_type,base_unit_id,tracking_type,status,created_at,updated_at) VALUES (:id,:tenant,'SKU-1','One','STOCKABLE',:unit,'NONE','ACTIVE',:now,:now)"),
        {"id": product_id, "tenant": a, "unit": unit_a, "now": now},
    )
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(
            text("INSERT INTO products (id,tenant_id,sku,name,product_type,base_unit_id,tracking_type,status,created_at,updated_at) VALUES (:id,:tenant,'SKU-1','Dup','STOCKABLE',:unit,'NONE','ACTIVE',:now,:now)"),
            {"id": uuid4(), "tenant": a, "unit": unit_a, "now": now},
        )
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(
            text("INSERT INTO products (id,tenant_id,sku,name,product_type,base_unit_id,tracking_type,status,created_at,updated_at) VALUES (:id,:tenant,'SKU-X','Cross','STOCKABLE',:unit,'NONE','ACTIVE',:now,:now)"),
            {"id": uuid4(), "tenant": a, "unit": unit_b, "now": now},
        )
    assert CatalogRepository().get_product(db, b, product_id) is None


def test_exact_conversion_validation():
    validate_conversion(Decimal("1.25000000"))
    with pytest.raises(ValueError):
        validate_conversion(Decimal("0"))
    with pytest.raises(ValueError):
        validate_conversion(Decimal("1.000000001"))


def test_warehouse_branch_legal_entity_mismatch_rejected(db):
    now = datetime.now(UTC)
    tenant_id = tenant(db, "warehouse")
    entity_a, _ = organization(db, tenant_id)
    entity_b, branch_b = organization(db, tenant_id)
    assert entity_a != entity_b
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(
            text("INSERT INTO warehouses (id,tenant_id,legal_entity_id,branch_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:entity,:branch,'WH','Mismatch','ACTIVE',:now,:now)"),
            {"id": uuid4(), "tenant": tenant_id, "entity": entity_a, "branch": branch_b, "now": now},
        )


def test_location_cross_warehouse_parent_and_cycle_rejected(db):
    now = datetime.now(UTC)
    tenant_id = tenant(db, "location")
    entity_id, branch_id = organization(db, tenant_id)
    wh1, wh2, root, child = uuid4(), uuid4(), uuid4(), uuid4()
    for wid, code in ((wh1, "W1"), (wh2, "W2")):
        db.execute(
            text("INSERT INTO warehouses (id,tenant_id,legal_entity_id,branch_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:entity,:branch,:code,:code,'ACTIVE',:now,:now)"),
            {"id": wid, "tenant": tenant_id, "entity": entity_id, "branch": branch_id, "code": code, "now": now},
        )
    db.execute(
        text("INSERT INTO warehouse_locations (id,tenant_id,warehouse_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:wh,'ROOT','Root','ACTIVE',:now,:now)"),
        {"id": root, "tenant": tenant_id, "wh": wh1, "now": now},
    )
    db.execute(
        text("INSERT INTO warehouse_locations (id,tenant_id,warehouse_id,parent_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:wh,:parent,'CHILD','Child','ACTIVE',:now,:now)"),
        {"id": child, "tenant": tenant_id, "wh": wh1, "parent": root, "now": now},
    )
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(
            text("INSERT INTO warehouse_locations (id,tenant_id,warehouse_id,parent_id,code,name,status,created_at,updated_at) VALUES (:id,:tenant,:wh,:parent,'BAD','Bad','ACTIVE',:now,:now)"),
            {"id": uuid4(), "tenant": tenant_id, "wh": wh2, "parent": root, "now": now},
        )
    with pytest.raises(ValueError):
        validate_location_parent(db, tenant_id=tenant_id, warehouse_id=wh1, location_id=root, parent_id=child)


def test_document_sequence_is_scoped_and_incremented(db):
    now = datetime.now(UTC)
    tenant_id = tenant(db, "number")
    seq_id = uuid4()
    db.execute(
        text("INSERT INTO document_sequences (id,tenant_id,document_type,period_key,prefix,next_value,padding,updated_at) VALUES (:id,:tenant,'TRANSFER','2026','TR-2026-',1,6,:now)"),
        {"id": seq_id, "tenant": tenant_id, "now": now},
    )
    first = allocate_document_number(db, tenant_id=tenant_id, document_type="TRANSFER", period_key="2026")
    second = allocate_document_number(db, tenant_id=tenant_id, document_type="TRANSFER", period_key="2026")
    assert first == "TR-2026-000001"
    assert second == "TR-2026-000002"


def test_archive_keeps_stable_product_id(db):
    now = datetime.now(UTC)
    tenant_id = tenant(db, "archive")
    unit_id = unit(db, tenant_id)
    product_id = uuid4()
    db.execute(
        text("INSERT INTO products (id,tenant_id,sku,name,product_type,base_unit_id,tracking_type,status,created_at,updated_at) VALUES (:id,:tenant,'STABLE','Stable','STOCKABLE',:unit,'NONE','ACTIVE',:now,:now)"),
        {"id": product_id, "tenant": tenant_id, "unit": unit_id, "now": now},
    )
    assert CatalogRepository().archive_product(db, tenant_id, product_id)
    row = CatalogRepository().get_product(db, tenant_id, product_id)
    assert row is not None and row["id"] == product_id and row["status"] == "ARCHIVED"
