"""
Seed the demo tenants with realistic demo data.

The records themselves live in scripts/demo_data.py; this file only turns them
into rows. Two tenants are seeded:

- "default"   Nordljus Media AB   — the tenant behind the landing page login
- "fjallvind" Fjällvind Event AB  — a second, smaller tenant (SQLite only)

Usage (inside the container, from backend/):

    python scripts/generate_test_data.py            # seed if not already seeded
    python scripts/generate_test_data.py --reset    # wipe the demo tenants and seed again

On application startup seed_test_data() runs without reset: it seeds an empty
database and never touches one that already holds customers.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from core.config import ADMIN_EMAIL
from core.database import DATABASE_URL, MasterSession, SessionLocal
from core.models.base import Base
from data.constants import CMS_CONFIG_KEY, DEFAULT_TZ
from models.account import Account
from models.alarm import Alarm
from models.call import Call
from models.company import Company
from models.config import TenantConfig
from models.customer import Customer
from models.invoice import Invoice, InvoiceNumber
from models.master import GlobalUser, LoginToken, Tenant, UserTenant
from models.product import Product
from models.product_customer import ProductCustomer
from models.tag import Tag, TagLink
from models.team import Team
from models.user import User
from scripts import demo_data

SEED_MARKER_KEY = "demo_seed"
SEED_VERSION = 2

# Deleted in this order on reset (children before parents).
DATA_MODELS = [TagLink, Tag, Alarm, Call, ProductCustomer, Invoice, InvoiceNumber,
               Company, Customer, Product]


def _when(days: int, hour: int = 12, minute: int = 0) -> datetime:
    """Local wall-clock time `days` from today, as the naive UTC the app stores."""
    local_now = datetime.now(ZoneInfo(DEFAULT_TZ))
    local = (local_now + timedelta(days=days)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def _tenant_db_url(slug: str) -> str | None:
    """DB url for a demo tenant. Extra tenants get a SQLite file next to the default one."""
    if slug == "default":
        return DATABASE_URL
    if not DATABASE_URL.startswith("sqlite"):
        return None
    return DATABASE_URL.rsplit("/", 1)[0] + f"/{slug}.db"


def _open_tenant_db(db_url: str) -> Session:
    if db_url == DATABASE_URL:
        return SessionLocal()
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def _is_seeded(tenant_db: Session) -> bool:
    return tenant_db.query(TenantConfig).filter_by(key=SEED_MARKER_KEY).first() is not None


def _set_config(tenant_db: Session, key: str, value: dict) -> None:
    payload = json.dumps(value, ensure_ascii=False)
    row = tenant_db.query(TenantConfig).filter_by(key=key).first()
    if row:
        row.value = payload
    else:
        tenant_db.add(TenantConfig(key=key, value=payload))


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def _reset_tenant(tenant_db: Session, master_db: Session, tenant: Tenant | None, removed_emails: set[str]) -> None:
    """Remove all business records plus the demo users and teams from one tenant DB.

    Kept: the "Admin" team, the CMS config row, and any local user that still has
    a real login for this tenant (those are moved to the Admin team).
    """
    for model in DATA_MODELS:
        tenant_db.query(model).delete(synchronize_session=False)

    admin_team = tenant_db.query(Team).filter_by(name="Admin").first()
    if not admin_team:
        admin_team = Team(name="Admin")
        tenant_db.add(admin_team)
        tenant_db.flush()

    for user in tenant_db.query(User).all():
        global_user = master_db.query(GlobalUser).filter_by(id=user.global_user_id).first()
        linked = bool(
            global_user and tenant and master_db.query(UserTenant).filter_by(
                global_user_id=global_user.id, tenant_id=tenant.id
            ).first()
        )
        if not linked or global_user.email in removed_emails:
            tenant_db.delete(user)
        else:
            user.team_id = admin_team.id
    tenant_db.flush()

    tenant_db.query(Team).filter(Team.id != admin_team.id).delete(synchronize_session=False)
    tenant_db.query(Account).delete(synchronize_session=False)
    tenant_db.query(TenantConfig).filter_by(key=SEED_MARKER_KEY).delete(synchronize_session=False)

    if tenant_db.bind.dialect.name == "sqlite":
        # Restart ids (and thereby invoice numbers) from 1.
        has_sequence = tenant_db.execute(
            text("SELECT name FROM sqlite_master WHERE name = 'sqlite_sequence'")
        ).first()
        if has_sequence:
            tenant_db.execute(text("DELETE FROM sqlite_sequence"))
    tenant_db.commit()


def reset_demo_data() -> None:
    """Wipe the demo tenants and remove demo logins (current and legacy)."""
    master_db = MasterSession()
    try:
        removed_emails = set(demo_data.demo_emails()) | set(demo_data.LEGACY_EMAILS)
        removed_emails.discard(ADMIN_EMAIL)

        for spec in demo_data.TENANTS:
            tenant = master_db.query(Tenant).filter_by(slug=spec["slug"]).first()
            if not tenant and spec["slug"] != "default":
                continue  # extra tenant not created yet — nothing to clear
            db_url = tenant.db_url if tenant else DATABASE_URL
            tenant_db = _open_tenant_db(db_url)
            try:
                _reset_tenant(tenant_db, master_db, tenant, removed_emails)
                print(f"🧹 Cleared tenant '{spec['slug']}'")
            finally:
                tenant_db.close()

        for global_user in master_db.query(GlobalUser).filter(GlobalUser.email.in_(removed_emails)).all():
            master_db.query(UserTenant).filter_by(global_user_id=global_user.id).delete()
            master_db.query(LoginToken).filter_by(global_user_id=global_user.id).delete()
            master_db.delete(global_user)
        master_db.commit()
    finally:
        master_db.close()


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def _ensure_tenant(master_db: Session, spec: dict, db_url: str) -> Tenant:
    tenant = master_db.query(Tenant).filter_by(slug=spec["slug"]).first()
    if not tenant:
        tenant = Tenant(slug=spec["slug"], db_url=db_url)
        master_db.add(tenant)
    tenant.name = spec["name"]
    tenant.active = True
    tenant.require_2fa = False  # demo logins have no mailbox to receive a login link
    master_db.flush()
    return tenant


def _ensure_superadmin(master_db: Session, tenant_db: Session, tenant: Tenant) -> None:
    """Give the global admin access to the tenant, as tenant creation in Global Admin does."""
    admin_team = tenant_db.query(Team).filter_by(name="Admin").first()
    if not admin_team:
        admin_team = Team(name="Admin")
        tenant_db.add(admin_team)
        tenant_db.flush()

    global_admin = master_db.query(GlobalUser).filter_by(email=ADMIN_EMAIL).first()
    if not global_admin:
        return
    if not master_db.query(UserTenant).filter_by(global_user_id=global_admin.id, tenant_id=tenant.id).first():
        master_db.add(UserTenant(global_user_id=global_admin.id, tenant_id=tenant.id))
    if not tenant_db.query(User).filter_by(global_user_id=global_admin.id).first():
        tenant_db.add(User(username=ADMIN_EMAIL, password_hash="", admin=1,
                           global_user_id=global_admin.id, team_id=admin_team.id))
    tenant_db.flush()


def _seed_tenant(master_db: Session, tenant_db: Session, tenant: Tenant, spec: dict) -> None:
    _set_config(tenant_db, CMS_CONFIG_KEY, demo_data.DEMO_CMS)
    _ensure_superadmin(master_db, tenant_db, tenant)

    # --- Accounts and teams ---
    accounts = {}
    for a in spec["accounts"]:
        accounts[a["key"]] = Account(name=a["name"], extra=dict(a["extra"]))
    tenant_db.add_all(accounts.values())
    tenant_db.flush()

    teams = {}
    for t in spec["teams"]:
        teams[t["key"]] = Team(name=t["name"], account_id=accounts[t["account"]].id, extra=dict(t["extra"]))
    tenant_db.add_all(teams.values())
    tenant_db.flush()

    # --- Users: login identity in master DB, local user in tenant DB ---
    users = {}
    for u in spec["users"]:
        global_user = master_db.query(GlobalUser).filter_by(email=u["email"]).first()
        if not global_user:
            global_user = GlobalUser(email=u["email"], is_superadmin=False)
            global_user.set_password(demo_data.PASSWORD)
            master_db.add(global_user)
            master_db.flush()
        if not master_db.query(UserTenant).filter_by(global_user_id=global_user.id, tenant_id=tenant.id).first():
            master_db.add(UserTenant(global_user_id=global_user.id, tenant_id=tenant.id))

        local_user = tenant_db.query(User).filter_by(global_user_id=global_user.id).first()
        if not local_user:
            local_user = User(username=u["email"], global_user_id=global_user.id)
            tenant_db.add(local_user)
        local_user.admin = u["admin"]
        local_user.team_id = teams[u["team"]].id
        local_user.roles = dict(u["roles"])
        local_user.extra = dict(u["extra"])
        users[u["email"]] = local_user
    tenant_db.flush()

    # --- Products ---
    products = {}
    for p in spec["products"]:
        product = Product(
            type_id=p["type_id"], name=p["name"], price=p["price"], description=p["description"],
            start_date=_when(*p["start"]), end_date=_when(*p["end"]),
            extra_visilble_all=p["visible_all"], extra=dict(p["extra"]),
        )
        for n in p["filters"]:
            setattr(product, f"is_filter_{n}", True)
        products[p["key"]] = product
    tenant_db.add_all(products.values())

    # --- Customers ---
    customers = {}
    tag_names = []
    for c in spec["customers"]:
        customer = Customer(
            user_id=c["user_id"], first_name=c["first_name"], last_name=c["last_name"],
            email=c["email"], phone=c["phone"], description_phone=c["description_phone"],
            location=c["location"], contributes=c["contributes"],
            team_id=teams[c["team"]].id if c["team"] else None,
            assigned_user_id=users[c["assigned"]].id if c["assigned"] else None,
            comment=c["comment"], sub_caller=c["sub_caller"],
            organisations=list(c["organisations"]), categories=list(c["categories"]),
            personality_type=c["personality_type"], tags=list(c["tags"]), extra=dict(c["extra"]),
        )
        for n in c["filters"]:
            setattr(customer, f"is_filter_{n}", True)
        customers[c["key"]] = customer
        tag_names.extend(t for t in c["tags"] if t not in tag_names)
    tenant_db.add_all(customers.values())
    tenant_db.flush()

    # Tags also go in the tag tables, which feed the autocomplete in the customer form.
    for name in tag_names:
        tag = Tag(name=name)
        tenant_db.add(tag)
        tenant_db.flush()
        tenant_db.add(TagLink(tag_id=tag.id, object_type="tags"))

    # --- Product selections per customer ---
    for customer_key, product_key, status, type_status, order_days in spec["selections"]:
        tenant_db.add(ProductCustomer(
            customer_id=customers[customer_key].id, product_id=products[product_key].id,
            status=status, type_status=type_status,
            order_date=_when(order_days) if order_days is not None else None,
        ))

    # --- Calls (oldest first, so the call log reads chronologically) ---
    for customer_key, team_key, when, status, note in sorted(spec["calls"], key=lambda c: c[2]):
        call_date = _when(*when)
        customer = customers[customer_key]
        tenant_db.add(Call(customer_id=customer.id, team_id=teams[team_key].id,
                           call_date=call_date, status=status, note=note))
        # Same rule as the call center: answered and outside calls count as contact.
        if status in (demo_data.ANSWER, demo_data.OUTSIDE):
            if not customer.last_call_date or call_date > customer.last_call_date:
                customer.last_call_date = call_date

    # --- Alarms ---
    for customer_key, product_key, team_key, when, reminder_minutes, note in spec["alarms"]:
        date = _when(*when)
        tenant_db.add(Alarm(
            customer_id=customers[customer_key].id, product_id=products[product_key].id,
            team_id=teams[team_key].id, date=date,
            reminder=date - timedelta(minutes=reminder_minutes), note=note,
        ))

    # --- Companies ---
    companies = {}
    for c in spec["companies"]:
        companies[c["key"]] = Company(
            first_name=c["first_name"], last_name=c["last_name"], email=c["email"], phone=c["phone"],
            team_id=teams[c["team"]].id, comment=c["comment"], extra=dict(c["extra"]),
        )
    tenant_db.add_all(companies.values())
    tenant_db.flush()

    # --- Invoices ---
    for inv in spec["invoices"]:
        number = None
        if inv["status"] != demo_data.PROCESSING:
            # Approved (and later cancelled) invoices have drawn a number from the sequence.
            seq = InvoiceNumber()
            tenant_db.add(seq)
            tenant_db.flush()
            number = seq.id
        date = _when(inv["date"])
        tenant_db.add(Invoice(
            number=number, team_id=teams[inv["team"]].id, company_id=companies[inv["company"]].id,
            date=date,
            extra={
                "status": inv["status"],
                "due_date": (date + timedelta(days=inv["due"] - inv["date"])).strftime("%Y-%m-%d"),
                "vat": inv["vat"],
                "currency": inv["currency"],
                "note": inv["note"],
                "row": {
                    str(i): {"description": description, "price": price, "qty": qty}
                    for i, (description, price, qty) in enumerate(inv["rows"], start=1)
                },
            },
        ))

    _set_config(tenant_db, SEED_MARKER_KEY, {
        "version": SEED_VERSION,
        "seeded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    master_db.commit()
    tenant_db.commit()

    print(f"✅ Seeded '{spec['name']}': "
          f"{len(spec['users'])} users, {len(spec['customers'])} customers, "
          f"{len(spec['products'])} products, {len(spec['calls'])} calls, "
          f"{len(spec['alarms'])} alarms, {len(spec['companies'])} companies, "
          f"{len(spec['invoices'])} invoices")


def seed_test_data(reset: bool = False) -> None:
    """Seed the demo tenants. Skips a tenant that is already seeded or holds other data."""
    if reset:
        reset_demo_data()

    master_db = MasterSession()
    try:
        for spec in demo_data.TENANTS:
            db_url = _tenant_db_url(spec["slug"])
            if not db_url:
                print(f"ℹ️  Skipping demo tenant '{spec['slug']}': extra tenants are only seeded on SQLite.")
                continue

            tenant_db = _open_tenant_db(db_url)
            try:
                if _is_seeded(tenant_db):
                    print(f"ℹ️  Demo data already exists in '{spec['slug']}'. Skipping.")
                    continue
                if tenant_db.query(Customer).first():
                    print(f"⚠️  Tenant '{spec['slug']}' holds data that is not from this generator. "
                          "Run `python scripts/generate_test_data.py --reset` to replace it.")
                    break  # leave the other demo tenants alone too
                tenant = _ensure_tenant(master_db, spec, db_url)
                _seed_tenant(master_db, tenant_db, tenant, spec)
            except Exception as e:
                print(f"❌ Error generating demo data for '{spec['slug']}': {e}")
                import traceback
                traceback.print_exc()
                tenant_db.rollback()
                master_db.rollback()
            finally:
                tenant_db.close()
    finally:
        master_db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the demo tenants with demo data")
    parser.add_argument("--reset", action="store_true",
                        help="wipe the demo tenants (all records, demo users and teams) before seeding")
    args = parser.parse_args()
    seed_test_data(reset=args.reset)
