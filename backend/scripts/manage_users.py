"""
Create or update a user in a specific tenant.

Usage:
    python scripts/manage_users.py --tenant <slug> --email <email> [options]

Examples:
    python scripts/manage_users.py --tenant acme --email john@acme.com --password Secret123 --admin 1 --team "Main Office"
    python scripts/manage_users.py --tenant acme --email john@acme.com --team "Sales"

Writes to both:
  - master.db: GlobalUser (auth identity, email + password)
  - tenant DB:  local User (caller, admin flag, team info)

Password is only updated when --password is explicitly passed.
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import models.account   # noqa: F401 — register all models so SQLAlchemy resolves relationships
import models.alarm     # noqa: F401
import models.call      # noqa: F401
import models.caller    # noqa: F401
import models.company   # noqa: F401
import models.customer  # noqa: F401
import models.invoice   # noqa: F401
import models.product   # noqa: F401
import models.product_customer  # noqa: F401
import models.tag       # noqa: F401

from getpass import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.master import GlobalUser, MasterBase, Tenant, UserTenant
from models.user import User
from models.team import Team
from core.database import MASTER_DATABASE_URL


def get_master_db() -> Session:
    args = {"check_same_thread": False} if MASTER_DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(MASTER_DATABASE_URL, connect_args=args)
    MasterBase.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def get_tenant_db(tenant: Tenant) -> Session:
    args = {"check_same_thread": False} if tenant.db_url.startswith("sqlite") else {}
    engine = create_engine(tenant.db_url, connect_args=args)
    return sessionmaker(bind=engine)()


def manage_user(tenant_slug: str, email: str, password: str | None, admin: int, team_name: str | None):
    master_db = get_master_db()

    tenant = master_db.query(Tenant).filter_by(slug=tenant_slug, active=True).first()
    if not tenant:
        print(f"❌ Tenant '{tenant_slug}' not found or inactive.")
        master_db.close()
        sys.exit(1)

    tenant_db = get_tenant_db(tenant)

    try:
        # --- GlobalUser (master DB) ---
        global_user = master_db.query(GlobalUser).filter_by(email=email).first()
        if not global_user:
            if not password:
                password = getpass("Password (new user): ")
            global_user = GlobalUser(email=email)
            global_user.set_password(password)
            master_db.add(global_user)
            master_db.flush()
            print(f"  Created GlobalUser '{email}'")
        else:
            if password:
                global_user.set_password(password)
                print(f"  Updated password for '{email}'")

        # Ensure linked to this tenant
        link = master_db.query(UserTenant).filter_by(
            global_user_id=global_user.id, tenant_id=tenant.id
        ).first()
        if not link:
            master_db.add(UserTenant(global_user_id=global_user.id, tenant_id=tenant.id))
            print(f"  Linked '{email}' to tenant '{tenant_slug}'")

        master_db.commit()

        # --- Local User (tenant DB) ---
        caller = None
        if team_name:
            caller = tenant_db.query(Team).filter_by(name=team_name).first()
            if not caller:
                caller = Team(name=team_name)
                tenant_db.add(caller)
                tenant_db.flush()
                print(f"  Created team '{team_name}'")

        local_user = tenant_db.query(User).filter_by(global_user_id=global_user.id).first()
        if local_user:
            local_user.admin = admin
            if caller is not None:
                local_user.team = caller
            print(f"  Updated local user in '{tenant_slug}' (admin={admin})")
        else:
            local_user = User(
                username=email,
                admin=admin,
                global_user_id=global_user.id,
                team=caller,
            )
            tenant_db.add(local_user)
            print(f"  Created local user in '{tenant_slug}' (admin={admin})")

        tenant_db.commit()

    except Exception as e:
        master_db.rollback()
        tenant_db.rollback()
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        master_db.close()
        tenant_db.close()

    print(f"\n✅ Done. User '{email}' is ready in tenant '{tenant_slug}'.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create or update a user in a tenant.")
    parser.add_argument("--tenant", required=True, help="Tenant slug, e.g. acme")
    parser.add_argument("--email", required=True, help="Email address (globally unique login identity)")
    parser.add_argument("--password", default=None, help="Password (prompted if omitted for new users)")
    parser.add_argument("--admin", type=int, default=0, help="Admin flag: 0=normal, 1=admin")
    parser.add_argument("--team", default=None, help="Team/caller name (optional)")

    args = parser.parse_args()
    manage_user(args.tenant, args.email, args.password, args.admin, args.caller)
