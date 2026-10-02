"""Provision the temporary passwordless NOMOS demo administrator."""
from datetime import UTC, datetime
from uuid import UUID, uuid4
from sqlalchemy import create_engine, text
from app.core.config import get_settings

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
EMAIL = "admin@demo.nomos.local"

def main() -> None:
    engine=create_engine(get_settings().database_url,pool_pre_ping=True); now=datetime.now(UTC)
    with engine.begin() as db:
        db.execute(text("""INSERT INTO tenants(id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at)
        VALUES(:id,'nomos-demo','NOMOS Demo','ACTIVE','th','Asia/Bangkok','THB',:now,:now)
        ON CONFLICT (id) DO UPDATE SET status='ACTIVE',updated_at=:now"""),{"id":TENANT_ID,"now":now})
        user=db.execute(text("SELECT id FROM users WHERE lower(email)=lower(:e)"),{"e":EMAIL}).scalar_one_or_none()
        if user is None:
            user=uuid4()
            db.execute(text("""INSERT INTO users(id,email,password_hash,display_name,status,locale,created_at,updated_at)
            VALUES(:id,:e,'disabled','Demo Administrator','ACTIVE','th',:now,:now)"""),{"id":user,"e":EMAIL,"now":now})
        tu=db.execute(text("SELECT id FROM tenant_users WHERE tenant_id=:t AND user_id=:u"),{"t":TENANT_ID,"u":user}).scalar_one_or_none()
        if tu is None:
            tu=uuid4(); db.execute(text("""INSERT INTO tenant_users(id,tenant_id,user_id,status,joined_at,created_at,updated_at)
            VALUES(:id,:t,:u,'ACTIVE',:now,:now,:now)"""),{"id":tu,"t":TENANT_ID,"u":user,"now":now})
        role=db.execute(text("SELECT id FROM roles WHERE tenant_id=:t AND code='ADMIN'"),{"t":TENANT_ID}).scalar_one_or_none()
        if role is None:
            role=uuid4(); db.execute(text("""INSERT INTO roles(id,tenant_id,code,name,description,is_system,status,created_at,updated_at)
            VALUES(:id,:t,'ADMIN','Administrator','Temporary demo administrator',true,'ACTIVE',:now,:now)"""),{"id":role,"t":TENANT_ID,"now":now})
        db.execute(text("""INSERT INTO tenant_user_roles(tenant_id,tenant_user_id,role_id,created_at)
        SELECT :t,:tu,:r,:now WHERE NOT EXISTS(SELECT 1 FROM tenant_user_roles WHERE tenant_id=:t AND tenant_user_id=:tu AND role_id=:r)"""),{"t":TENANT_ID,"tu":tu,"r":role,"now":now})
        db.execute(text("""INSERT INTO role_permissions(tenant_id,role_id,permission_id,created_at)
        SELECT :t,:r,p.id,:now FROM permissions p WHERE NOT EXISTS
        (SELECT 1 FROM role_permissions rp WHERE rp.tenant_id=:t AND rp.role_id=:r AND rp.permission_id=p.id)"""),{"t":TENANT_ID,"r":role,"now":now})
        entity=db.execute(text("SELECT id FROM legal_entities WHERE tenant_id=:t AND code='DEMO'"),{"t":TENANT_ID}).scalar_one_or_none()
        if entity is None:
            entity=uuid4(); db.execute(text("""INSERT INTO legal_entities(id,tenant_id,code,legal_name,country_code,base_currency,timezone,status,created_at,updated_at)
            VALUES(:id,:t,'DEMO','NOMOS Demo Co.','TH','THB','Asia/Bangkok','ACTIVE',:now,:now)"""),{"id":entity,"t":TENANT_ID,"now":now})
        unit=db.execute(text("SELECT id FROM units WHERE tenant_id=:t AND code='EA'"),{"t":TENANT_ID}).scalar_one_or_none()
        if unit is None:
            unit=uuid4(); db.execute(text("""INSERT INTO units(id,tenant_id,code,name,symbol,precision,status,created_at,updated_at)
            VALUES(:id,:t,'EA','Each','ea',0,'ACTIVE',:now,:now)"""),{"id":unit,"t":TENANT_ID,"now":now})
        warehouse=db.execute(text("SELECT id FROM warehouses WHERE tenant_id=:t AND code='DEMO-WH'"),{"t":TENANT_ID}).scalar_one_or_none()
        if warehouse is None:
            warehouse=uuid4(); db.execute(text("""INSERT INTO warehouses(id,tenant_id,legal_entity_id,branch_id,code,name,status,created_at,updated_at)
            VALUES(:id,:t,:e,NULL,'DEMO-WH','Demo Warehouse','ACTIVE',:now,:now)"""),{"id":warehouse,"t":TENANT_ID,"e":entity,"now":now})
        location=db.execute(text("SELECT id FROM warehouse_locations WHERE tenant_id=:t AND warehouse_id=:w AND code='MAIN'"),{"t":TENANT_ID,"w":warehouse}).scalar_one_or_none()
        if location is None:
            location=uuid4(); db.execute(text("""INSERT INTO warehouse_locations(id,tenant_id,warehouse_id,parent_id,code,name,location_type,allow_stock,status,created_at,updated_at)
            VALUES(:id,:t,:w,NULL,'MAIN','Main Storage','STORAGE',true,'ACTIVE',:now,:now)"""),{"id":location,"t":TENANT_ID,"w":warehouse,"now":now})
        product=db.execute(text("SELECT id FROM products WHERE tenant_id=:t AND sku='DEMO-E2E'"),{"t":TENANT_ID}).scalar_one_or_none()
        if product is None:
            product=uuid4(); db.execute(text("""INSERT INTO products(id,tenant_id,sku,name,product_type,base_unit_id,category_id,tracking_type,description,status,archived_at,created_at,updated_at)
            VALUES(:id,:t,'DEMO-E2E','Demo E2E Stock Item','STOCK',:u,NULL,'NONE','Browser acceptance fixture','ACTIVE',NULL,:now,:now)"""),{"id":product,"t":TENANT_ID,"u":unit,"now":now})
        n=db.execute(text("SELECT count(*) FROM role_permissions WHERE tenant_id=:t AND role_id=:r"),{"t":TENANT_ID,"r":role}).scalar_one()
    print(f"TENANT_ID={TENANT_ID} EMAIL={EMAIL} PERMISSIONS={n}")
if __name__=="__main__": main()
