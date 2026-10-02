from datetime import date, timedelta
from io import BytesIO

import pytest
from fastapi import HTTPException
from openpyxl import load_workbook
from sqlalchemy import create_engine, text
from test_phase4_inventory import ctx, seed

from app.application.reporting import (
    MAX_RANGE_DAYS,
    ReportingError,
    export_csv,
    export_xlsx,
    run_report,
)
from app.core.config import get_settings


@pytest.fixture
def engine():
    url = get_settings().database_url
    if not url.startswith("postgresql"):
        pytest.skip("Phase 11 acceptance requires PostgreSQL")
    value = create_engine(url, pool_pre_ping=True)
    try:
        yield value
    finally:
        value.dispose()


def report_ctx(tenant, permissions):
    base = ctx(tenant)
    return type(base)(
        request_id=base.request_id, actor_user_id=base.actor_user_id, tenant_id=tenant,
        tenant_user_id=base.tenant_user_id, permissions=frozenset(permissions),
    )


def test_report_catalog_is_allowlisted_and_unknown_report_rejected(engine):
    tenant, *_ = seed(engine)
    context = report_ctx(tenant, {"report.read"})
    with engine.connect() as db:
        with pytest.raises(ReportingError, match="unknown report"):
            run_report(db, context=context, report="select * from users")


def test_report_bounds_and_permission_are_enforced(engine):
    tenant, *_ = seed(engine)
    allowed = report_ctx(tenant, {"report.read"})
    denied = report_ctx(tenant, set())
    with engine.connect() as db:
        with pytest.raises(ReportingError, match="date range"):
            run_report(db, context=allowed, report="sales-orders",
                start=date.today()-timedelta(days=MAX_RANGE_DAYS+1), end=date.today())
        with pytest.raises(ReportingError, match="limit"):
            run_report(db, context=allowed, report="inventory-stock", limit=2001)
        with pytest.raises(HTTPException):
            run_report(db, context=denied, report="management-summary")


def test_management_report_is_tenant_isolated(engine):
    tenant, *_ = seed(engine)
    other, *_ = seed(engine)
    context = report_ctx(tenant, {"report.read"})
    with engine.begin() as db:
        db.execute(text("""INSERT INTO approval_policies
          (id,tenant_id,code,name,request_type,required_permission,steps_required,
           prohibit_self_approval,status,created_at,updated_at)
          VALUES (gen_random_uuid(),:other,'FOREIGN','Foreign','X','approval.decide',1,true,'ACTIVE',now(),now())"""),
          {"other": other})
        rows = run_report(db, context=context, report="management-summary")
    values = {row["metric"]: int(row["value"]) for row in rows}
    assert values["pending_approvals"] == 0


def test_csv_and_xlsx_neutralize_spreadsheet_formulas():
    rows = [{"name": "=HYPERLINK(\"bad\")", "amount": "-1", "safe": "plain"}]
    columns = ["name", "amount", "safe"]
    csv_payload = export_csv(rows, columns).decode("utf-8-sig")
    assert "'=HYPERLINK" in csv_payload
    assert "'-1" in csv_payload
    workbook = load_workbook(BytesIO(export_xlsx(rows, columns)), read_only=True)
    values = list(workbook.active.values)
    assert values[1] == ("'=HYPERLINK(\"bad\")", "'-1", "plain")
