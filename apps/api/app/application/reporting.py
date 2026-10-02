import csv
import io
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

from app.domain.security import RequestContext, require_permission

MAX_ROWS = 2000
MAX_RANGE_DAYS = 366


class ReportingError(ValueError):
    pass


REPORT_COLUMNS: dict[str, list[str]] = {
    "inventory-stock": ["sku", "product_name", "warehouse_code", "location_code", "on_hand"],
    "procurement-orders": ["order_number", "supplier_name", "status", "currency_code", "ordered_total",
                           "ordered_quantity", "received_quantity", "returned_quantity", "updated_at"],
    "sales-orders": ["order_number", "customer_name", "status", "currency_code", "order_total",
                     "ordered_quantity", "reserved_quantity", "delivered_quantity", "returned_quantity", "updated_at"],
    "crm-pipeline": ["stage", "opportunity_count", "pipeline_amount"],
    "management-summary": ["metric", "value"],
}


def _bounds(start: date | None, end: date | None, limit: int) -> tuple[date, date, int]:
    today = date.today()
    end = end or today
    start = start or end - timedelta(days=30)
    if start > end:
        raise ReportingError("start date must not be after end date")
    if (end - start).days > MAX_RANGE_DAYS:
        raise ReportingError(f"date range must not exceed {MAX_RANGE_DAYS} days")
    if limit < 1 or limit > MAX_ROWS:
        raise ReportingError(f"limit must be between 1 and {MAX_ROWS}")
    return start, end, limit


def run_report(
    db: Connection, *, context: RequestContext, report: str,
    start: date | None = None, end: date | None = None, limit: int = 200,
) -> list[dict[str, Any]]:
    require_permission(context, "report.read")
    start, end, limit = _bounds(start, end, limit)
    params = {"tenant": context.tenant_id, "start": start, "end": end + timedelta(days=1), "limit": limit}
    if report == "inventory-stock":
        sql = """SELECT p.sku,p.name product_name,w.code warehouse_code,l.code location_code,b.on_hand
          FROM inventory_balances b JOIN products p ON p.tenant_id=b.tenant_id AND p.id=b.product_id
          JOIN warehouse_locations l ON l.tenant_id=b.tenant_id AND l.id=b.location_id
          JOIN warehouses w ON w.tenant_id=l.tenant_id AND w.id=l.warehouse_id
          WHERE b.tenant_id=:tenant AND b.on_hand<>0 ORDER BY p.sku,l.code,b.id LIMIT :limit"""
    elif report == "procurement-orders":
        sql = """SELECT po.order_number,bp.name supplier_name,po.status,po.currency_code,
          COALESCE(sum(pol.line_total),0) ordered_total,COALESCE(sum(pol.ordered_quantity),0) ordered_quantity,
          COALESCE(sum(pol.received_quantity),0) received_quantity,COALESCE(sum(pol.returned_quantity),0) returned_quantity,
          po.updated_at FROM purchase_orders po JOIN business_partners bp ON bp.tenant_id=po.tenant_id AND bp.id=po.supplier_id
          LEFT JOIN purchase_order_lines pol ON pol.tenant_id=po.tenant_id AND pol.purchase_order_id=po.id
          WHERE po.tenant_id=:tenant AND po.updated_at>=:start AND po.updated_at<:end
          GROUP BY po.id,bp.name ORDER BY po.updated_at DESC,po.id LIMIT :limit"""
    elif report == "sales-orders":
        sql = """SELECT so.order_number,bp.name customer_name,so.status,so.currency_code,
          COALESCE(sum(sol.line_total),0) order_total,COALESCE(sum(sol.ordered_quantity),0) ordered_quantity,
          COALESCE(sum(sol.reserved_quantity),0) reserved_quantity,COALESCE(sum(sol.delivered_quantity),0) delivered_quantity,
          COALESCE(sum(sol.returned_quantity),0) returned_quantity,so.updated_at
          FROM sales_orders so JOIN business_partners bp ON bp.tenant_id=so.tenant_id AND bp.id=so.customer_id
          LEFT JOIN sales_order_lines sol ON sol.tenant_id=so.tenant_id AND sol.sales_order_id=so.id
          WHERE so.tenant_id=:tenant AND so.updated_at>=:start AND so.updated_at<:end
          GROUP BY so.id,bp.name ORDER BY so.updated_at DESC,so.id LIMIT :limit"""
    elif report == "crm-pipeline":
        sql = """SELECT stage,count(*) opportunity_count,COALESCE(sum(amount),0) pipeline_amount
          FROM crm_opportunities WHERE tenant_id=:tenant AND updated_at>=:start AND updated_at<:end
          GROUP BY stage ORDER BY stage LIMIT :limit"""
    elif report == "management-summary":
        sql = """SELECT metric,value FROM (
          SELECT 1 n,'stock_positions' metric,count(*)::numeric value FROM inventory_balances WHERE tenant_id=:tenant AND on_hand<>0
          UNION ALL SELECT 2,'open_purchase_orders',count(*)::numeric FROM purchase_orders WHERE tenant_id=:tenant AND status NOT IN ('CLOSED','CANCELLED','RECEIVED')
          UNION ALL SELECT 3,'open_sales_orders',count(*)::numeric FROM sales_orders WHERE tenant_id=:tenant AND status NOT IN ('CLOSED','CANCELLED')
          UNION ALL SELECT 4,'open_opportunities',count(*)::numeric FROM crm_opportunities WHERE tenant_id=:tenant AND stage NOT IN ('WON','LOST')
          UNION ALL SELECT 5,'pending_approvals',count(*)::numeric FROM approval_requests WHERE tenant_id=:tenant AND status='PENDING'
        ) x ORDER BY n LIMIT :limit"""
    else:
        raise ReportingError("unknown report")
    return [dict(row) for row in db.execute(text(sql), params).mappings().all()]


def serialize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        item: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, UUID):
                item[key] = str(value)
            elif isinstance(value, Decimal):
                item[key] = format(value, "f")
            elif hasattr(value, "isoformat") and value is not None:
                item[key] = value.isoformat()
            else:
                item[key] = value
        out.append(item)
    return out


def _safe_cell(value: Any) -> str:
    raw = "" if value is None else str(value)
    return "'" + raw if raw.startswith(("=", "+", "-", "@")) else raw


def export_csv(rows: list[dict[str, Any]], columns: list[str]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in serialize_rows(rows):
        writer.writerow({key: _safe_cell(row.get(key)) for key in columns})
    return output.getvalue().encode("utf-8-sig")
