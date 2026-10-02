from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit, write_outbox


class CRMError(ValueError):
    pass


def _audit(db:Connection,ctx:RequestContext,action:str,target_type:str,target_id:UUID)->None:
    write_audit(db,tenant_id=ctx.tenant_id,request_id=ctx.request_id,action=action,
        actor_user_id=ctx.actor_user_id,actor_tenant_user_id=ctx.tenant_user_id,
        target_type=target_type,target_id=target_id,metadata={})


def create_partner(db:Connection,*,context:RequestContext,code:str,name:str,is_customer:bool,is_supplier:bool,
                   legal_name:str|None=None,tax_id:str|None=None,owner_tenant_user_id:UUID|None=None)->UUID:
    require_permission(context,"partner.manage")
    if not is_customer and not is_supplier: raise CRMError("partner must be customer, supplier or both")
    pid,now=uuid4(),datetime.now(UTC)
    db.execute(text("""INSERT INTO business_partners
      (id,tenant_id,code,name,legal_name,tax_id,is_customer,is_supplier,status,owner_tenant_user_id,created_at,updated_at)
      VALUES (:id,:tenant,:code,:name,:legal,:tax,:customer,:supplier,'ACTIVE',:owner,:now,:now)"""),
      {"id":pid,"tenant":context.tenant_id,"code":code,"name":name,"legal":legal_name,"tax":tax_id,
       "customer":is_customer,"supplier":is_supplier,"owner":owner_tenant_user_id,"now":now})
    _audit(db,context,"crm.partner.created","business_partner",pid)
    return pid


def add_contact(db:Connection,*,context:RequestContext,partner_id:UUID,name:str,email:str|None=None,
                phone:str|None=None,position:str|None=None,is_primary:bool=False)->UUID:
    require_permission(context,"partner.manage");cid=uuid4()
    exists=db.execute(text("SELECT 1 FROM business_partners WHERE tenant_id=:t AND id=:p AND status='ACTIVE'"),
                      {"t":context.tenant_id,"p":partner_id}).first()
    if not exists: raise CRMError("partner not found")
    if is_primary: db.execute(text("UPDATE partner_contacts SET is_primary=false WHERE tenant_id=:t AND partner_id=:p"),
                              {"t":context.tenant_id,"p":partner_id})
    db.execute(text("""INSERT INTO partner_contacts(id,tenant_id,partner_id,name,email,phone,position,is_primary,created_at)
      VALUES (:id,:t,:p,:name,:email,:phone,:position,:primary,:now)"""),
      {"id":cid,"t":context.tenant_id,"p":partner_id,"name":name,"email":email,"phone":phone,"position":position,
       "primary":is_primary,"now":datetime.now(UTC)})
    _audit(db,context,"crm.partner.contact_added","partner_contact",cid);return cid


def add_address(db:Connection,*,context:RequestContext,partner_id:UUID,address_type:str,line1:str,
                line2:str|None=None,district:str|None=None,province:str|None=None,postal_code:str|None=None,
                country_code:str="TH",is_primary:bool=False)->UUID:
    require_permission(context,"partner.manage");aid=uuid4()
    if address_type not in {"BILLING","SHIPPING","OFFICE","OTHER"}: raise CRMError("invalid address type")
    exists=db.execute(text("SELECT 1 FROM business_partners WHERE tenant_id=:t AND id=:p AND status='ACTIVE'"),
                      {"t":context.tenant_id,"p":partner_id}).first()
    if not exists: raise CRMError("partner not found")
    if is_primary: db.execute(text("UPDATE partner_addresses SET is_primary=false WHERE tenant_id=:t AND partner_id=:p AND address_type=:type"),
                              {"t":context.tenant_id,"p":partner_id,"type":address_type})
    db.execute(text("""INSERT INTO partner_addresses
      (id,tenant_id,partner_id,address_type,line1,line2,district,province,postal_code,country_code,is_primary,created_at)
      VALUES (:id,:t,:p,:type,:line1,:line2,:district,:province,:postal,:country,:primary,:now)"""),
      {"id":aid,"t":context.tenant_id,"p":partner_id,"type":address_type,"line1":line1,"line2":line2,
       "district":district,"province":province,"postal":postal_code,"country":country_code,"primary":is_primary,"now":datetime.now(UTC)})
    _audit(db,context,"crm.partner.address_added","partner_address",aid);return aid


def create_lead(db:Connection,*,context:RequestContext,lead_number:str,name:str,company_name:str|None=None,
                email:str|None=None,phone:str|None=None,owner_tenant_user_id:UUID|None=None,source:str|None=None)->UUID:
    require_permission(context,"crm.manage");lid,now=uuid4(),datetime.now(UTC)
    db.execute(text("""INSERT INTO crm_leads
      (id,tenant_id,lead_number,name,company_name,email,phone,status,owner_tenant_user_id,source,created_at,updated_at)
      VALUES (:id,:t,:number,:name,:company,:email,:phone,'OPEN',:owner,:source,:now,:now)"""),
      {"id":lid,"t":context.tenant_id,"number":lead_number,"name":name,"company":company_name,"email":email,
       "phone":phone,"owner":owner_tenant_user_id,"source":source,"now":now})
    _audit(db,context,"crm.lead.created","crm_lead",lid);return lid


def transition_lead(db:Connection,*,context:RequestContext,lead_id:UUID,status:str)->None:
    require_permission(context,"crm.manage")
    allowed={"OPEN":{"QUALIFIED","CANCELLED"},"QUALIFIED":{"WON","LOST","CANCELLED"}}
    current=db.execute(text("SELECT status FROM crm_leads WHERE tenant_id=:t AND id=:id FOR UPDATE"),
                       {"t":context.tenant_id,"id":lead_id}).scalar_one_or_none()
    if current is None: raise CRMError("lead not found")
    if status not in allowed.get(current,set()): raise CRMError("invalid lead transition")
    db.execute(text("UPDATE crm_leads SET status=:status,updated_at=:now WHERE tenant_id=:t AND id=:id"),
               {"status":status,"now":datetime.now(UTC),"t":context.tenant_id,"id":lead_id})
    _audit(db,context,"crm.lead.status_changed","crm_lead",lead_id)


def create_opportunity(db:Connection,*,context:RequestContext,opportunity_number:str,name:str,lead_id:UUID|None=None,
                       partner_id:UUID|None=None,owner_tenant_user_id:UUID|None=None,currency_code:str="THB",
                       estimated_amount:Decimal=Decimal(0),expected_close_date:date|None=None)->UUID:
    require_permission(context,"crm.manage")
    if lead_id is None and partner_id is None: raise CRMError("lead or partner required")
    if estimated_amount<0: raise CRMError("estimated amount cannot be negative")
    if lead_id and not db.execute(text("SELECT 1 FROM crm_leads WHERE tenant_id=:t AND id=:id"),{"t":context.tenant_id,"id":lead_id}).first():
        raise CRMError("lead not found")
    if partner_id and not db.execute(text("SELECT 1 FROM business_partners WHERE tenant_id=:t AND id=:id AND is_customer"),{"t":context.tenant_id,"id":partner_id}).first():
        raise CRMError("customer partner not found")
    oid,now=uuid4(),datetime.now(UTC)
    db.execute(text("""INSERT INTO crm_opportunities
      (id,tenant_id,opportunity_number,name,lead_id,partner_id,owner_tenant_user_id,status,currency_code,estimated_amount,expected_close_date,created_at,updated_at)
      VALUES (:id,:t,:number,:name,:lead,:partner,:owner,'OPEN',:currency,:amount,:close,:now,:now)"""),
      {"id":oid,"t":context.tenant_id,"number":opportunity_number,"name":name,"lead":lead_id,"partner":partner_id,
       "owner":owner_tenant_user_id,"currency":currency_code.upper(),"amount":estimated_amount,"close":expected_close_date,"now":now})
    _audit(db,context,"crm.opportunity.created","crm_opportunity",oid);return oid


def add_activity(db:Connection,*,context:RequestContext,activity_type:str,subject:str,note:str|None=None,
                 partner_id:UUID|None=None,lead_id:UUID|None=None,opportunity_id:UUID|None=None,
                 owner_tenant_user_id:UUID|None=None,occurred_at:datetime|None=None)->UUID:
    require_permission(context,"crm.manage")
    if not any((partner_id,lead_id,opportunity_id)): raise CRMError("activity target required")
    checks=(("business_partners",partner_id),("crm_leads",lead_id),("crm_opportunities",opportunity_id))
    for table,target in checks:
        if target and not db.execute(text(f"SELECT 1 FROM {table} WHERE tenant_id=:t AND id=:id"),{"t":context.tenant_id,"id":target}).first():
            raise CRMError("activity target not found")
    aid=uuid4();now=datetime.now(UTC)
    db.execute(text("""INSERT INTO crm_activities
      (id,tenant_id,partner_id,lead_id,opportunity_id,activity_type,subject,note,owner_tenant_user_id,occurred_at,created_at)
      VALUES (:id,:t,:partner,:lead,:opp,:type,:subject,:note,:owner,:occurred,:now)"""),
      {"id":aid,"t":context.tenant_id,"partner":partner_id,"lead":lead_id,"opp":opportunity_id,
       "type":activity_type,"subject":subject,"note":note,"owner":owner_tenant_user_id,"occurred":occurred_at or now,"now":now})
    _audit(db,context,"crm.activity.created","crm_activity",aid)
    write_outbox(db,tenant_id=context.tenant_id,event_type="crm.activity.created",aggregate_type="crm_activity",
                 aggregate_id=aid,payload={"activity_type":activity_type})
    return aid
