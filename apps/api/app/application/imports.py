from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.application.catalog import create_product
from app.application.inventory import StockLine, post_inventory
from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit, write_outbox


class ImportError(ValueError):
    pass


def create_batch(connection: Connection, *, context: RequestContext, import_type: str,
                 source_name: str, rows: list[dict[str, Any]]) -> UUID:
    kind=import_type.upper()
    require_permission(context,"product.manage" if kind=="PRODUCT" else "inventory.adjust")
    if kind not in {"PRODUCT","OPENING_STOCK"} or not rows:
        raise ImportError("unsupported or empty import")
    batch_id,now=uuid4(),datetime.now(UTC)
    connection.execute(text("""
      INSERT INTO import_batches(id,tenant_id,import_type,status,source_name,created_by_user_id,total_rows,created_at,updated_at)
      VALUES(:id,:tenant,:kind,'UPLOADED',:name,:actor,:count,:now,:now)
    """),{"id":batch_id,"tenant":context.tenant_id,"kind":kind,"name":source_name[:240],
           "actor":context.actor_user_id,"count":len(rows),"now":now})
    for number,row in enumerate(rows,1):
        connection.execute(text("""
          INSERT INTO import_rows(id,tenant_id,batch_id,row_number,source_data,normalized_data,errors,created_at)
          VALUES(:id,:tenant,:batch,:number,CAST(:source AS JSONB),'{}'::jsonb,'[]'::jsonb,:now)
        """),{"id":uuid4(),"tenant":context.tenant_id,"batch":batch_id,"number":number,
               "source":__import__("json").dumps(row),"now":now})
    write_audit(connection,tenant_id=context.tenant_id,request_id=context.request_id,action="import.batch.uploaded",
                actor_user_id=context.actor_user_id,actor_tenant_user_id=context.tenant_user_id,
                target_type="import_batch",target_id=batch_id,metadata={"import_type":kind,"rows":len(rows)})
    return batch_id


def _product_row(connection: Connection, tenant: UUID, source: dict[str, Any]) -> tuple[dict[str, Any],list[dict[str,str]]]:
    errors:list[dict[str,str]]=[]
    sku=str(source.get("sku","")).strip();name=str(source.get("name","")).strip()
    unit_code=str(source.get("base_unit_code","")).strip()
    product_type=str(source.get("product_type","STOCKABLE")).strip().upper()
    tracking=str(source.get("tracking_type","NONE")).strip().upper()
    unit=connection.execute(text("SELECT id FROM units WHERE tenant_id=:t AND code=:c AND status='ACTIVE'"),
                            {"t":tenant,"c":unit_code}).scalar_one_or_none()
    category=None
    category_code=str(source.get("category_code","")).strip()
    if category_code:
        category=connection.execute(text("SELECT id FROM categories WHERE tenant_id=:t AND code=:c AND status='ACTIVE'"),
                                    {"t":tenant,"c":category_code}).scalar_one_or_none()
    if not sku: errors.append({"field":"sku","code":"REQUIRED"})
    if not name: errors.append({"field":"name","code":"REQUIRED"})
    if not unit: errors.append({"field":"base_unit_code","code":"UNKNOWN_REFERENCE"})
    if category_code and not category: errors.append({"field":"category_code","code":"UNKNOWN_REFERENCE"})
    if product_type not in {"STOCKABLE","CONSUMABLE","SERVICE"}: errors.append({"field":"product_type","code":"INVALID_VALUE"})
    if tracking not in {"NONE","LOT","SERIAL"}: errors.append({"field":"tracking_type","code":"INVALID_VALUE"})
    duplicate=connection.execute(text("SELECT 1 FROM products WHERE tenant_id=:t AND sku=:sku"),{"t":tenant,"sku":sku}).first()
    if duplicate: errors.append({"field":"sku","code":"DUPLICATE_RESOURCE"})
    return {"sku":sku,"name":name,"base_unit_id":str(unit) if unit else None,"category_id":str(category) if category else None,
            "product_type":product_type,"tracking_type":tracking,"description":source.get("description")},errors


def _opening_row(connection: Connection, tenant: UUID, source: dict[str, Any]) -> tuple[dict[str, Any],list[dict[str,str]]]:
    errors:list[dict[str,str]]=[]
    def ref(sql:str,value:str)->UUID|None:
        return connection.execute(text(sql),{"t":tenant,"c":value}).scalar_one_or_none()
    entity=ref("SELECT id FROM legal_entities WHERE tenant_id=:t AND code=:c AND status='ACTIVE'",str(source.get("legal_entity_code","")).strip())
    product=ref("SELECT id FROM products WHERE tenant_id=:t AND sku=:c AND status='ACTIVE'",str(source.get("sku","")).strip())
    unit=ref("SELECT id FROM units WHERE tenant_id=:t AND code=:c AND status='ACTIVE'",str(source.get("unit_code","")).strip())
    location=connection.execute(text("""
      SELECT l.id FROM warehouse_locations l JOIN warehouses w ON w.tenant_id=l.tenant_id AND w.id=l.warehouse_id
      WHERE l.tenant_id=:t AND w.code=:w AND l.code=:c AND l.status='ACTIVE' AND l.allow_stock
    """),{"t":tenant,"w":str(source.get("warehouse_code","")).strip(),"c":str(source.get("location_code","")).strip()}).scalar_one_or_none()
    for field,value in (("legal_entity_code",entity),("sku",product),("unit_code",unit),("location_code",location)):
        if not value: errors.append({"field":field,"code":"UNKNOWN_REFERENCE"})
    try:
        quantity=Decimal(str(source.get("quantity","")))
        exponent=quantity.as_tuple().exponent\n        if quantity<=0 or not isinstance(exponent,int) or max(0,-exponent)>8: raise InvalidOperation
    except (InvalidOperation,ValueError):
        quantity=Decimal(0);errors.append({"field":"quantity","code":"INVALID_DECIMAL"})
    return {"legal_entity_id":str(entity) if entity else None,"product_id":str(product) if product else None,
            "unit_id":str(unit) if unit else None,"location_id":str(location) if location else None,
            "quantity":format(quantity,"f")},errors


def validate_batch(connection: Connection, *, context: RequestContext, batch_id: UUID) -> dict[str,int]:
    batch=connection.execute(text("SELECT import_type,status FROM import_batches WHERE tenant_id=:t AND id=:id FOR UPDATE"),
                             {"t":context.tenant_id,"id":batch_id}).mappings().first()
    if not batch: raise ImportError("batch not found")
    require_permission(context,"product.manage" if batch["import_type"]=="PRODUCT" else "inventory.adjust")
    if batch["status"]=="COMMITTED": raise ImportError("committed batch is immutable")
    rows=connection.execute(text("SELECT id,source_data FROM import_rows WHERE tenant_id=:t AND batch_id=:b ORDER BY row_number"),
                            {"t":context.tenant_id,"b":batch_id}).mappings().all()
    seen:set[str]=set();valid=errors_count=0
    for row in rows:
        normalized,errors=(_product_row(connection,context.tenant_id,row["source_data"]) if batch["import_type"]=="PRODUCT"
                           else _opening_row(connection,context.tenant_id,row["source_data"]))
        identity=str(normalized.get("sku") or "") if batch["import_type"]=="PRODUCT" else "|".join(str(normalized.get(k)) for k in ("product_id","location_id"))
        if identity in seen: errors.append({"field":"row","code":"DUPLICATE_FILE_ROW"})
        seen.add(identity)
        connection.execute(text("UPDATE import_rows SET normalized_data=CAST(:n AS JSONB),errors=CAST(:e AS JSONB) WHERE id=:id"),
                           {"n":__import__("json").dumps(normalized),"e":__import__("json").dumps(errors),"id":row["id"]})
        if errors: errors_count+=1
        else: valid+=1
    status="READY_TO_COMMIT" if errors_count==0 else "VALIDATED_WITH_ERRORS"
    connection.execute(text("UPDATE import_batches SET status=:s,valid_rows=:v,error_rows=:e,updated_at=:now WHERE tenant_id=:t AND id=:id"),
                       {"s":status,"v":valid,"e":errors_count,"now":datetime.now(UTC),"t":context.tenant_id,"id":batch_id})
    write_audit(connection,tenant_id=context.tenant_id,request_id=context.request_id,action="import.batch.validated",
                actor_user_id=context.actor_user_id,actor_tenant_user_id=context.tenant_user_id,target_type="import_batch",
                target_id=batch_id,metadata={"valid_rows":valid,"error_rows":errors_count})
    return {"valid_rows":valid,"error_rows":errors_count}


def commit_batch(connection: Connection, *, context: RequestContext, batch_id: UUID) -> list[UUID]:
    batch=connection.execute(text("SELECT import_type,status,committed_transaction_id FROM import_batches WHERE tenant_id=:t AND id=:id FOR UPDATE"),
                             {"t":context.tenant_id,"id":batch_id}).mappings().first()
    if not batch: raise ImportError("batch not found")
    require_permission(context,"product.manage" if batch["import_type"]=="PRODUCT" else "inventory.adjust")
    if batch["status"]=="COMMITTED":
        return [batch["committed_transaction_id"]] if batch["committed_transaction_id"] else []
    if batch["status"]!="READY_TO_COMMIT": raise ImportError("batch must validate without errors before commit")
    rows=connection.execute(text("SELECT id,normalized_data FROM import_rows WHERE tenant_id=:t AND batch_id=:b ORDER BY row_number"),
                            {"t":context.tenant_id,"b":batch_id}).mappings().all()
    results:list[UUID]=[]
    if batch["import_type"]=="PRODUCT":
        for row in rows:
            d=row["normalized_data"]
            target=create_product(connection,context=context,sku=d["sku"],name=d["name"],product_type=d["product_type"],
                                  base_unit_id=UUID(d["base_unit_id"]),category_id=UUID(d["category_id"]) if d["category_id"] else None,
                                  tracking_type=d["tracking_type"],description=d.get("description"))
            results.append(target)
            connection.execute(text("UPDATE import_rows SET target_id=:target WHERE id=:id"),{"target":target,"id":row["id"]})
    else:
        grouped:dict[UUID,list[StockLine]]={}
        for row in rows:
            d=row["normalized_data"];entity=UUID(d["legal_entity_id"])
            grouped.setdefault(entity,[]).append(StockLine(UUID(d["product_id"]),UUID(d["unit_id"]),UUID(d["location_id"]),Decimal(d["quantity"])))
        if len(grouped)!=1: raise ImportError("opening stock batch must contain one legal entity")
        entity,lines=next(iter(grouped.items()))
        tx=post_inventory(connection,context=context,transaction_type="OPENING",legal_entity_id=entity,branch_id=None,
                          lines=lines,idempotency_key=f"import-opening-{batch_id}",reference=f"IMPORT:{batch_id}",
                          reason="Opening stock import",source_type="IMPORT_BATCH",source_id=batch_id,source_number=str(batch_id))
        results.append(tx)
        connection.execute(text("UPDATE import_batches SET committed_transaction_id=:tx WHERE tenant_id=:t AND id=:id"),
                           {"tx":tx,"t":context.tenant_id,"id":batch_id})
    now=datetime.now(UTC)
    connection.execute(text("UPDATE import_batches SET status='COMMITTED',committed_at=:now,updated_at=:now WHERE tenant_id=:t AND id=:id"),
                       {"now":now,"t":context.tenant_id,"id":batch_id})
    write_audit(connection,tenant_id=context.tenant_id,request_id=context.request_id,action="import.batch.committed",
                actor_user_id=context.actor_user_id,actor_tenant_user_id=context.tenant_user_id,target_type="import_batch",
                target_id=batch_id,metadata={"targets":[str(x) for x in results]})
    write_outbox(connection,tenant_id=context.tenant_id,aggregate_type="import_batch",aggregate_id=batch_id,
                 event_type="import.batch.committed",payload={"import_type":batch["import_type"],"targets":[str(x) for x in results]})
    return results
