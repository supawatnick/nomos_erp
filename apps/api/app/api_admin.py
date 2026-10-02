from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import create_engine, text

from app.application.auth import resolve_session
from app.core.config import get_settings
from app.domain.security import RequestContext, require_permission

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _context(request: Request, authorization: str | None, tenant: str | None) -> RequestContext:
    if not authorization or not authorization.startswith("Bearer ") or not tenant:
        raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"})
    try:
        tenant_id = UUID(tenant)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"}) from exc
    return resolve_session(authorization.removeprefix("Bearer ").strip(), tenant_id, request.state.request_id)


@router.get("/users")
def users(request: Request, authorization: str | None = Header(default=None),
          x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")) -> dict[str, object]:
    context = _context(request, authorization, x_tenant_id)
    require_permission(context, "user.read")
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.connect() as db:
        rows = db.execute(text("""
            SELECT tu.id,u.id user_id,u.email,u.display_name,u.status user_status,tu.status membership_status,
                   tu.employee_code,COALESCE(array_agg(r.code ORDER BY r.code) FILTER (WHERE r.code IS NOT NULL),'{}') roles
            FROM tenant_users tu JOIN users u ON u.id=tu.user_id
            LEFT JOIN tenant_user_roles tur ON tur.tenant_id=tu.tenant_id AND tur.tenant_user_id=tu.id
            LEFT JOIN roles r ON r.tenant_id=tur.tenant_id AND r.id=tur.role_id
            WHERE tu.tenant_id=:tenant
            GROUP BY tu.id,u.id,u.email,u.display_name,u.status,tu.status,tu.employee_code
            ORDER BY u.display_name,u.email
        """), {"tenant": context.tenant_id}).mappings().all()
    data=[{**dict(x),"id":str(x["id"]),"user_id":str(x["user_id"])} for x in rows]
    return {"data":data,"meta":{"request_id":str(context.request_id)}}


@router.get("/roles")
def roles(request: Request, authorization: str | None = Header(default=None),
          x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")) -> dict[str, object]:
    context = _context(request, authorization, x_tenant_id)
    require_permission(context, "role.read")
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with engine.connect() as db:
        rows=db.execute(text("""
            SELECT r.id,r.code,r.name,r.description,r.status,r.is_system,
                   COALESCE(array_agg(p.code ORDER BY p.code) FILTER (WHERE p.code IS NOT NULL),'{}') permissions
            FROM roles r LEFT JOIN role_permissions rp ON rp.tenant_id=r.tenant_id AND rp.role_id=r.id
            LEFT JOIN permissions p ON p.id=rp.permission_id
            WHERE r.tenant_id=:tenant GROUP BY r.id ORDER BY r.code
        """),{"tenant":context.tenant_id}).mappings().all()
    data=[{**dict(x),"id":str(x["id"])} for x in rows]
    return {"data":data,"meta":{"request_id":str(context.request_id)}}


@router.get("/audit")
def audit(request: Request, authorization: str | None = Header(default=None),
          x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")) -> dict[str, object]:
    context = _context(request, authorization, x_tenant_id)
    require_permission(context, "audit.read")
    engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    with engine.connect() as db:
        rows=db.execute(text("""
            SELECT id,occurred_at,actor_user_id,action,target_type,target_id,channel,request_id,result,metadata
            FROM audit_logs WHERE tenant_id=:tenant ORDER BY occurred_at DESC,id DESC LIMIT 200
        """),{"tenant":context.tenant_id}).mappings().all()
    data=[]
    for row in rows:
        d=dict(row)
        for k in ("id","actor_user_id","target_id","request_id"):
            d[k]=str(d[k]) if d[k] else None
        d["occurred_at"]=d["occurred_at"].isoformat()
        data.append(d)
    return {"data":data,"meta":{"request_id":str(context.request_id)}}
