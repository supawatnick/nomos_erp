from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.api_master import trusted_context
from app.application.crm import (
    CRMError,
    add_activity,
    add_address,
    add_contact,
    archive_partner,
    create_lead,
    create_opportunity,
    create_partner,
    transition_lead,
    update_partner,
)
from app.core.config import get_settings
from app.domain.security import require_permission

router=APIRouter(prefix="/api/v1",tags=["partners-crm"])

class PartnerIn(BaseModel):
    code:str=Field(min_length=1,max_length=64);name:str=Field(min_length=1,max_length=240)
    legal_name:str|None=None;tax_id:str|None=None;is_customer:bool=False;is_supplier:bool=False;owner_tenant_user_id:UUID|None=None
class ContactIn(BaseModel):
    name:str;email:str|None=None;phone:str|None=None;position:str|None=None;is_primary:bool=False
class AddressIn(BaseModel):
    address_type:str;line1:str;line2:str|None=None;district:str|None=None;province:str|None=None;postal_code:str|None=None;country_code:str="TH";is_primary:bool=False
class LeadIn(BaseModel):
    lead_number:str;name:str;company_name:str|None=None;email:str|None=None;phone:str|None=None;owner_tenant_user_id:UUID|None=None;source:str|None=None
class OpportunityIn(BaseModel):
    opportunity_number:str;name:str;lead_id:UUID|None=None;partner_id:UUID|None=None;owner_tenant_user_id:UUID|None=None
    currency_code:str="THB";estimated_amount:Decimal=Decimal(0);expected_close_date:date|None=None
class ActivityIn(BaseModel):
    activity_type:str;subject:str;note:str|None=None;partner_id:UUID|None=None;lead_id:UUID|None=None;opportunity_id:UUID|None=None;owner_tenant_user_id:UUID|None=None

def _ctx(request:Request,authorization:str|None,tenant:str|None):
    return trusted_context(request,authorization,tenant)
def _engine(): return create_engine(get_settings().database_url,pool_pre_ping=True)
def _serialize(rows):
    out=[]
    for row in rows:
        d=dict(row)
        for k,v in list(d.items()):
            if isinstance(v,UUID): d[k]=str(v)
            elif hasattr(v,"isoformat") and v is not None: d[k]=v.isoformat()
            elif isinstance(v,Decimal): d[k]=format(v,"f")
        out.append(d)
    return out

@router.get("/partners")
def partners(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id);require_permission(c,"partner.read")
    with _engine().connect() as db: rows=db.execute(text("SELECT id,code,name,legal_name,tax_id,is_customer,is_supplier,status,owner_tenant_user_id,updated_at FROM business_partners WHERE tenant_id=:t ORDER BY code"),{"t":c.tenant_id}).mappings().all()
    return {"data":_serialize(rows),"meta":{"request_id":str(c.request_id)}}

@router.post("/partners",status_code=201)
def partner_create(payload:PartnerIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db: pid=create_partner(db,context=c,**payload.model_dump())
    except IntegrityError as exc: raise HTTPException(409,detail={"code":"DUPLICATE_RESOURCE"}) from exc
    except CRMError as exc: raise HTTPException(409,detail={"code":"VALIDATION_FAILED","message":str(exc)}) from exc
    return {"data":{"id":str(pid)},"meta":{"request_id":str(c.request_id)}}


@router.put("/partners/{partner_id}")
def partner_update(partner_id:UUID,payload:PartnerIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db: changed=update_partner(db,context=c,partner_id=partner_id,**payload.model_dump())
    except IntegrityError as exc: raise HTTPException(409,detail={"code":"DUPLICATE_RESOURCE"}) from exc
    except CRMError as exc: raise HTTPException(409,detail={"code":"VALIDATION_FAILED","message":str(exc)}) from exc
    if not changed: raise HTTPException(404,detail={"code":"RESOURCE_NOT_FOUND"})
    return {"data":{"id":str(partner_id)}}


@router.post("/partners/{partner_id}/archive")
def partner_archive(partner_id:UUID,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    with _engine().begin() as db: changed=archive_partner(db,context=c,partner_id=partner_id)
    if not changed: raise HTTPException(404,detail={"code":"RESOURCE_NOT_FOUND"})
    return {"data":{"id":str(partner_id),"status":"ARCHIVED"}}


@router.get("/partners/{partner_id}")
def partner_detail(partner_id:UUID,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id);require_permission(c,"partner.read")
    with _engine().connect() as db:
        head=db.execute(text("SELECT * FROM business_partners WHERE tenant_id=:t AND id=:id"),{"t":c.tenant_id,"id":partner_id}).mappings().first()
        if not head: raise HTTPException(404,detail={"code":"RESOURCE_NOT_FOUND"})
        contacts=db.execute(text("SELECT * FROM partner_contacts WHERE tenant_id=:t AND partner_id=:id ORDER BY is_primary DESC,name"),{"t":c.tenant_id,"id":partner_id}).mappings().all()
        addresses=db.execute(text("SELECT * FROM partner_addresses WHERE tenant_id=:t AND partner_id=:id ORDER BY is_primary DESC,address_type"),{"t":c.tenant_id,"id":partner_id}).mappings().all()
        activities=db.execute(text("SELECT * FROM crm_activities WHERE tenant_id=:t AND partner_id=:id ORDER BY occurred_at DESC"),{"t":c.tenant_id,"id":partner_id}).mappings().all()
    data=_serialize([head])[0];data["contacts"]=_serialize(contacts);data["addresses"]=_serialize(addresses);data["activities"]=_serialize(activities)
    return {"data":data,"meta":{"request_id":str(c.request_id)}}

@router.post("/partners/{partner_id}/contacts",status_code=201)
def contact_create(partner_id:UUID,payload:ContactIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db: rid=add_contact(db,context=c,partner_id=partner_id,**payload.model_dump())
    except CRMError as exc: raise HTTPException(404,detail={"code":"RESOURCE_NOT_FOUND","message":str(exc)}) from exc
    return {"data":{"id":str(rid)}}

@router.post("/partners/{partner_id}/addresses",status_code=201)
def address_create(partner_id:UUID,payload:AddressIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db: rid=add_address(db,context=c,partner_id=partner_id,**payload.model_dump())
    except CRMError as exc: raise HTTPException(409,detail={"code":"VALIDATION_FAILED","message":str(exc)}) from exc
    return {"data":{"id":str(rid)}}

@router.get("/crm/leads")
def leads(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id);require_permission(c,"crm.read")
    with _engine().connect() as db: rows=db.execute(text("SELECT id,lead_number,name,company_name,email,phone,status,partner_id,owner_tenant_user_id,source,updated_at FROM crm_leads WHERE tenant_id=:t ORDER BY updated_at DESC"),{"t":c.tenant_id}).mappings().all()
    return {"data":_serialize(rows),"meta":{"request_id":str(c.request_id)}}

@router.post("/crm/leads",status_code=201)
def lead_create(payload:LeadIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db: rid=create_lead(db,context=c,**payload.model_dump())
    except IntegrityError as exc: raise HTTPException(409,detail={"code":"DUPLICATE_RESOURCE"}) from exc
    return {"data":{"id":str(rid)}}

@router.post("/crm/leads/{lead_id}/transition/{new_status}")
def lead_transition(lead_id:UUID,new_status:str,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db: transition_lead(db,context=c,lead_id=lead_id,status=new_status.upper())
    except CRMError as exc: raise HTTPException(409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(lead_id),"status":new_status.upper()}}

@router.get("/crm/opportunities")
def opportunities(request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id);require_permission(c,"crm.read")
    with _engine().connect() as db: rows=db.execute(text("SELECT id,opportunity_number,name,lead_id,partner_id,owner_tenant_user_id,status,currency_code,estimated_amount,expected_close_date,updated_at FROM crm_opportunities WHERE tenant_id=:t ORDER BY updated_at DESC"),{"t":c.tenant_id}).mappings().all()
    return {"data":_serialize(rows),"meta":{"request_id":str(c.request_id)}}

@router.post("/crm/opportunities",status_code=201)
def opportunity_create(payload:OpportunityIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db: rid=create_opportunity(db,context=c,**payload.model_dump())
    except (CRMError,IntegrityError) as exc: raise HTTPException(409,detail={"code":"VALIDATION_FAILED","message":str(exc)}) from exc
    return {"data":{"id":str(rid)}}

@router.post("/crm/activities",status_code=201)
def activity_create(payload:ActivityIn,request:Request,authorization:str|None=Header(default=None),x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID")):
    c=_ctx(request,authorization,x_tenant_id)
    try:
        with _engine().begin() as db: rid=add_activity(db,context=c,**payload.model_dump())
    except CRMError as exc: raise HTTPException(409,detail={"code":"VALIDATION_FAILED","message":str(exc)}) from exc
    return {"data":{"id":str(rid)}}
