import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, text
from sqlalchemy.exc import IntegrityError

from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit, write_outbox


class InventoryError(ValueError):
    pass


class InsufficientStock(InventoryError):
    pass


class IdempotencyConflict(InventoryError):
    pass


@dataclass(frozen=True)
class StockLine:
    product_id: UUID
    unit_id: UUID
    location_id: UUID
    quantity: Decimal
    destination_location_id: UUID | None = None
    adjustment_direction: int | None = None


PERMISSION = {
    "RECEIVE": "inventory.receive",
    "OPENING": "inventory.receive",
    "ISSUE": "inventory.issue",
    "TRANSFER": "inventory.transfer",
    "ADJUST": "inventory.adjust",
    "REVERSAL": "inventory.adjust",
}


def _scale(value: Decimal) -> int:
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int):
        return 99
    return max(0, -exponent)


def _decimal(value: Decimal) -> Decimal:
    if value <= 0 or _scale(value) > 8:
        raise InventoryError("quantity must be positive with at most 8 decimal places")
    return value


def _fingerprint(kind: str, legal_entity_id: UUID, branch_id: UUID | None, lines: list[StockLine], reference: str | None, reason: str | None) -> str:
    body = {
        "type": kind, "legal_entity_id": str(legal_entity_id), "branch_id": str(branch_id) if branch_id else None,
        "reference": reference, "reason": reason,
        "lines": [
            {"product_id":str(x.product_id),"unit_id":str(x.unit_id),"location_id":str(x.location_id),
             "destination_location_id":str(x.destination_location_id) if x.destination_location_id else None,
             "adjustment_direction":x.adjustment_direction,"quantity":format(x.quantity, "f")} for x in lines
        ],
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",",":")).encode()).hexdigest()


def _claim(connection: Connection, tenant_id: UUID, key: str, fingerprint: str) -> UUID | None:
    row = connection.execute(text("""
        SELECT request_fingerprint,status,resource_id FROM idempotency_keys
        WHERE tenant_id=:tenant AND scope='inventory.post' AND idempotency_key=:key
        FOR UPDATE
    """), {"tenant":tenant_id,"key":key}).mappings().first()
    if row:
        if row["request_fingerprint"] != fingerprint:
            raise IdempotencyConflict("idempotency key payload conflict")
        if row["status"] == "COMPLETED":
            return row["resource_id"]
        raise IdempotencyConflict("idempotency request already in progress")
    now = datetime.now(UTC)
    try:
        connection.execute(text("""
            INSERT INTO idempotency_keys
            (id,tenant_id,scope,idempotency_key,request_fingerprint,status,expires_at,created_at,updated_at)
            VALUES (:id,:tenant,'inventory.post',:key,:fp,'IN_PROGRESS',:expires,:now,:now)
        """), {"id":uuid4(),"tenant":tenant_id,"key":key,"fp":fingerprint,"expires":now+timedelta(days=1),"now":now})
    except IntegrityError as exc:
        raise IdempotencyConflict("concurrent idempotency key") from exc
    return None


def _validate_line(connection: Connection, tenant_id: UUID, legal_entity_id: UUID, line: StockLine, destination: UUID | None = None) -> Decimal:
    _decimal(line.quantity)
    row = connection.execute(text("""
        SELECT p.status product_status,p.product_type,p.base_unit_id,u.precision,
               pu.factor_to_base,l.status location_status,l.allow_stock,w.status warehouse_status,w.legal_entity_id
        FROM products p
        JOIN units u ON u.tenant_id=p.tenant_id AND u.id=:unit
        LEFT JOIN product_units pu ON pu.tenant_id=p.tenant_id AND pu.product_id=p.id AND pu.unit_id=:unit
        JOIN warehouse_locations l ON l.tenant_id=p.tenant_id AND l.id=:location
        JOIN warehouses w ON w.tenant_id=l.tenant_id AND w.id=l.warehouse_id
        WHERE p.tenant_id=:tenant AND p.id=:product
    """), {"tenant":tenant_id,"product":line.product_id,"unit":line.unit_id,"location":line.location_id}).mappings().first()
    if not row or row["product_status"]!="ACTIVE" or row["product_type"]=="SERVICE" or row["location_status"]!="ACTIVE" or not row["allow_stock"] or row["warehouse_status"]!="ACTIVE" or row["legal_entity_id"]!=legal_entity_id:
        raise InventoryError("invalid active stock product/location/organization")
    if _scale(line.quantity) > int(row["precision"]):
        raise InventoryError("quantity exceeds unit precision")
    factor = Decimal(1) if line.unit_id == row["base_unit_id"] else row["factor_to_base"]
    if factor is None:
        raise InventoryError("unit is not configured for product")
    base = line.quantity * Decimal(factor)
    if _scale(base) > 8:
        raise InventoryError("base quantity exceeds precision")
    if destination:
        dest = connection.execute(text("""
            SELECT l.status,l.allow_stock,w.status warehouse_status,w.legal_entity_id
            FROM warehouse_locations l JOIN warehouses w ON w.tenant_id=l.tenant_id AND w.id=l.warehouse_id
            WHERE l.tenant_id=:tenant AND l.id=:location
        """), {"tenant":tenant_id,"location":destination}).mappings().first()
        if not dest or dest["status"]!="ACTIVE" or not dest["allow_stock"] or dest["warehouse_status"]!="ACTIVE" or dest["legal_entity_id"]!=legal_entity_id or destination==line.location_id:
            raise InventoryError("invalid transfer destination")
    return base


def _lock_balances(connection: Connection, tenant_id: UUID, keys: list[tuple[UUID,UUID]]) -> dict[tuple[UUID,UUID], Decimal]:
    unique = sorted(set(keys), key=lambda x:(str(x[0]),str(x[1])))
    for product, location in unique:
        connection.execute(text("""
            INSERT INTO inventory_balances (tenant_id,product_id,location_id,on_hand,updated_at)
            VALUES (:tenant,:product,:location,0,:now) ON CONFLICT DO NOTHING
        """), {"tenant":tenant_id,"product":product,"location":location,"now":datetime.now(UTC)})
    result: dict[tuple[UUID,UUID],Decimal] = {}
    for product, location in unique:
        value: Any = connection.execute(text("""
            SELECT on_hand FROM inventory_balances
            WHERE tenant_id=:tenant AND product_id=:product AND location_id=:location FOR UPDATE
        """), {"tenant":tenant_id,"product":product,"location":location}).scalar_one()
        result[(product,location)] = Decimal(value)
    return result


def post_inventory(
    connection: Connection, *, context: RequestContext, transaction_type: str,
    legal_entity_id: UUID, branch_id: UUID | None, lines: list[StockLine],
    idempotency_key: str, reference: str | None = None, reason: str | None = None,
    source_type: str | None = None, source_id: UUID | None = None, source_number: str | None = None,
) -> UUID:
    kind = transaction_type.upper()
    if kind not in {"RECEIVE","ISSUE","TRANSFER","ADJUST","OPENING"} or not lines:
        raise InventoryError("invalid inventory command")
    require_permission(context, PERMISSION[kind])
    fp = _fingerprint(kind, legal_entity_id, branch_id, lines, reference, reason)
    replay = _claim(connection, context.tenant_id, idempotency_key, fp)
    if replay:
        return replay

    effects: list[tuple[StockLine,UUID,Decimal,int]] = []
    for line in lines:
        destination = line.destination_location_id if kind=="TRANSFER" else None
        base = _validate_line(connection, context.tenant_id, legal_entity_id, line, destination)
        if kind=="TRANSFER":
            if destination is None:
                raise InventoryError("transfer destination required")
            effects += [(line,line.location_id,base,-1),(line,destination,base,1)]
        else:
            if kind=="ADJUST":
                if line.adjustment_direction not in (-1, 1):
                    raise InventoryError("adjustment_direction must be -1 or 1")
                direction = line.adjustment_direction
            else:
                direction = -1 if kind=="ISSUE" else 1
            effects.append((line,line.location_id,base,direction))

    deltas: dict[tuple[UUID,UUID],Decimal] = {}
    for line, location, base, direction in effects:
        key=(line.product_id,location)
        deltas[key]=deltas.get(key,Decimal(0)) + base*direction
    balances = _lock_balances(connection, context.tenant_id, list(deltas))
    for key, delta in deltas.items():
        if balances[key]+delta < 0:
            raise InsufficientStock("insufficient stock")

    now, tx_id = datetime.now(UTC), uuid4()
    connection.execute(text("""
        INSERT INTO inventory_transactions
        (id,tenant_id,legal_entity_id,branch_id,transaction_type,status,source_type,source_id,source_number,
         reference,reason,posted_at,posted_by_user_id,request_id,idempotency_key,created_at)
        VALUES (:id,:tenant,:entity,:branch,:kind,'POSTED',:source_type,:source_id,:source_number,
                :reference,:reason,:now,:actor,:request,:key,:now)
    """), {"id":tx_id,"tenant":context.tenant_id,"entity":legal_entity_id,"branch":branch_id,"kind":kind,
            "source_type":source_type,"source_id":source_id,"source_number":source_number,"reference":reference,
            "reason":reason,"now":now,"actor":context.actor_user_id,"request":context.request_id,"key":idempotency_key})
    for number,(line,location,base,direction) in enumerate(effects,1):
        connection.execute(text("""
            INSERT INTO inventory_transaction_lines
            (id,tenant_id,transaction_id,line_no,product_id,unit_id,location_id,quantity,base_quantity,direction,created_at)
            VALUES (:id,:tenant,:tx,:no,:product,:unit,:location,:quantity,:base,:direction,:now)
        """), {"id":uuid4(),"tenant":context.tenant_id,"tx":tx_id,"no":number,"product":line.product_id,
                "unit":line.unit_id,"location":location,"quantity":line.quantity,"base":base,"direction":direction,"now":now})
    for (product,location),delta in deltas.items():
        connection.execute(text("""
            UPDATE inventory_balances SET on_hand=on_hand+:delta,updated_at=:now
            WHERE tenant_id=:tenant AND product_id=:product AND location_id=:location
        """), {"delta":delta,"now":now,"tenant":context.tenant_id,"product":product,"location":location})
    write_audit(connection,tenant_id=context.tenant_id,request_id=context.request_id,action="inventory.transaction.posted",
                actor_user_id=context.actor_user_id,actor_tenant_user_id=context.tenant_user_id,target_type="inventory_transaction",
                target_id=tx_id,metadata={"transaction_type":kind,"reference":reference})
    write_outbox(connection,tenant_id=context.tenant_id,aggregate_type="inventory_transaction",aggregate_id=tx_id,
                 event_type="inventory.transaction.posted",payload={"transaction_id":str(tx_id),"transaction_type":kind,
                 "source_type":source_type,"source_id":str(source_id) if source_id else None})
    connection.execute(text("""
        UPDATE idempotency_keys SET status='COMPLETED',resource_type='inventory_transaction',resource_id=:resource,
        response_code=201,response_body=CAST(:body AS JSONB),updated_at=:now
        WHERE tenant_id=:tenant AND scope='inventory.post' AND idempotency_key=:key
    """), {"resource":tx_id,"body":json.dumps({"id":str(tx_id)}),"now":now,"tenant":context.tenant_id,"key":idempotency_key})
    return tx_id


def reverse_inventory(connection: Connection, *, context: RequestContext, transaction_id: UUID, idempotency_key: str, reason: str) -> UUID:
    require_permission(context, "inventory.adjust")
    fp=hashlib.sha256(f"reverse:{transaction_id}:{reason}".encode()).hexdigest()
    replay=_claim(connection,context.tenant_id,idempotency_key,fp)
    if replay:
        return replay
    original = connection.execute(text("""
        SELECT id,legal_entity_id,branch_id,transaction_type,reversed_by_id FROM inventory_transactions
        WHERE tenant_id=:tenant AND id=:id AND status='POSTED' FOR UPDATE
    """), {"tenant":context.tenant_id,"id":transaction_id}).mappings().first()
    if not original:
        raise InventoryError("transaction not found")
    if original["transaction_type"]=="REVERSAL" or original["reversed_by_id"]:
        raise InventoryError("transaction cannot be reversed")
    rows=connection.execute(text("""
        SELECT product_id,unit_id,location_id,quantity,base_quantity,direction
        FROM inventory_transaction_lines WHERE tenant_id=:tenant AND transaction_id=:id ORDER BY line_no
    """),{"tenant":context.tenant_id,"id":transaction_id}).mappings().all()
    deltas: dict[tuple[UUID,UUID],Decimal]={}
    for row in rows:
        key=(row["product_id"],row["location_id"])
        deltas[key]=deltas.get(key,Decimal(0)) - Decimal(row["base_quantity"])*int(row["direction"])
    balances=_lock_balances(connection,context.tenant_id,list(deltas))
    for key,delta in deltas.items():
        if balances[key]+delta<0:
            raise InsufficientStock("reversal would create negative stock")
    now, reversal_id=datetime.now(UTC),uuid4()
    connection.execute(text("""
        INSERT INTO inventory_transactions
        (id,tenant_id,legal_entity_id,branch_id,transaction_type,status,reference,reason,reversal_of_id,
         posted_at,posted_by_user_id,request_id,idempotency_key,created_at)
        VALUES (:id,:tenant,:entity,:branch,'REVERSAL','POSTED',:reference,:reason,:original,:now,:actor,:request,:key,:now)
    """),{"id":reversal_id,"tenant":context.tenant_id,"entity":original["legal_entity_id"],"branch":original["branch_id"],
           "reference":f"REV:{transaction_id}","reason":reason,"original":transaction_id,"now":now,
           "actor":context.actor_user_id,"request":context.request_id,"key":idempotency_key})
    for no,row in enumerate(rows,1):
        connection.execute(text("""
            INSERT INTO inventory_transaction_lines
            (id,tenant_id,transaction_id,line_no,product_id,unit_id,location_id,quantity,base_quantity,direction,created_at)
            VALUES (:id,:tenant,:tx,:no,:product,:unit,:location,:quantity,:base,:direction,:now)
        """),{"id":uuid4(),"tenant":context.tenant_id,"tx":reversal_id,"no":no,"product":row["product_id"],"unit":row["unit_id"],
              "location":row["location_id"],"quantity":row["quantity"],"base":row["base_quantity"],"direction":-int(row["direction"]),"now":now})
    for (product,location),delta in deltas.items():
        connection.execute(text("UPDATE inventory_balances SET on_hand=on_hand+:delta,updated_at=:now WHERE tenant_id=:tenant AND product_id=:product AND location_id=:location"),
                           {"delta":delta,"now":now,"tenant":context.tenant_id,"product":product,"location":location})
    connection.execute(text("UPDATE inventory_transactions SET reversed_by_id=:reversal WHERE tenant_id=:tenant AND id=:original"),
                       {"reversal":reversal_id,"tenant":context.tenant_id,"original":transaction_id})
    write_audit(connection,tenant_id=context.tenant_id,request_id=context.request_id,action="inventory.transaction.reversed",
                actor_user_id=context.actor_user_id,actor_tenant_user_id=context.tenant_user_id,target_type="inventory_transaction",
                target_id=reversal_id,metadata={"reversal_of_id":str(transaction_id),"reason":reason})
    write_outbox(connection,tenant_id=context.tenant_id,aggregate_type="inventory_transaction",aggregate_id=reversal_id,
                 event_type="inventory.transaction.reversed",payload={"transaction_id":str(reversal_id),"reversal_of_id":str(transaction_id)})
    connection.execute(text("""
        UPDATE idempotency_keys SET status='COMPLETED',resource_type='inventory_transaction',resource_id=:resource,
        response_code=201,response_body=CAST(:body AS JSONB),updated_at=:now
        WHERE tenant_id=:tenant AND scope='inventory.post' AND idempotency_key=:key
    """),{"resource":reversal_id,"body":json.dumps({"id":str(reversal_id)}),"now":now,"tenant":context.tenant_id,"key":idempotency_key})
    return reversal_id


def reconcile_inventory(connection: Connection, tenant_id: UUID) -> list[dict[str,Any]]:
    rows=connection.execute(text("""
        WITH ledger AS (
          SELECT l.tenant_id,l.product_id,l.location_id,
                 sum(l.base_quantity*l.direction)::numeric(24,8) AS ledger_on_hand
          FROM inventory_transaction_lines l JOIN inventory_transactions t
            ON t.tenant_id=l.tenant_id AND t.id=l.transaction_id
          WHERE l.tenant_id=:tenant AND t.status='POSTED'
          GROUP BY l.tenant_id,l.product_id,l.location_id
        ), keys AS (
          SELECT tenant_id,product_id,location_id FROM ledger
          UNION SELECT tenant_id,product_id,location_id FROM inventory_balances WHERE tenant_id=:tenant
        )
        SELECT k.product_id,k.location_id,coalesce(l.ledger_on_hand,0) ledger_on_hand,coalesce(b.on_hand,0) balance_on_hand
        FROM keys k LEFT JOIN ledger l USING(tenant_id,product_id,location_id)
        LEFT JOIN inventory_balances b USING(tenant_id,product_id,location_id)
        WHERE coalesce(l.ledger_on_hand,0) <> coalesce(b.on_hand,0)
        ORDER BY k.product_id,k.location_id
    """),{"tenant":tenant_id}).mappings().all()
    return [dict(x) for x in rows]
