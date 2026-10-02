from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.application.inventory import StockLine, post_inventory
from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit, write_outbox


class InventoryOperationsError(ValueError):
    pass


def _audit(connection: Connection, context: RequestContext, action: str, target_type: str,
           target_id: UUID, metadata: dict[str, Any]) -> None:
    write_audit(connection,tenant_id=context.tenant_id,request_id=context.request_id,action=action,
                actor_user_id=context.actor_user_id,actor_tenant_user_id=context.tenant_user_id,
                target_type=target_type,target_id=target_id,metadata=metadata)


def _scale(value: Decimal) -> int:
    exponent=value.as_tuple().exponent
    return max(0,-exponent) if isinstance(exponent,int) else 99


def create_stock_count(connection: Connection, *, context: RequestContext, legal_entity_id: UUID,
                       warehouse_id: UUID, count_number: str, reference: str | None = None) -> UUID:
    require_permission(context,"inventory.count")
    warehouse=connection.execute(text("SELECT legal_entity_id,status FROM warehouses WHERE tenant_id=:tenant AND id=:warehouse"),
                                 {"tenant":context.tenant_id,"warehouse":warehouse_id}).mappings().first()
    if not warehouse or warehouse["status"]!="ACTIVE" or warehouse["legal_entity_id"]!=legal_entity_id:
        raise InventoryOperationsError("invalid active warehouse/legal entity")
    count_id,now=uuid4(),datetime.now(UTC)
    connection.execute(text("""
        INSERT INTO stock_counts
        (id,tenant_id,legal_entity_id,warehouse_id,count_number,status,reference,created_by_user_id,created_at,updated_at)
        VALUES (:id,:tenant,:entity,:warehouse,:number,'DRAFT',:reference,:actor,:now,:now)
    """),{"id":count_id,"tenant":context.tenant_id,"entity":legal_entity_id,"warehouse":warehouse_id,
           "number":count_number,"reference":reference,"actor":context.actor_user_id,"now":now})
    rows=connection.execute(text("""
        SELECT b.product_id,b.location_id,p.base_unit_id,b.on_hand
        FROM inventory_balances b
        JOIN warehouse_locations l ON l.tenant_id=b.tenant_id AND l.id=b.location_id
        JOIN products p ON p.tenant_id=b.tenant_id AND p.id=b.product_id
        WHERE b.tenant_id=:tenant AND l.warehouse_id=:warehouse ORDER BY l.code,p.sku
    """),{"tenant":context.tenant_id,"warehouse":warehouse_id}).mappings().all()
    for no,row in enumerate(rows,1):
        connection.execute(text("""
            INSERT INTO stock_count_lines
            (id,tenant_id,stock_count_id,line_no,product_id,location_id,unit_id,system_quantity,created_at)
            VALUES (:id,:tenant,:count,:no,:product,:location,:unit,:system,:now)
        """),{"id":uuid4(),"tenant":context.tenant_id,"count":count_id,"no":no,"product":row["product_id"],
               "location":row["location_id"],"unit":row["base_unit_id"],"system":row["on_hand"],"now":now})
    _audit(connection,context,"inventory.stock_count.created","stock_count",count_id,{"count_number":count_number})
    return count_id


def record_count(connection: Connection, *, context: RequestContext, count_id: UUID,
                 lines: list[tuple[UUID, Decimal]]) -> None:
    require_permission(context,"inventory.count")
    row=connection.execute(text("SELECT status FROM stock_counts WHERE tenant_id=:tenant AND id=:id FOR UPDATE"),
                           {"tenant":context.tenant_id,"id":count_id}).mappings().first()
    if not row: raise InventoryOperationsError("stock count not found")
    if row["status"] not in {"DRAFT","COUNTED"}: raise InventoryOperationsError("stock count is not editable")
    if not lines: raise InventoryOperationsError("count lines required")
    for line_id,quantity in lines:
        if quantity<0 or _scale(quantity)>8: raise InventoryOperationsError("invalid counted quantity")
        changed=connection.execute(text("""
            UPDATE stock_count_lines SET counted_quantity=:quantity
            WHERE tenant_id=:tenant AND stock_count_id=:count AND id=:line
        """),{"quantity":quantity,"tenant":context.tenant_id,"count":count_id,"line":line_id}).rowcount
        if not changed: raise InventoryOperationsError("count line not found")
    missing: int=connection.execute(text("""
        SELECT count(*) FROM stock_count_lines WHERE tenant_id=:tenant AND stock_count_id=:count AND counted_quantity IS NULL
    """),{"tenant":context.tenant_id,"count":count_id}).scalar_one()
    new_status="COUNTED" if missing==0 else "DRAFT";now=datetime.now(UTC)
    connection.execute(text("UPDATE stock_counts SET status=:status,counted_at=:now,updated_at=:now WHERE tenant_id=:tenant AND id=:id"),
                       {"status":new_status,"now":now,"tenant":context.tenant_id,"id":count_id})


def post_stock_count(connection: Connection, *, context: RequestContext, count_id: UUID,
                     idempotency_key: str) -> UUID | None:
    require_permission(context,"inventory.count.post")
    count=connection.execute(text("""
        SELECT id,legal_entity_id,count_number,status,posted_transaction_id
        FROM stock_counts WHERE tenant_id=:tenant AND id=:id FOR UPDATE
    """),{"tenant":context.tenant_id,"id":count_id}).mappings().first()
    if not count: raise InventoryOperationsError("stock count not found")
    if count["status"]=="POSTED": return count["posted_transaction_id"]
    if count["status"]!="COUNTED": raise InventoryOperationsError("stock count must be fully counted")
    rows=connection.execute(text("""
        SELECT product_id,location_id,unit_id,system_quantity,counted_quantity
        FROM stock_count_lines WHERE tenant_id=:tenant AND stock_count_id=:id ORDER BY line_no
    """),{"tenant":context.tenant_id,"id":count_id}).mappings().all()
    lines: list[StockLine]=[]
    for row in rows:
        variance=Decimal(row["counted_quantity"])-Decimal(row["system_quantity"])
        if variance:
            unit_precision: int=connection.execute(
                text("SELECT precision FROM units WHERE tenant_id=:tenant AND id=:unit"),
                {"tenant":context.tenant_id,"unit":row["unit_id"]},
            ).scalar_one()
            quantity=abs(variance).quantize(Decimal(1).scaleb(-unit_precision))
            lines.append(StockLine(product_id=row["product_id"],unit_id=row["unit_id"],location_id=row["location_id"],
                                   quantity=quantity,adjustment_direction=1 if variance>0 else -1))
    tx_id: UUID | None=None
    if lines:
        tx_id=post_inventory(connection,context=context,transaction_type="ADJUST",legal_entity_id=count["legal_entity_id"],
            branch_id=None,lines=lines,idempotency_key=idempotency_key,reference=count["count_number"],
            reason="Stock count variance",source_type="STOCK_COUNT",source_id=count_id,source_number=count["count_number"])
    connection.execute(text("UPDATE stock_counts SET status='POSTED',posted_transaction_id=:tx,updated_at=:now WHERE tenant_id=:tenant AND id=:id"),
                       {"tx":tx_id,"now":datetime.now(UTC),"tenant":context.tenant_id,"id":count_id})
    _audit(connection,context,"inventory.stock_count.posted","stock_count",count_id,{"transaction_id":str(tx_id) if tx_id else None})
    write_outbox(connection,tenant_id=context.tenant_id,event_type="inventory.stock_count.posted",
                 aggregate_type="stock_count",aggregate_id=count_id,payload={"transaction_id":str(tx_id) if tx_id else None})
    return tx_id


def upsert_reorder_policy(connection: Connection, *, context: RequestContext, product_id: UUID, location_id: UUID,
                          reorder_point: Decimal, target_quantity: Decimal, active: bool = True) -> UUID:
    require_permission(context,"inventory.reorder.manage")
    if reorder_point<0 or target_quantity<reorder_point: raise InventoryOperationsError("target quantity must be at least reorder point")
    if max(_scale(reorder_point),_scale(target_quantity))>8: raise InventoryOperationsError("reorder quantity precision exceeds 8 decimals")
    valid: bool=bool(connection.execute(text("""
        SELECT EXISTS(SELECT 1 FROM products p JOIN warehouse_locations l ON l.tenant_id=p.tenant_id
        WHERE p.tenant_id=:tenant AND p.id=:product AND l.id=:location
        AND p.status='ACTIVE' AND p.product_type<>'SERVICE' AND l.status='ACTIVE' AND l.allow_stock)
    """),{"tenant":context.tenant_id,"product":product_id,"location":location_id}).scalar_one())
    if not valid: raise InventoryOperationsError("invalid active product/location")
    policy_id,now=uuid4(),datetime.now(UTC)
    result: UUID=connection.execute(text("""
        INSERT INTO reorder_policies
        (id,tenant_id,product_id,location_id,reorder_point,target_quantity,is_active,created_at,updated_at)
        VALUES (:id,:tenant,:product,:location,:point,:target,:active,:now,:now)
        ON CONFLICT (tenant_id,product_id,location_id) DO UPDATE
        SET reorder_point=EXCLUDED.reorder_point,target_quantity=EXCLUDED.target_quantity,is_active=EXCLUDED.is_active,updated_at=EXCLUDED.updated_at
        RETURNING id
    """),{"id":policy_id,"tenant":context.tenant_id,"product":product_id,"location":location_id,
           "point":reorder_point,"target":target_quantity,"active":active,"now":now}).scalar_one()
    _audit(connection,context,"inventory.reorder_policy.upserted","reorder_policy",result,{})
    return result


def reorder_status(connection: Connection, tenant_id: UUID) -> list[dict[str, object]]:
    rows=connection.execute(text("""
        SELECT rp.id,rp.product_id,p.sku,p.name product_name,rp.location_id,l.code location_code,w.code warehouse_code,
               rp.reorder_point,rp.target_quantity,COALESCE(b.on_hand,0) on_hand,
               GREATEST(rp.target_quantity-COALESCE(b.on_hand,0),0) suggested_quantity
        FROM reorder_policies rp
        JOIN products p ON p.tenant_id=rp.tenant_id AND p.id=rp.product_id
        JOIN warehouse_locations l ON l.tenant_id=rp.tenant_id AND l.id=rp.location_id
        JOIN warehouses w ON w.tenant_id=l.tenant_id AND w.id=l.warehouse_id
        LEFT JOIN inventory_balances b ON b.tenant_id=rp.tenant_id AND b.product_id=rp.product_id AND b.location_id=rp.location_id
        WHERE rp.tenant_id=:tenant AND rp.is_active
        ORDER BY (COALESCE(b.on_hand,0)<=rp.reorder_point) DESC,p.sku,l.code
    """),{"tenant":tenant_id}).mappings().all()
    return [dict(x) for x in rows]
