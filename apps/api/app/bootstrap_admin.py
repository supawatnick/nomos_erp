"""Idempotent first-tenant/demo administrator bootstrap."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from secrets import token_bytes
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.domain.security import hash_password


def bootstrap_admin(*, email: str, password: str, tenant_slug: str, tenant_name: str) -> tuple[str, str]:
    if len(password) < 12:
        raise ValueError("password must be at least 12 characters")
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    now = datetime.now(UTC)
    with engine.begin() as db:
        tenant = db.execute(text("SELECT id FROM tenants WHERE slug=:slug"), {"slug": tenant_slug}).scalar_one_or_none()
        if tenant is None:
            tenant = uuid4()
            db.execute(text("""INSERT INTO tenants
                (id,slug,name,status,default_locale,default_timezone,base_currency,created_at,updated_at)
                VALUES (:id,:slug,:name,'ACTIVE','th','Asia/Bangkok','THB',:now,:now)"""),
                {"id": tenant, "slug": tenant_slug, "name": tenant_name, "now": now})
        user = db.execute(text("SELECT id FROM users WHERE lower(email)=lower(:email)"), {"email": email}).scalar_one_or_none()
        encoded = hash_password(password, token_bytes(16))
        if user is None:
            user = uuid4()
            db.execute(text("""INSERT INTO users
                (id,email,password_hash,display_name,status,locale,created_at,updated_at)
                VALUES (:id,:email,:password,'Demo Administrator','ACTIVE','th',:now,:now)"""),
                {"id": user, "email": email, "password": encoded, "now": now})
        else:
            db.execute(text("UPDATE users SET password_hash=:password,status='ACTIVE',updated_at=:now WHERE id=:id"),
                       {"password": encoded, "now": now, "id": user})
        tenant_user = db.execute(text("SELECT id FROM tenant_users WHERE tenant_id=:tenant AND user_id=:user"),
                                 {"tenant": tenant, "user": user}).scalar_one_or_none()
        if tenant_user is None:
            tenant_user = uuid4()
            db.execute(text("""INSERT INTO tenant_users
                (id,tenant_id,user_id,status,joined_at,created_at,updated_at)
                VALUES (:id,:tenant,:user,'ACTIVE',:now,:now,:now)"""),
                {"id": tenant_user, "tenant": tenant, "user": user, "now": now})
        role = db.execute(text("SELECT id FROM roles WHERE tenant_id=:tenant AND code='ADMIN'"), {"tenant": tenant}).scalar_one_or_none()
        if role is None:
            role = uuid4()
            db.execute(text("""INSERT INTO roles
                (id,tenant_id,code,name,description,is_system,status,created_at,updated_at)
                VALUES (:id,:tenant,'ADMIN','Administrator','Full tenant administrator',true,'ACTIVE',:now,:now)"""),
                {"id": role, "tenant": tenant, "now": now})
        db.execute(text("""INSERT INTO tenant_user_roles(tenant_id,tenant_user_id,role_id,created_at)
            SELECT :tenant,:tu,:role,:now WHERE NOT EXISTS
            (SELECT 1 FROM tenant_user_roles WHERE tenant_id=:tenant AND tenant_user_id=:tu AND role_id=:role)"""),
            {"tenant": tenant, "tu": tenant_user, "role": role, "now": now})
        db.execute(text("""INSERT INTO role_permissions(tenant_id,role_id,permission_id,created_at)
            SELECT :tenant,:role,p.id,:now FROM permissions p
            WHERE NOT EXISTS (SELECT 1 FROM role_permissions rp
              WHERE rp.tenant_id=:tenant AND rp.role_id=:role AND rp.permission_id=p.id)"""),
            {"tenant": tenant, "role": role, "now": now})
    engine.dispose()
    return str(tenant), password


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password")
    parser.add_argument("--tenant-slug", default="nomos-demo")
    parser.add_argument("--tenant-name", default="NOMOS Demo")
    args = parser.parse_args()
    tenant_id = bootstrap_admin(email=args.email, password=args.password, tenant_slug=args.tenant_slug, tenant_name=args.tenant_name)
    print(tenant_id)


if __name__ == "__main__":
    main()
