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
        n=db.execute(text("SELECT count(*) FROM role_permissions WHERE tenant_id=:t AND role_id=:r"),{"t":TENANT_ID,"r":role}).scalar_one()
    print(f"TENANT_ID={TENANT_ID} EMAIL={EMAIL} PERMISSIONS={n}")
if __name__=="__main__": main()
