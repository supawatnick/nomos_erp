from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit


class EntitlementDenied(PermissionError):
    pass
class CommercialError(ValueError):
    pass


def require_entitlement(db: Connection, *, tenant_id: UUID, feature_code: str, period_key: str | None=None,
                        increment: int=0) -> None:
    row=db.execute(text("""SELECT s.status,s.trial_ends_at,e.limit_value
      FROM saas_subscriptions s JOIN saas_plan_entitlements e ON e.plan_id=s.plan_id
      WHERE s.tenant_id=:t AND e.feature_code=:f"""),{"t":tenant_id,"f":feature_code}).mappings().first()
    now=datetime.now(UTC)
    if not row or row["status"] not in ("TRIAL","ACTIVE") or (row["status"]=="TRIAL" and row["trial_ends_at"] and row["trial_ends_at"]<now):
        raise EntitlementDenied("tenant subscription does not entitle this feature")
    limit=row["limit_value"]
    if limit is not None and period_key is not None:
        usage=db.execute(text("""SELECT usage_value FROM saas_usage_counters
          WHERE tenant_id=:t AND feature_code=:f AND period_key=:p FOR UPDATE"""),
          {"t":tenant_id,"f":feature_code,"p":period_key}).scalar_one_or_none() or 0
        if usage+increment>limit: raise EntitlementDenied("commercial feature limit exceeded")
        if increment:
            db.execute(text("""INSERT INTO saas_usage_counters (id,tenant_id,feature_code,period_key,usage_value,updated_at)
              VALUES (:id,:t,:f,:p,:v,now()) ON CONFLICT (tenant_id,feature_code,period_key)
              DO UPDATE SET usage_value=saas_usage_counters.usage_value+:v,updated_at=now()"""),
              {"id":uuid4(),"t":tenant_id,"f":feature_code,"p":period_key,"v":increment})


def provision_tenant(db: Connection, *, tenant_id: UUID, plan_code: str) -> UUID:
    existing=db.execute(text("SELECT id FROM saas_subscriptions WHERE tenant_id=:t"),{"t":tenant_id}).scalar_one_or_none()
    if existing: return existing
    plan=db.execute(text("SELECT id,trial_days FROM saas_plans WHERE code=:c AND status='ACTIVE'"),{"c":plan_code}).mappings().first()
    if not plan: raise CommercialError("active plan not found")
    now=datetime.now(UTC);trial_days=plan["trial_days"];sub=uuid4()
    db.execute(text("""INSERT INTO saas_subscriptions
      (id,tenant_id,plan_id,status,trial_ends_at,created_at,updated_at)
      VALUES (:id,:t,:p,:status,:trial,now(),now())"""),{"id":sub,"t":tenant_id,"p":plan["id"],
      "status":"TRIAL" if trial_days else "ACTIVE","trial":now+timedelta(days=trial_days) if trial_days else None})
    return sub


def transition_subscription(db: Connection, *, context: RequestContext, status: str) -> None:
    require_permission(context,"subscription.manage")
    if status not in {"ACTIVE","SUSPENDED","CANCELLED"}: raise CommercialError("unsupported subscription transition")
    row=db.execute(text("SELECT id,status,plan_id FROM saas_subscriptions WHERE tenant_id=:t FOR UPDATE"),
                   {"t":context.tenant_id}).mappings().first()
    if not row: raise CommercialError("subscription not found")
    plan=db.execute(text("SELECT retention_days FROM saas_plans WHERE id=:id"),{"id":row["plan_id"]}).mappings().one()
    now=datetime.now(UTC)
    db.execute(text("""UPDATE saas_subscriptions SET status=:status,cancelled_at=:cancelled,retention_until=:retention,updated_at=now()
      WHERE tenant_id=:t"""),{"status":status,"cancelled":now if status=="CANCELLED" else None,
      "retention":now+timedelta(days=plan["retention_days"]) if status=="CANCELLED" else None,"t":context.tenant_id})
    write_audit(db,tenant_id=context.tenant_id,request_id=context.request_id,action="saas.subscription.transitioned",
      actor_user_id=context.actor_user_id,actor_tenant_user_id=context.tenant_user_id,target_type="saas_subscription",
      target_id=row["id"],metadata={"from":row["status"],"to":status})


def request_tenant_export(db: Connection, *, context: RequestContext) -> UUID:
    require_permission(context,"tenant.export")
    export_id=uuid4()
    db.execute(text("""INSERT INTO saas_exports
      (id,tenant_id,requested_by_tenant_user_id,status,requested_at)
      VALUES (:id,:t,:u,'REQUESTED',now())"""),{"id":export_id,"t":context.tenant_id,"u":context.tenant_user_id})
    write_audit(db,tenant_id=context.tenant_id,request_id=context.request_id,action="saas.export.requested",
      actor_user_id=context.actor_user_id,actor_tenant_user_id=context.tenant_user_id,target_type="saas_export",
      target_id=export_id,metadata={})
    return export_id
