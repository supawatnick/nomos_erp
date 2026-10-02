import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.application.approvals import mark_executed, request_approval, require_approved_snapshot
from app.application.inventory import StockLine, post_procurement_inventory
from app.application.numbering import allocate_document_number
from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit, write_outbox


class ProcurementError(ValueError):
    pass


def _audit(db: Connection, ctx: RequestContext, action: str, target_type: str, target_id: UUID, metadata: dict | None = None) -> None:
    write_audit(db, tenant_id=ctx.tenant_id, request_id=ctx.request_id, action=action,
        actor_user_id=ctx.actor_user_id, actor_tenant_user_id=ctx.tenant_user_id,
        target_type=target_type, target_id=target_id, metadata=metadata or {})


def _product_unit_owned(db: Connection, tenant_id: UUID, product_id: UUID, unit_id: UUID) -> bool:
    return db.execute(text("""SELECT 1 FROM products p JOIN units u ON u.tenant_id=p.tenant_id
        WHERE p.tenant_id=:t AND p.id=:p AND u.id=:u AND p.status='ACTIVE' AND u.status='ACTIVE'
        AND (p.base_unit_id=:u OR EXISTS (
          SELECT 1 FROM product_units pu WHERE pu.tenant_id=:t AND pu.product_id=:p AND pu.unit_id=:u
        ))"""), {"t": tenant_id, "p": product_id, "u": unit_id}).first() is not None


def _allocate_tenant_document_number(db: Connection, tenant_id: UUID, document_type: str,
                                     period_key: str | None = None) -> str:
    period = period_key or str(datetime.now(UTC).year)
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
               {"key": f"{tenant_id}:{document_type}:{period}"})
    configured = db.execute(text("""SELECT 1 FROM document_sequences
        WHERE tenant_id=:t AND document_type=:type AND legal_entity_id IS NULL
          AND branch_id IS NULL AND period_key=:period"""),
        {"t": tenant_id, "type": document_type, "period": period}).first()
    if not configured:
        db.execute(text("""INSERT INTO document_sequences
            (id,tenant_id,document_type,legal_entity_id,branch_id,period_key,prefix,next_value,padding,updated_at)
            VALUES (:id,:t,:type,NULL,NULL,:period,:prefix,1,6,now())"""),
            {"id": uuid4(), "t": tenant_id, "type": document_type, "period": period,
             "prefix": f"{document_type}-{period}-"})
    return allocate_document_number(db, tenant_id=tenant_id, document_type=document_type, period_key=period)


def create_purchase_request(db: Connection, *, context: RequestContext, lines: list[dict],
                            needed_by: date | None = None, reason: str | None = None,
                            period_key: str | None = None, request_number: str | None = None) -> UUID:
    require_permission(context, "purchase_request.manage")
    if not lines:
        raise ProcurementError("purchase request requires at least one line")
    rid, now = uuid4(), datetime.now(UTC)
    request_number = _allocate_tenant_document_number(db, context.tenant_id, "PR", period_key)
    db.execute(text("""INSERT INTO purchase_requests
      (id,tenant_id,request_number,status,requested_by_tenant_user_id,needed_by,reason,version,created_at,updated_at)
      VALUES (:id,:t,:number,'DRAFT',:requester,:needed,:reason,1,:now,:now)"""),
      {"id": rid, "t": context.tenant_id, "number": request_number, "requester": context.tenant_user_id,
       "needed": needed_by, "reason": reason, "now": now})
    for index, line in enumerate(lines, 1):
        quantity = Decimal(str(line["quantity"]))
        if quantity <= 0:
            raise ProcurementError("quantity must be positive")
        product_id, unit_id = UUID(str(line["product_id"])), UUID(str(line["unit_id"]))
        if not _product_unit_owned(db, context.tenant_id, product_id, unit_id):
            raise ProcurementError("product or unit not found")
        db.execute(text("""INSERT INTO purchase_request_lines
          (id,tenant_id,purchase_request_id,line_number,product_id,unit_id,quantity,note)
          VALUES (:id,:t,:pr,:line,:product,:unit,:quantity,:note)"""),
          {"id": uuid4(), "t": context.tenant_id, "pr": rid, "line": index, "product": product_id,
           "unit": unit_id, "quantity": quantity, "note": line.get("note")})
    _audit(db, context, "procurement.request.created", "purchase_request", rid, {"request_number": request_number})
    write_outbox(db, tenant_id=context.tenant_id, event_type="procurement.request.created",
                 aggregate_type="purchase_request", aggregate_id=rid, payload={"request_number": request_number})
    return rid


def transition_purchase_request(db: Connection, *, context: RequestContext, request_id: UUID, status: str) -> None:
    require_permission(context, "purchase_request.manage")
    allowed = {
        "DRAFT": {"PENDING_APPROVAL", "CANCELLED"},
        "PENDING_APPROVAL": {"APPROVED", "REJECTED", "CANCELLED"},
        "APPROVED": {"SOURCING", "CANCELLED"},
        "SOURCING": {"CONVERTED", "CANCELLED"},
    }
    row = db.execute(text("SELECT status FROM purchase_requests WHERE tenant_id=:t AND id=:id FOR UPDATE"),
                     {"t": context.tenant_id, "id": request_id}).mappings().first()
    if not row:
        raise ProcurementError("purchase request not found")
    if status not in allowed.get(row["status"], set()):
        raise ProcurementError("invalid purchase request transition")
    db.execute(text("UPDATE purchase_requests SET status=:s,version=version+1,updated_at=:now WHERE tenant_id=:t AND id=:id"),
               {"s": status, "now": datetime.now(UTC), "t": context.tenant_id, "id": request_id})
    verb = {"PENDING_APPROVAL": "submitted", "APPROVED": "approved", "REJECTED": "rejected", "CANCELLED": "cancelled"}.get(status, "status_changed")
    _audit(db, context, f"procurement.request.{verb}", "purchase_request", request_id)


def create_rfq(db: Connection, *, context: RequestContext, supplier_ids: list[UUID],
               purchase_request_id: UUID | None = None, currency_code: str = "THB",
               response_due_date: date | None = None, period_key: str | None = None,
               rfq_number: str | None = None) -> UUID:
    require_permission(context, "rfq.manage")
    if not supplier_ids:
        raise ProcurementError("RFQ requires at least one supplier")
    if purchase_request_id is not None:
        pr = db.execute(text("SELECT status FROM purchase_requests WHERE tenant_id=:t AND id=:id"),
                        {"t": context.tenant_id, "id": purchase_request_id}).scalar_one_or_none()
        if pr not in {"APPROVED", "SOURCING"}:
            raise ProcurementError("approved purchase request not found")
    unique_suppliers = list(dict.fromkeys(supplier_ids))
    for supplier_id in unique_suppliers:
        ok = db.execute(text("""SELECT 1 FROM business_partners
            WHERE tenant_id=:t AND id=:id AND is_supplier AND status='ACTIVE'"""),
            {"t": context.tenant_id, "id": supplier_id}).first()
        if not ok:
            raise ProcurementError("supplier not found")
    rfq_id, now = uuid4(), datetime.now(UTC)
    rfq_number = _allocate_tenant_document_number(db, context.tenant_id, "RFQ", period_key)
    db.execute(text("""INSERT INTO procurement_rfqs
      (id,tenant_id,rfq_number,purchase_request_id,status,currency_code,response_due_date,version,created_at,updated_at)
      VALUES (:id,:t,:number,:pr,'DRAFT',:currency,:due,1,:now,:now)"""),
      {"id": rfq_id, "t": context.tenant_id, "number": rfq_number, "pr": purchase_request_id,
       "currency": currency_code.upper(), "due": response_due_date, "now": now})
    for supplier_id in unique_suppliers:
        db.execute(text("""INSERT INTO procurement_rfq_suppliers
          (id,tenant_id,rfq_id,supplier_id,status) VALUES (:id,:t,:rfq,:supplier,'INVITED')"""),
          {"id": uuid4(), "t": context.tenant_id, "rfq": rfq_id, "supplier": supplier_id})
    if purchase_request_id is not None:
        pr_lines = db.execute(text("""SELECT id,line_number,product_id,unit_id,quantity
            FROM purchase_request_lines WHERE tenant_id=:t AND purchase_request_id=:pr ORDER BY line_number"""),
            {"t": context.tenant_id, "pr": purchase_request_id}).mappings().all()
        for line in pr_lines:
            db.execute(text("""INSERT INTO procurement_rfq_lines
                (id,tenant_id,rfq_id,line_number,purchase_request_line_id,product_id,unit_id,quantity)
                VALUES (:id,:t,:rfq,:line,:pr_line,:product,:unit,:quantity)"""),
                {"id": uuid4(), "t": context.tenant_id, "rfq": rfq_id, "line": line["line_number"],
                 "pr_line": line["id"], "product": line["product_id"], "unit": line["unit_id"],
                 "quantity": line["quantity"]})
    _audit(db, context, "procurement.rfq.created", "procurement_rfq", rfq_id, {"rfq_number": rfq_number})
    return rfq_id


def send_rfq(db: Connection, *, context: RequestContext, rfq_id: UUID) -> None:
    require_permission(context, "rfq.manage")
    status = db.execute(text("SELECT status FROM procurement_rfqs WHERE tenant_id=:t AND id=:id FOR UPDATE"),
                        {"t": context.tenant_id, "id": rfq_id}).scalar_one_or_none()
    if status is None:
        raise ProcurementError("RFQ not found")
    if status != "DRAFT":
        raise ProcurementError("RFQ must be DRAFT to send")
    db.execute(text("UPDATE procurement_rfqs SET status='SENT',version=version+1,updated_at=:now WHERE tenant_id=:t AND id=:id"),
               {"now": datetime.now(UTC), "t": context.tenant_id, "id": rfq_id})
    _audit(db, context, "procurement.rfq.sent", "procurement_rfq", rfq_id)


def record_supplier_quote(db: Connection, *, context: RequestContext, rfq_id: UUID, supplier_id: UUID,
                          quoted_total: Decimal | None = None, note: str | None = None,
                          lines: list[dict] | None = None) -> None:
    require_permission(context, "rfq.manage")
    rfq_status = db.execute(text("SELECT status FROM procurement_rfqs WHERE tenant_id=:t AND id=:id FOR UPDATE"),
                            {"t": context.tenant_id, "id": rfq_id}).scalar_one_or_none()
    if rfq_status not in {"SENT", "RESPONSES_RECEIVED"}:
        raise ProcurementError("RFQ is not accepting responses")
    supplier_row = db.execute(text("""SELECT id FROM procurement_rfq_suppliers
        WHERE tenant_id=:t AND rfq_id=:rfq AND supplier_id=:supplier"""),
        {"t": context.tenant_id, "rfq": rfq_id, "supplier": supplier_id}).mappings().first()
    if not supplier_row:
        raise ProcurementError("invited supplier not found")
    if lines is not None:
        if not lines:
            raise ProcurementError("supplier quote requires lines")
        db.execute(text("""DELETE FROM procurement_rfq_supplier_lines
            WHERE tenant_id=:t AND rfq_supplier_id=:supplier"""),
            {"t": context.tenant_id, "supplier": supplier_row["id"]})
        total = Decimal(0)
        seen: set[UUID] = set()
        for offered in lines:
            rfq_line_id = UUID(str(offered["rfq_line_id"]))
            if rfq_line_id in seen:
                raise ProcurementError("duplicate RFQ quote line")
            seen.add(rfq_line_id)
            rfq_line = db.execute(text("""SELECT quantity FROM procurement_rfq_lines
                WHERE tenant_id=:t AND rfq_id=:rfq AND id=:line"""),
                {"t": context.tenant_id, "rfq": rfq_id, "line": rfq_line_id}).mappings().first()
            quantity = Decimal(offered["offered_quantity"])
            price = Decimal(offered["unit_price"])
            discount = Decimal(offered.get("discount_amount", 0))
            tax = Decimal(offered.get("tax_amount", 0))
            if not rfq_line or quantity <= 0 or quantity > Decimal(rfq_line["quantity"]) or price < 0 or discount < 0 or tax < 0:
                raise ProcurementError("invalid supplier quote line")
            gross = quantity * price
            if discount > gross:
                raise ProcurementError("quote discount exceeds gross amount")
            line_total = gross - discount + tax
            total += line_total
            db.execute(text("""INSERT INTO procurement_rfq_supplier_lines
                (id,tenant_id,rfq_supplier_id,rfq_line_id,offered_quantity,unit_price,discount_amount,tax_amount,line_total)
                VALUES (:id,:t,:supplier,:line,:quantity,:price,:discount,:tax,:total)"""),
                {"id": uuid4(), "t": context.tenant_id, "supplier": supplier_row["id"], "line": rfq_line_id,
                 "quantity": quantity, "price": price, "discount": discount, "tax": tax, "total": line_total})
        quoted_total = total
    if quoted_total is None or quoted_total < 0:
        raise ProcurementError("quoted total cannot be negative")
    db.execute(text("""UPDATE procurement_rfq_suppliers
        SET status='RESPONDED',quoted_total=:total,quoted_at=:now,note=:note
        WHERE tenant_id=:t AND id=:id"""),
        {"total": quoted_total, "now": datetime.now(UTC), "note": note, "t": context.tenant_id,
         "id": supplier_row["id"]})
    if rfq_status == "SENT":
        db.execute(text("""UPDATE procurement_rfqs SET status='RESPONSES_RECEIVED',version=version+1,updated_at=:now
            WHERE tenant_id=:t AND id=:id"""), {"now": datetime.now(UTC), "t": context.tenant_id, "id": rfq_id})


def award_rfq(db: Connection, *, context: RequestContext, rfq_id: UUID, supplier_id: UUID) -> None:
    require_permission(context, "rfq.manage")
    status = db.execute(text("SELECT status FROM procurement_rfqs WHERE tenant_id=:t AND id=:id FOR UPDATE"),
                        {"t": context.tenant_id, "id": rfq_id}).scalar_one_or_none()
    if status != "RESPONSES_RECEIVED":
        raise ProcurementError("RFQ must have responses before award")
    chosen = db.execute(text("""SELECT 1 FROM procurement_rfq_suppliers
        WHERE tenant_id=:t AND rfq_id=:rfq AND supplier_id=:supplier AND status='RESPONDED'"""),
        {"t": context.tenant_id, "rfq": rfq_id, "supplier": supplier_id}).first()
    if not chosen:
        raise ProcurementError("responding supplier not found")
    db.execute(text("""UPDATE procurement_rfq_suppliers SET status=CASE WHEN supplier_id=:supplier THEN 'AWARDED' ELSE
        CASE WHEN status='RESPONDED' THEN 'NOT_SELECTED' ELSE status END END WHERE tenant_id=:t AND rfq_id=:rfq"""),
        {"supplier": supplier_id, "t": context.tenant_id, "rfq": rfq_id})
    db.execute(text("""UPDATE procurement_rfqs SET status='AWARDED',awarded_supplier_id=:supplier,
        version=version+1,updated_at=:now WHERE tenant_id=:t AND id=:id"""),
        {"supplier": supplier_id, "now": datetime.now(UTC), "t": context.tenant_id, "id": rfq_id})
    _audit(db, context, "procurement.rfq.awarded", "procurement_rfq", rfq_id, {"supplier_id": str(supplier_id)})


def _po_fingerprint(supplier_id: UUID, currency_code: str, lines: list[dict]) -> str:
    body = {
        "supplier_id": str(supplier_id),
        "currency_code": currency_code.upper(),
        "lines": [
            {
                "product_id": str(line["product_id"]),
                "unit_id": str(line["unit_id"]),
                "quantity": format(Decimal(line["quantity"]), "f"),
                "unit_price": format(Decimal(line["unit_price"]), "f"),
                "discount_amount": format(Decimal(line.get("discount_amount", 0)), "f"),
                "tax_amount": format(Decimal(line.get("tax_amount", 0)), "f"),
            }
            for line in lines
        ],
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def create_purchase_order(
    db: Connection, *, context: RequestContext, legal_entity_id: UUID, branch_id: UUID | None,
    supplier_id: UUID, lines: list[dict], currency_code: str = "THB",
    source_rfq_id: UUID | None = None, period_key: str | None = None,
) -> UUID:
    require_permission(context, "purchase_order.manage")
    if not lines:
        raise ProcurementError("purchase order requires lines")
    organization = db.execute(text("""SELECT 1 FROM legal_entities le
        LEFT JOIN branches b ON b.tenant_id=le.tenant_id AND b.legal_entity_id=le.id AND b.id=:branch
        WHERE le.tenant_id=:t AND le.id=:entity AND le.status='ACTIVE'
          AND (:branch IS NULL OR b.id IS NOT NULL)"""),
        {"t": context.tenant_id, "entity": legal_entity_id, "branch": branch_id}).first()
    if not organization:
        raise ProcurementError("organization scope not found")
    supplier = db.execute(text("""SELECT 1 FROM business_partners
        WHERE tenant_id=:t AND id=:supplier AND is_supplier AND status='ACTIVE'"""),
        {"t": context.tenant_id, "supplier": supplier_id}).first()
    if not supplier:
        raise ProcurementError("supplier not found")
    if source_rfq_id:
        rfq = db.execute(text("""SELECT awarded_supplier_id,currency_code FROM procurement_rfqs
            WHERE tenant_id=:t AND id=:id AND status='AWARDED'"""),
            {"t": context.tenant_id, "id": source_rfq_id}).mappings().first()
        if not rfq or rfq["awarded_supplier_id"] != supplier_id:
            raise ProcurementError("awarded RFQ not found for supplier")
        if rfq["currency_code"] != currency_code.upper():
            raise ProcurementError("purchase order currency must match RFQ")
    normalized: list[dict] = []
    for line in lines:
        quantity = Decimal(line["quantity"])
        unit_price = Decimal(line["unit_price"])
        discount = Decimal(line.get("discount_amount", 0))
        tax = Decimal(line.get("tax_amount", 0))
        if quantity <= 0 or unit_price < 0 or discount < 0 or tax < 0:
            raise ProcurementError("invalid purchase order line")
        _product_unit_owned(db, context.tenant_id, line["product_id"], line["unit_id"])
        gross = quantity * unit_price
        if discount > gross:
            raise ProcurementError("discount exceeds gross amount")
        total = gross - discount + tax
        normalized.append({**line, "quantity": quantity, "unit_price": unit_price,
                           "discount_amount": discount, "tax_amount": tax, "line_total": total})
    now = datetime.now(UTC)
    number = allocate_document_number(
        db, tenant_id=context.tenant_id, document_type="PO",
        legal_entity_id=legal_entity_id, branch_id=branch_id,
        period_key=period_key or str(now.year),
    )
    order_id = uuid4()
    db.execute(text("""INSERT INTO purchase_orders
        (id,tenant_id,order_number,legal_entity_id,branch_id,supplier_id,source_rfq_id,currency_code,
         status,version,created_at,updated_at)
        VALUES (:id,:t,:number,:entity,:branch,:supplier,:rfq,:currency,'DRAFT',1,:now,:now)"""),
        {"id": order_id, "t": context.tenant_id, "number": number, "entity": legal_entity_id,
         "branch": branch_id, "supplier": supplier_id, "rfq": source_rfq_id,
         "currency": currency_code.upper(), "now": now})
    for line_number, line in enumerate(normalized, 1):
        db.execute(text("""INSERT INTO purchase_order_lines
            (id,tenant_id,purchase_order_id,line_number,product_id,unit_id,ordered_quantity,
             unit_price,discount_amount,tax_amount,line_total,received_quantity,returned_quantity)
            VALUES (:id,:t,:po,:line,:product,:unit,:quantity,:price,:discount,:tax,:total,0,0)"""),
            {"id": uuid4(), "t": context.tenant_id, "po": order_id, "line": line_number,
             "product": line["product_id"], "unit": line["unit_id"], "quantity": line["quantity"],
             "price": line["unit_price"], "discount": line["discount_amount"],
             "tax": line["tax_amount"], "total": line["line_total"]})
    _audit(db, context, "procurement.order.created", "purchase_order", order_id,
           {"order_number": number, "currency_code": currency_code.upper()})
    write_outbox(db, tenant_id=context.tenant_id, aggregate_type="purchase_order", aggregate_id=order_id,
                 event_type="procurement.order.created", payload={"purchase_order_id": str(order_id)})
    return order_id


def submit_purchase_order(db: Connection, *, context: RequestContext, order_id: UUID) -> None:
    require_permission(context, "purchase_order.manage")
    row = db.execute(text("""SELECT status FROM purchase_orders
        WHERE tenant_id=:t AND id=:id FOR UPDATE"""),
        {"t": context.tenant_id, "id": order_id}).mappings().first()
    if not row:
        raise ProcurementError("purchase order not found")
    if row["status"] != "DRAFT":
        raise ProcurementError("purchase order must be DRAFT to submit")
    db.execute(text("""UPDATE purchase_orders SET status='PENDING_APPROVAL',version=version+1,
        approval_fingerprint=NULL,approved_version=NULL,approved_at=NULL,approved_by_tenant_user_id=NULL,
        updated_at=:now WHERE tenant_id=:t AND id=:id"""),
        {"now": datetime.now(UTC), "t": context.tenant_id, "id": order_id})
    _audit(db, context, "procurement.order.submitted", "purchase_order", order_id)



def _purchase_order_approval_snapshot(db: Connection, tenant_id: UUID, order_id: UUID) -> tuple[dict, int]:
    order = db.execute(text("""SELECT supplier_id,currency_code,status,version FROM purchase_orders
        WHERE tenant_id=:t AND id=:id"""), {"t": tenant_id, "id": order_id}).mappings().first()
    if not order:
        raise ProcurementError("purchase order not found")
    lines = db.execute(text("""SELECT product_id,unit_id,ordered_quantity,unit_price,discount_amount,tax_amount
        FROM purchase_order_lines WHERE tenant_id=:t AND purchase_order_id=:id ORDER BY line_number"""),
        {"t": tenant_id, "id": order_id}).mappings().all()
    snapshot = {"supplier_id": str(order["supplier_id"]), "currency_code": order["currency_code"],
                "status": order["status"], "version": int(order["version"]),
                "lines": [{k: str(v) for k, v in dict(line).items()} for line in lines]}
    return snapshot, int(order["version"])


def request_purchase_order_approval(
    db: Connection, *, context: RequestContext, order_id: UUID, policy_code: str
) -> UUID:
    require_permission(context, "purchase_order.manage")
    snapshot, version = _purchase_order_approval_snapshot(db, context.tenant_id, order_id)
    if snapshot["status"] != "PENDING_APPROVAL":
        raise ProcurementError("purchase order must be pending approval")
    return request_approval(db, context=context, policy_code=policy_code,
        source_type="PURCHASE_ORDER", source_id=order_id, source_version=version, snapshot=snapshot)

def approve_purchase_order(db: Connection, *, context: RequestContext, order_id: UUID, approval_request_id: UUID | None = None) -> None:
    require_permission(context, "purchase_order.approve")
    active_control = db.execute(text("""SELECT 1 FROM approval_policies
        WHERE tenant_id=:t AND request_type='PURCHASE_ORDER' AND status='ACTIVE' LIMIT 1"""),
        {"t": context.tenant_id}).first()
    if active_control:
        if approval_request_id is None:
            raise ProcurementError("approved approval request required")
        snapshot, source_version = _purchase_order_approval_snapshot(db, context.tenant_id, order_id)
        require_approved_snapshot(db, context=context, approval_request_id=approval_request_id,
            source_type="PURCHASE_ORDER", source_id=order_id, source_version=source_version, snapshot=snapshot)
    order = db.execute(text("""SELECT status,version,supplier_id,currency_code FROM purchase_orders
        WHERE tenant_id=:t AND id=:id FOR UPDATE"""),
        {"t": context.tenant_id, "id": order_id}).mappings().first()
    if not order:
        raise ProcurementError("purchase order not found")
    if order["status"] != "PENDING_APPROVAL":
        raise ProcurementError("purchase order must be pending approval")
    rows = db.execute(text("""SELECT product_id,unit_id,ordered_quantity quantity,unit_price,
        discount_amount,tax_amount FROM purchase_order_lines
        WHERE tenant_id=:t AND purchase_order_id=:id ORDER BY line_number"""),
        {"t": context.tenant_id, "id": order_id}).mappings().all()
    fingerprint = _po_fingerprint(order["supplier_id"], order["currency_code"], [dict(row) for row in rows])
    approved_version = int(order["version"])
    db.execute(text("""UPDATE purchase_orders SET status='APPROVED',version=version+1,
        approval_fingerprint=:fingerprint,approved_version=:approved_version,approved_at=:now,
        approved_by_tenant_user_id=:actor,updated_at=:now WHERE tenant_id=:t AND id=:id"""),
        {"fingerprint": fingerprint, "approved_version": approved_version, "now": datetime.now(UTC),
         "actor": context.tenant_user_id, "t": context.tenant_id, "id": order_id})
    _audit(db, context, "procurement.order.approved", "purchase_order", order_id,
           {"approved_version": approved_version, "fingerprint": fingerprint})
    if active_control and approval_request_id is not None:
        mark_executed(db, context=context, approval_request_id=approval_request_id,
                      execution_reference=f"PURCHASE_ORDER:{order_id}")


def send_purchase_order(db: Connection, *, context: RequestContext, order_id: UUID) -> None:
    require_permission(context, "purchase_order.manage")
    order = db.execute(text("""SELECT status FROM purchase_orders
        WHERE tenant_id=:t AND id=:id FOR UPDATE"""),
        {"t": context.tenant_id, "id": order_id}).mappings().first()
    if not order:
        raise ProcurementError("purchase order not found")
    if order["status"] != "APPROVED":
        raise ProcurementError("purchase order must be APPROVED to send")
    db.execute(text("""UPDATE purchase_orders SET status='SENT',version=version+1,updated_at=:now
        WHERE tenant_id=:t AND id=:id"""),
        {"now": datetime.now(UTC), "t": context.tenant_id, "id": order_id})
    _audit(db, context, "procurement.order.sent", "purchase_order", order_id)


def _refresh_po_receipt_status(db: Connection, tenant_id: UUID, order_id: UUID) -> str:
    rows = db.execute(text("""SELECT ordered_quantity,received_quantity FROM purchase_order_lines
        WHERE tenant_id=:t AND purchase_order_id=:id ORDER BY line_number FOR UPDATE"""),
        {"t": tenant_id, "id": order_id}).mappings().all()
    received = sum((Decimal(row["received_quantity"]) for row in rows), Decimal(0))
    if rows and all(Decimal(row["received_quantity"]) >= Decimal(row["ordered_quantity"]) for row in rows):
        status = "RECEIVED"
    elif received > 0:
        status = "PARTIALLY_RECEIVED"
    else:
        status = "SENT"
    db.execute(text("""UPDATE purchase_orders SET status=:status,version=version+1,updated_at=:now
        WHERE tenant_id=:t AND id=:id"""),
        {"status": status, "now": datetime.now(UTC), "t": tenant_id, "id": order_id})
    return status


def post_goods_receipt(
    db: Connection, *, context: RequestContext, order_id: UUID, location_id: UUID,
    lines: list[dict], idempotency_key: str, period_key: str | None = None,
) -> UUID:
    require_permission(context, "procurement.receive")
    if not lines:
        raise ProcurementError("goods receipt requires lines")
    existing = db.execute(text("""SELECT id FROM goods_receipts
        WHERE tenant_id=:t AND idempotency_key=:key AND status='POSTED'"""),
        {"t": context.tenant_id, "key": idempotency_key}).scalar_one_or_none()
    if existing:
        return existing
    order = db.execute(text("""SELECT order_number,legal_entity_id,branch_id,status FROM purchase_orders
        WHERE tenant_id=:t AND id=:id FOR UPDATE"""),
        {"t": context.tenant_id, "id": order_id}).mappings().first()
    if not order or order["status"] not in {"SENT", "PARTIALLY_RECEIVED"}:
        raise ProcurementError("purchase order is not receivable")
    location = db.execute(text("""SELECT 1 FROM warehouse_locations l JOIN warehouses w
        ON w.tenant_id=l.tenant_id AND w.id=l.warehouse_id
        WHERE l.tenant_id=:t AND l.id=:location AND l.status='ACTIVE' AND l.allow_stock
          AND w.status='ACTIVE' AND w.legal_entity_id=:entity"""),
        {"t": context.tenant_id, "location": location_id, "entity": order["legal_entity_id"]}).first()
    if not location:
        raise ProcurementError("receipt location not found")
    normalized = []
    seen = set()
    for line in lines:
        line_id = UUID(str(line["purchase_order_line_id"]))
        if line_id in seen:
            raise ProcurementError("duplicate purchase order line")
        seen.add(line_id)
        quantity = Decimal(line["quantity"])
        if quantity <= 0:
            raise ProcurementError("receipt quantity must be positive")
        row = db.execute(text("""SELECT product_id,unit_id,ordered_quantity,received_quantity
            FROM purchase_order_lines WHERE tenant_id=:t AND id=:line AND purchase_order_id=:po FOR UPDATE"""),
            {"t": context.tenant_id, "line": line_id, "po": order_id}).mappings().first()
        if not row:
            raise ProcurementError("purchase order line not found")
        if Decimal(row["received_quantity"]) + quantity > Decimal(row["ordered_quantity"]):
            raise ProcurementError("receipt exceeds ordered quantity")
        normalized.append((line_id, quantity, row))
    now = datetime.now(UTC)
    receipt_id = uuid4()
    number = allocate_document_number(db, tenant_id=context.tenant_id, document_type="GR",
        legal_entity_id=order["legal_entity_id"], branch_id=order["branch_id"],
        period_key=period_key or str(now.year))
    db.execute(text("""INSERT INTO goods_receipts
        (id,tenant_id,receipt_number,purchase_order_id,location_id,status,idempotency_key,created_at,updated_at)
        VALUES (:id,:t,:number,:po,:location,'DRAFT',:key,:now,:now)"""),
        {"id": receipt_id, "t": context.tenant_id, "number": number, "po": order_id,
         "location": location_id, "key": idempotency_key, "now": now})
    stock_lines = []
    for line_id, quantity, row in normalized:
        db.execute(text("""INSERT INTO goods_receipt_lines
            (id,tenant_id,goods_receipt_id,purchase_order_line_id,quantity)
            VALUES (:id,:t,:receipt,:line,:quantity)"""),
            {"id": uuid4(), "t": context.tenant_id, "receipt": receipt_id, "line": line_id, "quantity": quantity})
        stock_lines.append(StockLine(product_id=row["product_id"], unit_id=row["unit_id"],
                                     location_id=location_id, quantity=quantity))
    inventory_id = post_procurement_inventory(
        db, context=context, transaction_type="RECEIVE", legal_entity_id=order["legal_entity_id"],
        branch_id=order["branch_id"], lines=stock_lines, idempotency_key=f"GR:{idempotency_key}",
        source_type="GOODS_RECEIPT", source_id=receipt_id, source_number=number,
    )
    for line_id, quantity, _ in normalized:
        db.execute(text("""UPDATE purchase_order_lines SET received_quantity=received_quantity+:quantity
            WHERE tenant_id=:t AND id=:line"""),
            {"quantity": quantity, "t": context.tenant_id, "line": line_id})
    status = _refresh_po_receipt_status(db, context.tenant_id, order_id)
    db.execute(text("""UPDATE goods_receipts SET status='POSTED',inventory_transaction_id=:inventory,
        posted_at=:now,updated_at=:now WHERE tenant_id=:t AND id=:id"""),
        {"inventory": inventory_id, "now": now, "t": context.tenant_id, "id": receipt_id})
    _audit(db, context, "procurement.receipt.posted", "goods_receipt", receipt_id,
           {"purchase_order_id": str(order_id), "inventory_transaction_id": str(inventory_id), "po_status": status})
    write_outbox(db, tenant_id=context.tenant_id, aggregate_type="goods_receipt", aggregate_id=receipt_id,
                 event_type="procurement.receipt.posted", payload={"goods_receipt_id": str(receipt_id)})
    return receipt_id


def post_purchase_return(
    db: Connection, *, context: RequestContext, order_id: UUID, location_id: UUID,
    lines: list[dict], idempotency_key: str, period_key: str | None = None,
) -> UUID:
    require_permission(context, "procurement.receive")
    if not lines:
        raise ProcurementError("purchase return requires lines")
    existing = db.execute(text("""SELECT id FROM purchase_returns
        WHERE tenant_id=:t AND idempotency_key=:key AND status='POSTED'"""),
        {"t": context.tenant_id, "key": idempotency_key}).scalar_one_or_none()
    if existing:
        return existing
    order = db.execute(text("""SELECT order_number,legal_entity_id,branch_id,status FROM purchase_orders
        WHERE tenant_id=:t AND id=:id FOR UPDATE"""),
        {"t": context.tenant_id, "id": order_id}).mappings().first()
    if not order or order["status"] not in {"PARTIALLY_RECEIVED", "RECEIVED"}:
        raise ProcurementError("purchase order has no returnable receipt")
    normalized = []
    seen = set()
    for line in lines:
        line_id = UUID(str(line["purchase_order_line_id"]))
        if line_id in seen:
            raise ProcurementError("duplicate purchase order line")
        seen.add(line_id)
        quantity = Decimal(line["quantity"])
        if quantity <= 0:
            raise ProcurementError("return quantity must be positive")
        row = db.execute(text("""SELECT product_id,unit_id,received_quantity,returned_quantity
            FROM purchase_order_lines WHERE tenant_id=:t AND id=:line AND purchase_order_id=:po FOR UPDATE"""),
            {"t": context.tenant_id, "line": line_id, "po": order_id}).mappings().first()
        if not row:
            raise ProcurementError("purchase order line not found")
        if Decimal(row["returned_quantity"]) + quantity > Decimal(row["received_quantity"]):
            raise ProcurementError("return exceeds received quantity")
        normalized.append((line_id, quantity, row))
    now = datetime.now(UTC)
    return_id = uuid4()
    number = allocate_document_number(db, tenant_id=context.tenant_id, document_type="PRT",
        legal_entity_id=order["legal_entity_id"], branch_id=order["branch_id"],
        period_key=period_key or str(now.year))
    db.execute(text("""INSERT INTO purchase_returns
        (id,tenant_id,return_number,purchase_order_id,location_id,status,idempotency_key,created_at,updated_at)
        VALUES (:id,:t,:number,:po,:location,'DRAFT',:key,:now,:now)"""),
        {"id": return_id, "t": context.tenant_id, "number": number, "po": order_id,
         "location": location_id, "key": idempotency_key, "now": now})
    stock_lines = []
    for line_id, quantity, row in normalized:
        db.execute(text("""INSERT INTO purchase_return_lines
            (id,tenant_id,purchase_return_id,purchase_order_line_id,quantity)
            VALUES (:id,:t,:return_id,:line,:quantity)"""),
            {"id": uuid4(), "t": context.tenant_id, "return_id": return_id, "line": line_id, "quantity": quantity})
        stock_lines.append(StockLine(product_id=row["product_id"], unit_id=row["unit_id"],
                                     location_id=location_id, quantity=quantity))
    inventory_id = post_procurement_inventory(
        db, context=context, transaction_type="ISSUE", legal_entity_id=order["legal_entity_id"],
        branch_id=order["branch_id"], lines=stock_lines, idempotency_key=f"PRT:{idempotency_key}",
        source_type="PURCHASE_RETURN", source_id=return_id, source_number=number,
    )
    for line_id, quantity, _ in normalized:
        db.execute(text("""UPDATE purchase_order_lines SET returned_quantity=returned_quantity+:quantity
            WHERE tenant_id=:t AND id=:line"""),
            {"quantity": quantity, "t": context.tenant_id, "line": line_id})
    db.execute(text("""UPDATE purchase_returns SET status='POSTED',inventory_transaction_id=:inventory,
        posted_at=:now,updated_at=:now WHERE tenant_id=:t AND id=:id"""),
        {"inventory": inventory_id, "now": now, "t": context.tenant_id, "id": return_id})
    _audit(db, context, "procurement.return.posted", "purchase_return", return_id,
           {"purchase_order_id": str(order_id), "inventory_transaction_id": str(inventory_id)})
    write_outbox(db, tenant_id=context.tenant_id, aggregate_type="purchase_return", aggregate_id=return_id,
                 event_type="procurement.return.posted", payload={"purchase_return_id": str(return_id)})
    return return_id
