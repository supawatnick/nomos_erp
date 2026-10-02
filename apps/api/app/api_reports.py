from datetime import date

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from sqlalchemy import create_engine

from app.api_master import trusted_context
from app.application.reporting import (
    REPORT_COLUMNS,
    ReportingError,
    export_csv,
    export_xlsx,
    run_report,
    serialize_rows,
)
from app.core.config import get_settings
from app.domain.security import require_permission

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


def _engine():
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def _context(request: Request, authorization: str | None, tenant: str | None):
    return trusted_context(request, authorization, tenant)


@router.get("")
def catalog(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    context = _context(request, authorization, x_tenant_id)
    require_permission(context, "report.read")
    return {"data": [{"code": code, "columns": columns} for code, columns in REPORT_COLUMNS.items()],
            "meta": {"request_id": str(context.request_id)}}


@router.get("/{report}")
def report_data(
    report: str, request: Request, start: date | None = None, end: date | None = None,
    limit: int = Query(default=200, ge=1, le=2000),
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    context = _context(request, authorization, x_tenant_id)
    try:
        with _engine().connect() as db:
            rows = run_report(db, context=context, report=report, start=start, end=end, limit=limit)
    except ReportingError as exc:
        raise HTTPException(422, detail={"code": "VALIDATION_FAILED", "message": str(exc)}) from exc
    return {"data": serialize_rows(rows),
            "meta": {"request_id": str(context.request_id), "limit": limit, "bounded": True}}


@router.get("/{report}/export")
def report_export(
    report: str, request: Request, format: str = Query(pattern="^(csv|xlsx)$"),
    start: date | None = None, end: date | None = None,
    limit: int = Query(default=2000, ge=1, le=2000),
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    context = _context(request, authorization, x_tenant_id)
    require_permission(context, "report.export")
    if report not in REPORT_COLUMNS:
        raise HTTPException(404, detail={"code": "RESOURCE_NOT_FOUND"})
    try:
        with _engine().connect() as db:
            rows = run_report(db, context=context, report=report, start=start, end=end, limit=limit)
    except ReportingError as exc:
        raise HTTPException(422, detail={"code": "VALIDATION_FAILED", "message": str(exc)}) from exc
    columns = REPORT_COLUMNS[report]
    if format == "csv":
        payload, media, suffix = export_csv(rows, columns), "text/csv; charset=utf-8", "csv"
    else:
        payload, media, suffix = export_xlsx(rows, columns), (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"), "xlsx"
    return Response(payload, media_type=media, headers={
        "Content-Disposition": f'attachment; filename="{report}.{suffix}"',
        "X-Report-Row-Count": str(len(rows)),
        "X-Report-Bounded": "true",
    })
