from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.application.inventory import StockLine, _post_inventory_core
from app.application.numbering import allocate_document_number
from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit, write_outbox


class SalesError(ValueError):
    pass


def _audit(db: Connection, context: RequestContext, action: str, target_type: str, target_id: UUID, metadata=None):
    write_audit(db, tenant_id=context.tenant_id, request_id=context.request_id, action=action,
        actor_user_id=context.actor_user_id, actor_tenant_user_id=context.tenant_user_id,
        target_type=target_type, target_id=target_id, metadata=metadata or {})


def _number(db: Connection, context: RequestContext, kind: str, entity: UUID, branch: UUID | None, period: str | None):
    return allocate_document_number(db, tenant_id=context.tenant_id, document_type=kind,
        legal_entity_id=entity, branch_id=branch, period_key=period or str(datetime.now(UTC).year))


def _org_customer(db: Connection, context: RequestContext, entity: UUID, branch: UUID | None, customer: UUID):
    ok = db.execute(text("""SELECT 1 FROM legal_entities e
        LEFT JOIN branches b ON b.tenant_id=e.tenant_id AND b.legal_entity_id=e.id AND b.id=:branch
        JOIN business_partners p ON p.tenant_id=e.tenant_id AND p.id=:customer
        WHERE e.tenant_id=:t AND e.id=:entity AND e.status='ACTIVE'
          AND (:branch IS NULL OR b.status='ACTIVE') AND p.status='ACTIVE' AND p.is_customer"""),
        {"t": context.tenant_id, "entity": entity, "branch": branch, "customer": customer}).first()
    if not ok:
        raise SalesError("organization or customer not found")


def _lines(db: Connection, context: RequestContext, lines: list[dict]):
    if not lines:
        raise SalesError("document requires lines")
    out = []
    for no, line in enumerate(lines, 1):
        product, unit = UUID(str(line["product_id"])), UUID(str(line["unit_id"]))
        quantity, price = Decimal(line["quantity"]), Decimal(line["unit_price"])
        discount, tax = Decimal(line.get("discount_amount", 0)), Decimal(line.get("tax_amount", 0))
        owned = db.execute(text("""SELECT 1 FROM products p JOIN units u ON u.tenant_id=p.tenant_id AND u.id=:unit
            WHERE p.tenant_id=:t AND p.id=:product AND p.status='ACTIVE'"""),
            {"t": context.tenant_id, "product": product, "unit": unit}).first()
        if not owned or quantity <= 0 or price < 0 or discount < 0 or tax < 0:
            raise SalesError("invalid sales line")
        gross = quantity * price
        if discount > gross:
            raise SalesError("discount exceeds gross amount")
        out.append({"line_number": no, "product_id": product, "unit_id": unit, "quantity": quantity,
                    "unit_price": price, "discount_amount": discount, "tax_amount": tax,
                    "line_total": gross - discount + tax})
    return out


def create_quotation(db: Connection, *, context: RequestContext, legal_entity_id: UUID, branch_id: UUID | None,
                     customer_id: UUID, lines: list[dict], currency_code: str = "THB", valid_until: date | None = None,
                     terms: str | None = None, opportunity_id: UUID | None = None,
                     owner_tenant_user_id: UUID | None = None, period_key: str | None = None) -> UUID:
    require_permission(context, "quotation.manage")
    _org_customer(db, context, legal_entity_id, branch_id, customer_id)
    normalized = _lines(db, context, lines)
    if opportunity_id and not db.execute(text("SELECT 1 FROM crm_opportunities WHERE tenant_id=:t AND id=:id"),
        {"t": context.tenant_id, "id": opportunity_id}).first():
        raise SalesError("opportunity not found")
    now, qid, rid = datetime.now(UTC), uuid4(), uuid4()
    number = _number(db, context, "QT", legal_entity_id, branch_id, period_key)
    db.execute(text("""INSERT INTO sales_quotations
      (id,tenant_id,quotation_number,legal_entity_id,branch_id,customer_id,opportunity_id,owner_tenant_user_id,
       currency_code,status,current_revision,valid_until,version,created_at,updated_at)
      VALUES (:id,:t,:number,:entity,:branch,:customer,:opp,:owner,:currency,'DRAFT',1,:valid,1,:now,:now)"""),
      {"id":qid,"t":context.tenant_id,"number":number,"entity":legal_entity_id,"branch":branch_id,"customer":customer_id,
       "opp":opportunity_id,"owner":owner_tenant_user_id,"currency":currency_code,"valid":valid_until,"now":now})
    total = sum((x["line_total"] for x in normalized), Decimal(0))
    db.execute(text("""INSERT INTO sales_quotation_revisions
      (id,tenant_id,quotation_id,revision,customer_id,currency_code,valid_until,terms,total_amount,created_at)
      VALUES (:id,:t,:q,1,:customer,:currency,:valid,:terms,:total,:now)"""),
      {"id":rid,"t":context.tenant_id,"q":qid,"customer":customer_id,"currency":currency_code,
       "valid":valid_until,"terms":terms,"total":total,"now":now})
    for x in normalized:
        db.execute(text("""INSERT INTO sales_quotation_lines
          (id,tenant_id,quotation_revision_id,line_number,product_id,unit_id,quantity,unit_price,discount_amount,tax_amount,line_total)
          VALUES (:id,:t,:rev,:line,:product,:unit,:qty,:price,:discount,:tax,:total)"""),
          {"id":uuid4(),"t":context.tenant_id,"rev":rid,"line":x["line_number"],"product":x["product_id"],
           "unit":x["unit_id"],"qty":x["quantity"],"price":x["unit_price"],"discount":x["discount_amount"],
           "tax":x["tax_amount"],"total":x["line_total"]})
    _audit(db, context, "sales.quotation.created", "sales_quotation", qid, {"revision":1,"number":number})
    return qid


def send_quotation(db: Connection, *, context: RequestContext, quotation_id: UUID):
    require_permission(context, "quotation.manage")
    row=db.execute(text("SELECT status,valid_until,current_revision FROM sales_quotations WHERE tenant_id=:t AND id=:id FOR UPDATE"),
        {"t":context.tenant_id,"id":quotation_id}).mappings().first()
    if not row or row["status"]!="DRAFT":
        raise SalesError("quotation must be DRAFT to send")
    if row["valid_until"] and row["valid_until"] < date.today():
        raise SalesError("quotation is expired")
    db.execute(text("UPDATE sales_quotations SET status='SENT',version=version+1,updated_at=:now WHERE tenant_id=:t AND id=:id"),
        {"now":datetime.now(UTC),"t":context.tenant_id,"id":quotation_id})
    _audit(db,context,"sales.quotation.sent","sales_quotation",quotation_id,{"revision":row["current_revision"]})


def revise_quotation(db: Connection, *, context: RequestContext, quotation_id: UUID, lines: list[dict],
                     valid_until: date | None = None, terms: str | None = None):
    require_permission(context, "quotation.manage")
    q=db.execute(text("""SELECT status,current_revision,customer_id,currency_code FROM sales_quotations
        WHERE tenant_id=:t AND id=:id FOR UPDATE"""),{"t":context.tenant_id,"id":quotation_id}).mappings().first()
    if not q or q["status"] not in {"DRAFT","SENT"}:
        raise SalesError("quotation cannot be revised")
    normalized=_lines(db,context,lines); revision=int(q["current_revision"])+1; rid=uuid4(); now=datetime.now(UTC)
    total=sum((x["line_total"] for x in normalized),Decimal(0))
    db.execute(text("""INSERT INTO sales_quotation_revisions
      (id,tenant_id,quotation_id,revision,customer_id,currency_code,valid_until,terms,total_amount,created_at)
      VALUES (:id,:t,:q,:revision,:customer,:currency,:valid,:terms,:total,:now)"""),
      {"id":rid,"t":context.tenant_id,"q":quotation_id,"revision":revision,"customer":q["customer_id"],
       "currency":q["currency_code"],"valid":valid_until,"terms":terms,"total":total,"now":now})
    for x in normalized:
        db.execute(text("""INSERT INTO sales_quotation_lines
          (id,tenant_id,quotation_revision_id,line_number,product_id,unit_id,quantity,unit_price,discount_amount,tax_amount,line_total)
          VALUES (:id,:t,:rev,:line,:product,:unit,:qty,:price,:discount,:tax,:total)"""),
          {"id":uuid4(),"t":context.tenant_id,"rev":rid,"line":x["line_number"],"product":x["product_id"],"unit":x["unit_id"],
           "qty":x["quantity"],"price":x["unit_price"],"discount":x["discount_amount"],"tax":x["tax_amount"],"total":x["line_total"]})
    db.execute(text("""UPDATE sales_quotations SET current_revision=:revision,status='DRAFT',valid_until=:valid,
        version=version+1,updated_at=:now WHERE tenant_id=:t AND id=:id"""),
        {"revision":revision,"valid":valid_until,"now":now,"t":context.tenant_id,"id":quotation_id})
    _audit(db,context,"sales.quotation.revised","sales_quotation",quotation_id,{"revision":revision})


def accept_quotation(db: Connection, *, context: RequestContext, quotation_id: UUID, accepted_by: str) -> UUID:
    require_permission(context,"quotation.transition")
    q=db.execute(text("""SELECT * FROM sales_quotations WHERE tenant_id=:t AND id=:id FOR UPDATE"""),
        {"t":context.tenant_id,"id":quotation_id}).mappings().first()
    if not q or q["status"]!="SENT":
        raise SalesError("quotation must be SENT to accept")
    if q["valid_until"] and q["valid_until"] < date.today():
        db.execute(text("UPDATE sales_quotations SET status='EXPIRED',updated_at=:now WHERE tenant_id=:t AND id=:id"),
            {"now":datetime.now(UTC),"t":context.tenant_id,"id":quotation_id})
        raise SalesError("quotation is expired")
    rev=db.execute(text("""SELECT * FROM sales_quotation_revisions WHERE tenant_id=:t AND quotation_id=:q
        AND revision=:revision"""),{"t":context.tenant_id,"q":quotation_id,"revision":q["current_revision"]}).mappings().one()
    lines=db.execute(text("""SELECT * FROM sales_quotation_lines WHERE tenant_id=:t AND quotation_revision_id=:rev ORDER BY line_number"""),
        {"t":context.tenant_id,"rev":rev["id"]}).mappings().all()
    now=datetime.now(UTC); order_id=uuid4()
    order_number=_number(db,context,"SO",q["legal_entity_id"],q["branch_id"],None)
    db.execute(text("""INSERT INTO sales_orders
      (id,tenant_id,order_number,legal_entity_id,branch_id,customer_id,source_quotation_id,source_quotation_revision,
       currency_code,status,version,created_at,updated_at)
      VALUES (:id,:t,:number,:entity,:branch,:customer,:q,:revision,:currency,'DRAFT',1,:now,:now)"""),
      {"id":order_id,"t":context.tenant_id,"number":order_number,"entity":q["legal_entity_id"],"branch":q["branch_id"],
       "customer":q["customer_id"],"q":quotation_id,"revision":q["current_revision"],"currency":q["currency_code"],"now":now})
    for line in lines:
        db.execute(text("""INSERT INTO sales_order_lines
          (id,tenant_id,sales_order_id,line_number,product_id,unit_id,ordered_quantity,unit_price,discount_amount,tax_amount,line_total)
          VALUES (:id,:t,:so,:line,:product,:unit,:qty,:price,:discount,:tax,:total)"""),
          {"id":uuid4(),"t":context.tenant_id,"so":order_id,"line":line["line_number"],"product":line["product_id"],
           "unit":line["unit_id"],"qty":line["quantity"],"price":line["unit_price"],"discount":line["discount_amount"],
           "tax":line["tax_amount"],"total":line["line_total"]})
    db.execute(text("""UPDATE sales_quotations SET status='ACCEPTED',accepted_revision=current_revision,
        accepted_at=:now,accepted_by=:by,version=version+1,updated_at=:now WHERE tenant_id=:t AND id=:id"""),
        {"now":now,"by":accepted_by,"t":context.tenant_id,"id":quotation_id})
    _audit(db,context,"sales.quotation.accepted","sales_quotation",quotation_id,{"revision":q["current_revision"],"sales_order_id":str(order_id)})
    _audit(db,context,"sales.order.created","sales_order",order_id,{"source_quotation_id":str(quotation_id),"source_revision":q["current_revision"]})
    return order_id


def confirm_order(db: Connection, *, context: RequestContext, order_id: UUID):
    require_permission(context,"sales_order.manage")
    row=db.execute(text("SELECT status FROM sales_orders WHERE tenant_id=:t AND id=:id FOR UPDATE"),
        {"t":context.tenant_id,"id":order_id}).mappings().first()
    if not row or row["status"]!="DRAFT":
        raise SalesError("sales order must be DRAFT")
    now=datetime.now(UTC)
    db.execute(text("UPDATE sales_orders SET status='CONFIRMED',confirmed_at=:now,version=version+1,updated_at=:now WHERE tenant_id=:t AND id=:id"),
        {"now":now,"t":context.tenant_id,"id":order_id})
    _audit(db,context,"sales.order.confirmed","sales_order",order_id)


def _order_status(db: Connection, tenant: UUID, order_id: UUID):
    rows=db.execute(text("""SELECT ordered_quantity,reserved_quantity,delivered_quantity FROM sales_order_lines
      WHERE tenant_id=:t AND sales_order_id=:id FOR UPDATE"""),{"t":tenant,"id":order_id}).mappings().all()
    delivered=sum((Decimal(x["delivered_quantity"]) for x in rows),Decimal(0))
    reserved=sum((Decimal(x["reserved_quantity"]) for x in rows),Decimal(0))
    if rows and all(Decimal(x["delivered_quantity"])>=Decimal(x["ordered_quantity"]) for x in rows): status="FULFILLED"
    elif delivered>0: status="PARTIALLY_FULFILLED"
    elif rows and all(Decimal(x["reserved_quantity"])>=Decimal(x["ordered_quantity"]) for x in rows): status="RESERVED"
    elif reserved>0: status="PARTIALLY_RESERVED"
    else: status="CONFIRMED"
    db.execute(text("UPDATE sales_orders SET status=:status,version=version+1,updated_at=:now WHERE tenant_id=:t AND id=:id"),
        {"status":status,"now":datetime.now(UTC),"t":tenant,"id":order_id})
    return status


def reserve_order(db: Connection, *, context: RequestContext, order_id: UUID, location_id: UUID, lines: list[dict]):
    require_permission(context,"sales.reserve")
    order=db.execute(text("""SELECT legal_entity_id,status FROM sales_orders WHERE tenant_id=:t AND id=:id FOR UPDATE"""),
        {"t":context.tenant_id,"id":order_id}).mappings().first()
    if not order or order["status"] not in {"CONFIRMED","PARTIALLY_RESERVED","RESERVED","PROCESSING"}:
        raise SalesError("sales order is not reservable")
    for item in lines:
        line_id=UUID(str(item["sales_order_line_id"])); qty=Decimal(item["quantity"])
        line=db.execute(text("""SELECT product_id,ordered_quantity,reserved_quantity,delivered_quantity FROM sales_order_lines
          WHERE tenant_id=:t AND id=:line AND sales_order_id=:so FOR UPDATE"""),
          {"t":context.tenant_id,"line":line_id,"so":order_id}).mappings().first()
        if not line or qty<=0 or Decimal(line["reserved_quantity"])+qty>Decimal(line["ordered_quantity"]):
            raise SalesError("invalid reservation quantity")
        on_hand=Decimal(db.execute(text("""SELECT COALESCE(on_hand,0) FROM inventory_balances
          WHERE tenant_id=:t AND product_id=:product AND location_id=:location FOR UPDATE"""),
          {"t":context.tenant_id,"product":line["product_id"],"location":location_id}).scalar_one_or_none() or 0)
        other=Decimal(db.execute(text("""SELECT COALESCE(sum(r.quantity-r.fulfilled_quantity),0)
          FROM sales_reservations r JOIN sales_order_lines l ON l.tenant_id=r.tenant_id AND l.id=r.sales_order_line_id
          WHERE r.tenant_id=:t AND r.location_id=:location AND l.product_id=:product AND r.status='ACTIVE'"""),
          {"t":context.tenant_id,"location":location_id,"product":line["product_id"]}).scalar_one())
        if on_hand-other < qty:
            raise SalesError("insufficient available stock")
        db.execute(text("""INSERT INTO sales_reservations
          (id,tenant_id,sales_order_id,sales_order_line_id,location_id,quantity,status,created_at)
          VALUES (:id,:t,:so,:line,:location,:qty,'ACTIVE',:now)"""),
          {"id":uuid4(),"t":context.tenant_id,"so":order_id,"line":line_id,"location":location_id,"qty":qty,"now":datetime.now(UTC)})
        db.execute(text("UPDATE sales_order_lines SET reserved_quantity=reserved_quantity+:qty WHERE tenant_id=:t AND id=:id"),
          {"qty":qty,"t":context.tenant_id,"id":line_id})
    status=_order_status(db,context.tenant_id,order_id)
    _audit(db,context,"sales.reservation.created","sales_order",order_id,{"status":status})


def _sales_inventory(db: Connection, context: RequestContext, kind: str, entity: UUID, branch: UUID | None,
                     lines: list[StockLine], key: str, source_type: str, source_id: UUID, source_number: str):
    require_permission(context,"sales.fulfill")
    return _post_inventory_core(db,context=context,transaction_type=kind,legal_entity_id=entity,branch_id=branch,
        lines=lines,idempotency_key=key,source_type=source_type,source_id=source_id,source_number=source_number)


def post_delivery(db: Connection, *, context: RequestContext, order_id: UUID, location_id: UUID,
                  lines: list[dict], idempotency_key: str, period_key: str | None = None) -> UUID:
    require_permission(context,"sales.fulfill")
    existing=db.execute(text("SELECT id FROM sales_deliveries WHERE tenant_id=:t AND idempotency_key=:key"),
        {"t":context.tenant_id,"key":idempotency_key}).scalar_one_or_none()
    if existing:return existing
    order=db.execute(text("""SELECT order_number,legal_entity_id,branch_id,status FROM sales_orders
      WHERE tenant_id=:t AND id=:id FOR UPDATE"""),{"t":context.tenant_id,"id":order_id}).mappings().first()
    if not order or order["status"] not in {"CONFIRMED","PARTIALLY_RESERVED","RESERVED","PROCESSING","PARTIALLY_FULFILLED"}:
        raise SalesError("sales order is not fulfillable")
    normalized=[]; stock=[]
    for item in lines:
        line_id=UUID(str(item["sales_order_line_id"])); qty=Decimal(item["quantity"])
        line=db.execute(text("""SELECT product_id,unit_id,ordered_quantity,delivered_quantity FROM sales_order_lines
          WHERE tenant_id=:t AND id=:line AND sales_order_id=:so FOR UPDATE"""),
          {"t":context.tenant_id,"line":line_id,"so":order_id}).mappings().first()
        if not line or qty<=0 or Decimal(line["delivered_quantity"])+qty>Decimal(line["ordered_quantity"]):
            raise SalesError("invalid delivery quantity")
        normalized.append((line_id,qty,line));stock.append(StockLine(line["product_id"],line["unit_id"],location_id,qty))
    now=datetime.now(UTC); did=uuid4(); number=_number(db,context,"DL",order["legal_entity_id"],order["branch_id"],period_key)
    inventory=_sales_inventory(db,context,"ISSUE",order["legal_entity_id"],order["branch_id"],stock,
        f"DL:{idempotency_key}","SALES_DELIVERY",did,number)
    db.execute(text("""INSERT INTO sales_deliveries
      (id,tenant_id,delivery_number,sales_order_id,location_id,status,inventory_transaction_id,idempotency_key,posted_at)
      VALUES (:id,:t,:number,:so,:location,'POSTED',:inventory,:key,:now)"""),
      {"id":did,"t":context.tenant_id,"number":number,"so":order_id,"location":location_id,"inventory":inventory,"key":idempotency_key,"now":now})
    for line_id,qty,_ in normalized:
        db.execute(text("INSERT INTO sales_delivery_lines (id,tenant_id,delivery_id,sales_order_line_id,quantity) VALUES (:id,:t,:delivery,:line,:qty)"),
          {"id":uuid4(),"t":context.tenant_id,"delivery":did,"line":line_id,"qty":qty})
        db.execute(text("UPDATE sales_order_lines SET delivered_quantity=delivered_quantity+:qty WHERE tenant_id=:t AND id=:id"),
          {"qty":qty,"t":context.tenant_id,"id":line_id})
        remaining=qty
        reservations=db.execute(text("""SELECT id,quantity,fulfilled_quantity FROM sales_reservations
          WHERE tenant_id=:t AND sales_order_line_id=:line AND location_id=:location AND status='ACTIVE'
          ORDER BY created_at,id FOR UPDATE"""),{"t":context.tenant_id,"line":line_id,"location":location_id}).mappings().all()
        for r in reservations:
            take=min(remaining,Decimal(r["quantity"])-Decimal(r["fulfilled_quantity"]))
            if take<=0:continue
            new=Decimal(r["fulfilled_quantity"])+take
            db.execute(text("""UPDATE sales_reservations SET fulfilled_quantity=:new,status=CASE WHEN :new>=quantity THEN 'FULFILLED' ELSE status END
              WHERE tenant_id=:t AND id=:id"""),{"new":new,"t":context.tenant_id,"id":r["id"]})
            db.execute(text("UPDATE sales_order_lines SET reserved_quantity=reserved_quantity-:take WHERE tenant_id=:t AND id=:id"),
              {"take":take,"t":context.tenant_id,"id":line_id});remaining-=take
            if remaining<=0:break
    status=_order_status(db,context.tenant_id,order_id)
    _audit(db,context,"sales.delivery.posted","sales_delivery",did,{"sales_order_id":str(order_id),"inventory_transaction_id":str(inventory),"status":status})
    write_outbox(db,tenant_id=context.tenant_id,aggregate_type="sales_delivery",aggregate_id=did,event_type="sales.delivery.posted",payload={"sales_delivery_id":str(did)})
    return did


def post_sales_return(db: Connection, *, context: RequestContext, order_id: UUID, location_id: UUID,
                      lines: list[dict], idempotency_key: str, period_key: str | None = None) -> UUID:
    require_permission(context,"sales.fulfill")
    existing=db.execute(text("SELECT id FROM sales_returns WHERE tenant_id=:t AND idempotency_key=:key"),
        {"t":context.tenant_id,"key":idempotency_key}).scalar_one_or_none()
    if existing:return existing
    order=db.execute(text("SELECT legal_entity_id,branch_id FROM sales_orders WHERE tenant_id=:t AND id=:id FOR UPDATE"),
        {"t":context.tenant_id,"id":order_id}).mappings().first()
    if not order:raise SalesError("sales order not found")
    normalized=[];stock=[]
    for item in lines:
        line_id=UUID(str(item["sales_order_line_id"]));qty=Decimal(item["quantity"])
        line=db.execute(text("""SELECT product_id,unit_id,delivered_quantity,returned_quantity FROM sales_order_lines
          WHERE tenant_id=:t AND id=:line AND sales_order_id=:so FOR UPDATE"""),
          {"t":context.tenant_id,"line":line_id,"so":order_id}).mappings().first()
        if not line or qty<=0 or Decimal(line["returned_quantity"])+qty>Decimal(line["delivered_quantity"]):
            raise SalesError("return exceeds delivered quantity")
        normalized.append((line_id,qty,line));stock.append(StockLine(line["product_id"],line["unit_id"],location_id,qty))
    now=datetime.now(UTC);rid=uuid4();number=_number(db,context,"SRT",order["legal_entity_id"],order["branch_id"],period_key)
    inventory=_sales_inventory(db,context,"RECEIVE",order["legal_entity_id"],order["branch_id"],stock,
        f"SRT:{idempotency_key}","SALES_RETURN",rid,number)
    db.execute(text("""INSERT INTO sales_returns
      (id,tenant_id,return_number,sales_order_id,location_id,inventory_transaction_id,idempotency_key,posted_at)
      VALUES (:id,:t,:number,:so,:location,:inventory,:key,:now)"""),
      {"id":rid,"t":context.tenant_id,"number":number,"so":order_id,"location":location_id,"inventory":inventory,"key":idempotency_key,"now":now})
    for line_id,qty,_ in normalized:
        db.execute(text("INSERT INTO sales_return_lines (id,tenant_id,return_id,sales_order_line_id,quantity) VALUES (:id,:t,:return_id,:line,:qty)"),
          {"id":uuid4(),"t":context.tenant_id,"return_id":rid,"line":line_id,"qty":qty})
        db.execute(text("UPDATE sales_order_lines SET returned_quantity=returned_quantity+:qty WHERE tenant_id=:t AND id=:id"),
          {"qty":qty,"t":context.tenant_id,"id":line_id})
    _audit(db,context,"sales.return.posted","sales_return",rid,{"sales_order_id":str(order_id),"inventory_transaction_id":str(inventory)})
    write_outbox(db,tenant_id=context.tenant_id,aggregate_type="sales_return",aggregate_id=rid,event_type="sales.return.posted",payload={"sales_return_id":str(rid)})
    return rid
