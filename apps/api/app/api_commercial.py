from fastapi import APIRouter, Header, Request
from sqlalchemy import create_engine, text

from app.api_master import trusted_context
from app.application.commercial import (
    request_tenant_export,
    require_entitlement,
    transition_subscription,
)
from app.core.config import get_settings
from app.domain.security import require_permission

router=APIRouter(prefix="/api/v1/commercial",tags=["commercial"])
def _engine(): return create_engine(get_settings().database_url,pool_pre_ping=True)
def _ctx(r,a,t): return trusted_context(r,a,t)

@router.get("/subscription")
def subscription(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id);require_permission(c,"subscription.read")
    with _engine().connect() as db:
        row=db.execute(text("""SELECT s.id,s.status,s.trial_ends_at,s.current_period_ends_at,s.cancelled_at,s.retention_until,
          p.code plan_code,p.name plan_name FROM saas_subscriptions s JOIN saas_plans p ON p.id=s.plan_id WHERE s.tenant_id=:t"""),
          {"t":c.tenant_id}).mappings().first()
        ent=db.execute(text("""SELECT e.feature_code,e.limit_value FROM saas_plan_entitlements e JOIN saas_subscriptions s ON s.plan_id=e.plan_id
          WHERE s.tenant_id=:t ORDER BY e.feature_code"""),{"t":c.tenant_id}).mappings().all()
    return {"data":None if not row else {**dict(row),"id":str(row["id"]),"entitlements":[dict(x) for x in ent]}}
@router.post("/subscription/{status}")
def transition(status:str,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    with _engine().begin() as db: transition_subscription(db,context=c,status=status.upper())
    return {"data":{"status":status.upper()}}
@router.post("/exports",status_code=202)
def export(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    with _engine().begin() as db:
        require_entitlement(db,tenant_id=c.tenant_id,feature_code="tenant.export")
        value=request_tenant_export(db,context=c)
    return {"data":{"id":str(value),"status":"REQUESTED"}}
