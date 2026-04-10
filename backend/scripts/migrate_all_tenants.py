#!/usr/bin/env python3
"""
Migrate all tenant databases to the latest schema.

This script:
1. Queries the master DB for all active tenants
2. For each tenant, runs `alembic upgrade head` against that tenant's DB
3. Reports success/failure for each tenant

Usage:
    python scripts/migrate_all_tenants.py
"""

import sys
import os
import subprocess
from sqlalchemy.orm import Session

# --- Path setup ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.database import get_master_db, MasterSession
from models.master import Tenant


def migrate_tenant(db_url: str, tenant_slug: str) -> bool:
    """Run alembic upgrade against a single tenant database."""
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url

    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print(f"  ✅ {tenant_slug}: migration successful")
            return True
        else:
            print(f"  ❌ {tenant_slug}: migration failed")
            print(f"     Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ❌ {tenant_slug}: migration timed out")
        return False
    except Exception as e:
        print(f"  ❌ {tenant_slug}: {e}")
        return False


def main():
    print("🔄 Migrating all tenant databases...\n")

    # Get master DB session
    master_db = MasterSession()

    try:
        # Query all active tenants
        tenants = master_db.query(Tenant).filter_by(active=True).all()

        if not tenants:
            print("⚠️  No active tenants found.")
            return 0

        print(f"Found {len(tenants)} active tenant(s):\n")

        success_count = 0
        for tenant in tenants:
            if migrate_tenant(tenant.db_url, tenant.slug):
                success_count += 1

        print(f"\n{'='*50}")
        print(f"✅ Migration complete: {success_count}/{len(tenants)} successful")
        print(f"{'='*50}")

        return 0 if success_count == len(tenants) else 1

    finally:
        master_db.close()


if __name__ == "__main__":
    sys.exit(main())
