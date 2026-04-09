import os

from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import ADMIN_EMAIL, ADMIN_PASSWORD
from core.models.base import Base

DATABASE_URL = os.environ["DATABASE_URL"]
MASTER_DATABASE_URL = os.environ.get("MASTER_DATABASE_URL", DATABASE_URL)

# --- Tenant engine (used for single-tenant init, migrations, onboarding scripts) ---
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Master engine ---
_master_args = {"check_same_thread": False} if MASTER_DATABASE_URL.startswith("sqlite") else {}
master_engine = create_engine(MASTER_DATABASE_URL, connect_args=_master_args)
MasterSession = sessionmaker(autocommit=False, autoflush=False, bind=master_engine)

# Cache tenant engines by db_url to avoid recreating per request
_tenant_engines: dict[str, object] = {}


def _get_tenant_engine(db_url: str):
    if db_url not in _tenant_engines:
        args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        _tenant_engines[db_url] = create_engine(db_url, connect_args=args)
    return _tenant_engines[db_url]


def get_master_db():
    db = MasterSession()
    try:
        yield db
    finally:
        db.close()


def get_db(request: Request):
    db_url = request.session.get("tenant_db_url")
    if not db_url:
        raise HTTPException(status_code=401, detail="No tenant selected")
    tenant_engine = _get_tenant_engine(db_url)
    db = sessionmaker(bind=tenant_engine)()
    try:
        yield db
    finally:
        db.close()


def _migrate_master_schema():
    """Apply schema changes that create_all() cannot handle (column renames, additions).
    Safe to run on both fresh and existing databases."""
    import sqlalchemy as sa

    inspector = sa.inspect(master_engine)
    tables = inspector.get_table_names()

    with master_engine.connect() as conn:
        # global_users: username -> email rename
        if "global_users" in tables:
            gu_cols = {c["name"] for c in inspector.get_columns("global_users")}
            if "username" in gu_cols and "email" not in gu_cols:
                conn.execute(sa.text("ALTER TABLE global_users RENAME COLUMN username TO email"))
                conn.commit()

        # tenants: add require_2fa
        if "tenants" in tables:
            t_cols = {c["name"] for c in inspector.get_columns("tenants")}
            if "require_2fa" not in t_cols:
                conn.execute(sa.text("ALTER TABLE tenants ADD COLUMN require_2fa BOOLEAN DEFAULT 1"))
                conn.commit()
            if "enabled_verticals" not in t_cols:
                conn.execute(sa.text("ALTER TABLE tenants ADD COLUMN enabled_verticals VARCHAR"))
                conn.commit()

        # global_users: add is_superadmin
        if "global_users" in tables:
            gu_cols = {c["name"] for c in inspector.get_columns("global_users")}
            if "is_superadmin" not in gu_cols:
                conn.execute(sa.text("ALTER TABLE global_users ADD COLUMN is_superadmin BOOLEAN DEFAULT 0"))
                conn.commit()

    # login_tokens: create if missing (create_all handles new DBs; this covers existing ones)
    if "login_tokens" not in tables:
        from models.master import MasterBase
        MasterBase.metadata.tables["login_tokens"].create(bind=master_engine, checkfirst=True)


def init_admin_user():
    from models.master import GlobalUser, Tenant, UserTenant
    from core.models.models import User

    _migrate_master_schema()

    master_db: Session = MasterSession()
    tenant_db: Session = SessionLocal()

    try:
        # Ensure default tenant exists
        tenant = master_db.query(Tenant).filter_by(slug="default").first()
        if not tenant:
            tenant = Tenant(slug="default", name="Default", db_url=DATABASE_URL)
            master_db.add(tenant)
            master_db.flush()

        # Ensure global admin exists
        global_user = master_db.query(GlobalUser).filter_by(email=ADMIN_EMAIL).first()
        if not global_user:
            global_user = GlobalUser(email=ADMIN_EMAIL, is_superadmin=True)
            global_user.set_password(ADMIN_PASSWORD)
            master_db.add(global_user)
            master_db.flush()
        elif not global_user.is_superadmin:
            global_user.is_superadmin = True
            master_db.flush()

        # Link global admin to default tenant
        link = master_db.query(UserTenant).filter_by(
            global_user_id=global_user.id, tenant_id=tenant.id
        ).first()
        if not link:
            master_db.add(UserTenant(global_user_id=global_user.id, tenant_id=tenant.id))

        master_db.commit()

        # Ensure default Team exists in tenant DB
        from models.caller import Team
        default_team = tenant_db.query(Team).filter_by(name="Admin").first()
        if not default_team:
            default_team = Team(name="Admin")
            tenant_db.add(default_team)
            tenant_db.flush()

        # Ensure local User exists in tenant DB
        local_user = tenant_db.query(User).filter_by(global_user_id=global_user.id).first()
        if not local_user:
            local_user = User(username=ADMIN_EMAIL, password_hash="", admin=1,
                              global_user_id=global_user.id, caller_id=default_team.id)
            tenant_db.add(local_user)
            tenant_db.commit()
            print(f"✅ Admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        elif local_user.caller_id is None:
            local_user.caller_id = default_team.id
            tenant_db.commit()

    finally:
        master_db.close()
        tenant_db.close()
