"""
Create a new tenant and its database.

Usage:
    python scripts/create_tenant.py <slug> "<Display Name>" [--db-dir /dbdata]

Example:
    python scripts/create_tenant.py acme "Acme Corp"
    python scripts/create_tenant.py globex "Globex Inc" --db-dir /mnt/dbdata

Steps performed:
    1. Create the tenant SQLite DB file
    2. Run all Alembic migrations against it
    3. Register the tenant in master.db (Tenant row)
    4. Optionally create an admin GlobalUser and link to tenant

Run from the backend/ directory with MASTER_DATABASE_URL set.
"""

import argparse
import os
import sys

# Make sure backend/ is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

MASTER_DATABASE_URL = os.environ.get("MASTER_DATABASE_URL")
if not MASTER_DATABASE_URL:
    print("❌ MASTER_DATABASE_URL env var is required.")
    sys.exit(1)


def get_master_session():
    args = {"check_same_thread": False} if MASTER_DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(MASTER_DATABASE_URL, connect_args=args)
    return sessionmaker(bind=engine)()


def create_tenant(slug: str, name: str, db_dir: str = "/dbdata"):
    from models.master import GlobalUser, MasterBase, Tenant, UserTenant

    db_path = os.path.join(db_dir, f"{slug}.db")
    db_url = f"sqlite:///{db_path}"

    # 1. Ensure DB directory exists
    os.makedirs(db_dir, exist_ok=True)

    # Import all models so SQLAlchemy can resolve relationship strings (e.g. "Team")
    import models.account  
    import models.alarm  
    import models.team  
    import models.call  
    import models.company  
    import models.customer  
    import models.invoice  
    import models.product  
    import models.product_customer 
    import models.tag  
    from models.user import User
    from core.models.base import Base

    # 2. Create all tables in the new tenant DB directly (no alembic subprocess needed for new DBs)
    print(f"Creating schema for {slug}...")
    tenant_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=tenant_engine)
    print(f"  Schema ready.")

    # 3. Register in master DB
    master_db = get_master_session()
    master_engine = master_db.bind

    # Ensure master tables exist
    MasterBase.metadata.create_all(bind=master_engine)

    existing = master_db.query(Tenant).filter_by(slug=slug).first()
    if existing:
        print(f"⚠️  Tenant '{slug}' already exists in master DB — skipping registration.")
        master_db.close()
        return

    tenant = Tenant(slug=slug, name=name, db_url=db_url)
    master_db.add(tenant)
    master_db.commit()
    master_db.refresh(tenant)
    print(f"✅ Tenant '{name}' registered (id={tenant.id}, db={db_path})")

    # 4. Optionally create an admin user for this tenant
    answer = input("Create an admin user for this tenant? [y/N] ").strip().lower()
    if answer == "y":
        email = input("Email: ").strip()
        password = input("Password: ").strip()

        global_user = master_db.query(GlobalUser).filter_by(email=email).first()
        if not global_user:
            global_user = GlobalUser(email=email)
            global_user.set_password(password)
            master_db.add(global_user)
            master_db.flush()
            print(f"  Created GlobalUser '{email}'")
        else:
            print(f"  GlobalUser '{email}' already exists — reusing.")

        link = master_db.query(UserTenant).filter_by(
            global_user_id=global_user.id, tenant_id=tenant.id
        ).first()
        if not link:
            master_db.add(UserTenant(global_user_id=global_user.id, tenant_id=tenant.id))

        master_db.commit()

        # Create local User in tenant DB
        from models.team import Team
        tenant_db = sessionmaker(bind=tenant_engine)()
        default_team = tenant_db.query(Team).filter_by(name="Admin").first()
        if not default_team:
            default_team = Team(name="Admin")
            tenant_db.add(default_team)
            tenant_db.flush()
        local = tenant_db.query(User).filter_by(global_user_id=global_user.id).first()
        if not local:
            tenant_db.add(User(username=email, admin=1, global_user_id=global_user.id,
                               team_id=default_team.id))
            tenant_db.commit()
        elif local.team_id is None:
            local.team_id = default_team.id
            tenant_db.commit()
        tenant_db.close()
        print(f"  Local admin user created in {slug}.db")

    master_db.close()
    print(f"\nDone. Tenant '{slug}' is ready.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new tenant")
    parser.add_argument("slug", help="URL-safe identifier, e.g. acme")
    parser.add_argument("name", help='Display name, e.g. "Acme Corp"')
    args = parser.parse_args()

    if not args.slug.isidentifier():
        print("❌ Slug must be a valid identifier (letters, digits, underscores).")
        sys.exit(1)

    create_tenant(args.slug, args.name, "/dbdata")
