"""
Generate test data for the system.

Naming conventions for test entities:
- Teams: "team_<modules>" e.g., "team_customers_products" indicates Module 1
- Users: "user_<role>_<team>" e.g., "user_admin_sales" indicates admin role in sales team
- Customers: "cust_<status>_<properties>" e.g., "cust_active_filter1_filter2"
- Products: "prod_<type>_<price>" e.g., "prod_service_1000"

Modules:
- Module 1: customers, products, calls, alarms
- Module 2: customers, companies, accounts, invoices
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database import SessionLocal, MasterSession
from models.master import GlobalUser, Tenant, UserTenant
from models.user import User, pwd_context
from models.account import Account
from models.team import Team
from models.customer import Customer
from models.product import Product
from models.product_customer import ProductCustomer
from models.call import Call
from models.alarm import Alarm
from models.company import Company
from models.invoice import Invoice, InvoiceNumber


def seed_test_data():
    """Generate test data for development and testing."""
    tenant_db = SessionLocal()
    master_db = MasterSession()

    try:
        # Check if test data already exists
        existing_team = tenant_db.query(Team).filter_by(name="team_customers_products").first()
        if existing_team:
            print("ℹ️  Test data already exists. Skipping generation.")
            return

        print("🌱 Generating test data...")

        # ============================================================
        # MODULE 1: CUSTOMERS, PRODUCTS, CALLS, ALARMS
        # ============================================================

        # Create Accounts
        account_1 = Account(name="Account 1 - Module 1")
        account_2 = Account(name="Account 2 - Module 2")
        tenant_db.add_all([account_1, account_2])
        tenant_db.flush()

        # Create Teams for Module 1
        team_customers_products = Team(
            name="team_customers_products",
            account_id=account_1.id
        )
        team_calls_alarms = Team(
            name="team_calls_alarms",
            account_id=account_1.id
        )

        # Create Teams for Module 2
        team_invoices_companies = Team(
            name="team_invoices_companies",
            account_id=account_2.id
        )
        team_accounts_all = Team(
            name="team_accounts_all",
            account_id=account_2.id
        )

        tenant_db.add_all([
            team_customers_products,
            team_calls_alarms,
            team_invoices_companies,
            team_accounts_all,
        ])
        tenant_db.flush()

        # Create Products
        products = [
            Product(
                name="prod_service_premium",
                type_id="service",
                price=1500,
                description="Premium service product",
                is_filter_1=True,
            ),
            Product(
                name="prod_consultation_standard",
                type_id="consultation",
                price=500,
                description="Standard consultation",
                is_filter_2=True,
            ),
            Product(
                name="prod_support_basic",
                type_id="support",
                price=200,
                description="Basic support package",
                is_filter_3=True,
                is_filter_4=True,
            ),
            Product(
                name="prod_training_advanced",
                type_id="training",
                price=3000,
                description="Advanced training course",
                is_filter_5=True,
            ),
            Product(
                name="prod_free_trial",
                type_id="trial",
                price=0,
                description="Free trial product",
                is_filter_1=True,
                is_filter_2=True,
            ),
        ]
        tenant_db.add_all(products)
        tenant_db.flush()

        # Create Customers for team_customers_products
        customers_cp = [
            Customer(
                first_name="Alice",
                last_name="Active_filter1_filter2",
                user_id="alice_001",
                email="alice@example.com",
                phone="+46701234567",
                location="Stockholm",
                team_id=team_customers_products.id,
                is_filter_1=True,
                is_filter_2=True,
                personality_type=1,
            ),
            Customer(
                first_name="Bob",
                last_name="Basic_filter3",
                user_id="bob_002",
                email="bob@example.com",
                phone="+46702345678",
                location="Gothenburg",
                team_id=team_customers_products.id,
                is_filter_3=True,
                personality_type=2,
            ),
            Customer(
                first_name="Charlie",
                last_name="Complex_filter1_filter4_filter5",
                user_id="charlie_003",
                email="charlie@example.com",
                phone="+46703456789",
                location="Malmö",
                team_id=team_customers_products.id,
                is_filter_1=True,
                is_filter_4=True,
                is_filter_5=True,
                personality_type=3,
                contributes=1000,
            ),
        ]
        tenant_db.add_all(customers_cp)
        tenant_db.flush()

        # Create Customers for team_calls_alarms
        customers_ca = [
            Customer(
                first_name="Diana",
                last_name="Urgent_filter2_filter3",
                user_id="diana_004",
                email="diana@example.com",
                phone="+46704567890",
                location="Uppsala",
                team_id=team_calls_alarms.id,
                is_filter_2=True,
                is_filter_3=True,
                personality_type=1,
            ),
            Customer(
                first_name="Ethan",
                last_name="VIP_filter1_filter5",
                user_id="ethan_005",
                email="ethan@example.com",
                phone="+46705678901",
                location="Västerås",
                team_id=team_calls_alarms.id,
                is_filter_1=True,
                is_filter_5=True,
                personality_type=4,
                contributes=5000,
            ),
        ]
        tenant_db.add_all(customers_ca)
        tenant_db.flush()

        # Create Customers for Module 2 teams
        customers_m2 = [
            Customer(
                first_name="Fiona",
                last_name="Invoice_client",
                user_id="fiona_006",
                email="fiona@example.com",
                phone="+46706789012",
                location="Linköping",
                team_id=team_invoices_companies.id,
                is_filter_1=True,
            ),
            Customer(
                first_name="George",
                last_name="Company_contact",
                user_id="george_007",
                email="george@example.com",
                phone="+46707890123",
                location="Helsingborg",
                team_id=team_accounts_all.id,
                is_filter_2=True,
            ),
        ]
        tenant_db.add_all(customers_m2)
        tenant_db.flush()

        # Link customers to products via ProductCustomer
        pc_assignments = [
            ProductCustomer(customer_id=customers_cp[0].id, product_id=products[0].id, status=3),  # Alice -> Premium
            ProductCustomer(customer_id=customers_cp[0].id, product_id=products[1].id, status=5),  # Alice -> Consultation (attended)
            ProductCustomer(customer_id=customers_cp[1].id, product_id=products[2].id, status=1),  # Bob -> Support (not going)
            ProductCustomer(customer_id=customers_cp[2].id, product_id=products[3].id, status=3),  # Charlie -> Training
            ProductCustomer(customer_id=customers_ca[0].id, product_id=products[0].id, status=2),  # Diana -> Premium (maybe)
            ProductCustomer(customer_id=customers_ca[1].id, product_id=products[4].id, status=4),  # Ethan -> Trial (paid)
        ]
        tenant_db.add_all(pc_assignments)
        tenant_db.flush()

        # Create Calls
        now = datetime.now(timezone.utc)
        calls = [
            Call(
                customer_id=customers_cp[0].id,
                team_id=team_customers_products.id,
                call_date=now - timedelta(days=2),
                status=[1],
                note="Initial consultation call",
            ),
            Call(
                customer_id=customers_cp[1].id,
                team_id=team_customers_products.id,
                call_date=now - timedelta(days=5),
                status=[2],
                note="Follow-up call",
            ),
            Call(
                customer_id=customers_ca[0].id,
                team_id=team_calls_alarms.id,
                call_date=now - timedelta(days=1),
                status=[1],
                note="Urgent support call",
            ),
            Call(
                customer_id=customers_ca[1].id,
                team_id=team_calls_alarms.id,
                call_date=now,
                status=[0],
                note="VIP account review",
            ),
        ]
        tenant_db.add_all(calls)
        tenant_db.flush()

        # Create Alarms
        alarms = [
            Alarm(
                customer_id=customers_cp[0].id,
                product_id=products[0].id,
                team_id=team_customers_products.id,
                date=now,
                reminder=now + timedelta(days=7),
                note="Schedule renewal meeting",
            ),
            Alarm(
                customer_id=customers_ca[0].id,
                product_id=products[3].id,
                team_id=team_calls_alarms.id,
                date=now,
                reminder=now + timedelta(days=3),
                note="Training completion follow-up",
            ),
            Alarm(
                customer_id=customers_ca[1].id,
                team_id=team_calls_alarms.id,
                date=now,
                reminder=now + timedelta(days=14),
                note="Quarterly business review",
            ),
        ]
        tenant_db.add_all(alarms)
        tenant_db.flush()

        # ============================================================
        # MODULE 2: INVOICES & COMPANIES
        # ============================================================

        # Create Companies
        companies = [
            Company(
                first_name="Acme",
                last_name="Corp",
                email="billing@acme.com",
                phone="+46801234567",
                team_id=team_invoices_companies.id,
                comment="Main invoice contact",
            ),
            Company(
                first_name="Tech",
                last_name="Solutions",
                email="accounts@techsol.com",
                phone="+46802345678",
                team_id=team_invoices_companies.id,
                comment="Preferred vendor",
            ),
            Company(
                first_name="Global",
                last_name="Services",
                email="support@globalserv.com",
                phone="+46803456789",
                team_id=team_accounts_all.id,
                comment="Partner company",
            ),
        ]
        tenant_db.add_all(companies)
        tenant_db.flush()

        # Create InvoiceNumbers seed
        for i in range(10):
            tenant_db.add(InvoiceNumber())
        tenant_db.flush()

        # Create Invoices
        invoices = [
            Invoice(
                number=1001,
                team_id=team_invoices_companies.id,
                company_id=companies[0].id,
                date=now - timedelta(days=30),
            ),
            Invoice(
                number=1002,
                team_id=team_invoices_companies.id,
                company_id=companies[1].id,
                date=now - timedelta(days=15),
            ),
            Invoice(
                number=2001,
                team_id=team_accounts_all.id,
                company_id=companies[2].id,
                date=now - timedelta(days=7),
            ),
            Invoice(
                number=1003,
                team_id=team_invoices_companies.id,
                company_id=companies[0].id,
                date=now,
            ),
        ]
        tenant_db.add_all(invoices)
        tenant_db.commit()

        # ============================================================
        # CREATE TEST USERS WITH DIFFERENT ROLES AND TEAM ASSIGNMENTS
        # ============================================================

        # Get the default tenant for linking users
        from models.master import Tenant as MasterTenant
        default_tenant = master_db.query(MasterTenant).filter_by(slug="default").first()
        if not default_tenant:
            # If no default tenant, use the first one
            default_tenant = master_db.query(MasterTenant).first()

        # Get or create global users for test accounts
        test_users_data = [
            {
                "email": "m1admin@x",
                "username": "m1admin",
                "password": "1234",
                "description": "Admin - Module 1 (customers, products, calls, alarms)",
                "team_id": team_customers_products.id,
                "admin": 1,
                "roles": {
                    "customers": 0b0001,
                    "products": 0b0001,
                },
            },
            {
                "email": "m2admin@x",
                "username": "m2admin",
                "password": "1234",
                "description": "Admin - Module 2 (invoices, companies, accounts)",
                "team_id": team_invoices_companies.id,
                "admin": 1,
                "roles": {
                    "invoices": 0b0001,
                    "companies": 0b0001,
                },
            },
            {
                "email": "sales@x",
                "username": "sales",
                "password": "1234",
                "description": "Sales team user - customers & products",
                "team_id": team_customers_products.id,
                "admin": 0,
                "roles": {
                    "customers": 0b0001,
                    "products": 0b0001,
                },
            },
            {
                "email": "support@x",
                "username": "support",
                "password": "1234",
                "description": "Support team user - calls & alarms",
                "team_id": team_calls_alarms.id,
                "admin": 0,
                "roles": {},  # Can still use calls/alarms, but no explicit roles
            },
            {
                "email": "finance@x",
                "username": "finance",
                "password": "1234",
                "description": "Finance - invoices & companies",
                "team_id": team_invoices_companies.id,
                "admin": 0,
                "roles": {
                    "invoices": 0b0001,
                    "companies": 0b0001,
                },
            },
            {
                "email": "viewer@x",
                "username": "viewer",
                "password": "1234",
                "description": "Limited access user - read-only view",
                "team_id": team_accounts_all.id,
                "admin": 0,
                "roles": {},
            },
        ]

        for user_data in test_users_data:
            # Create or update global user
            global_user = master_db.query(GlobalUser).filter_by(email=user_data["email"]).first()
            if not global_user:
                global_user = GlobalUser(
                    email=user_data["email"],
                    is_superadmin=False,
                )
                global_user.set_password(user_data["password"])
                master_db.add(global_user)
                master_db.flush()

                # Link user to default tenant
                if default_tenant:
                    link = master_db.query(UserTenant).filter_by(
                        global_user_id=global_user.id, tenant_id=default_tenant.id
                    ).first()
                    if not link:
                        master_db.add(UserTenant(
                            global_user_id=global_user.id,
                            tenant_id=default_tenant.id
                        ))
                        master_db.flush()

            # Create tenant local user
            local_user = tenant_db.query(User).filter_by(global_user_id=global_user.id).first()
            if not local_user:
                local_user = User(
                    username=user_data["username"],
                    global_user_id=global_user.id,
                    admin=user_data["admin"],
                    team_id=user_data["team_id"],
                    roles=user_data["roles"],
                    extra={"description": user_data["description"]},
                )
                tenant_db.add(local_user)
                tenant_db.flush()
                print(f"✅ User created: {user_data['email']} ({user_data['description']})")

        master_db.commit()
        tenant_db.commit()

        print("✅ Test data generated successfully!")
        print("\n📋 Test Users Created (password: 1234):")
        print("   - m1admin (Admin - Module 1)")
        print("   - m2admin (Admin - Module 2)")
        print("   - sales (Sales - Customers & Products)")
        print("   - support (Support - Calls & Alarms)")
        print("   - finance (Finance - Invoices & Companies)")
        print("   - viewer (Limited - View Only)")
        print("\n📦 Test Data Summary:")
        print(f"   Teams: {tenant_db.query(Team).count()}")
        print(f"   Customers: {tenant_db.query(Customer).count()}")
        print(f"   Products: {tenant_db.query(Product).count()}")
        print(f"   Calls: {tenant_db.query(Call).count()}")
        print(f"   Alarms: {tenant_db.query(Alarm).count()}")
        print(f"   Companies: {tenant_db.query(Company).count()}")
        print(f"   Invoices: {tenant_db.query(Invoice).count()}")
        print(f"   Product-Customer Links: {tenant_db.query(ProductCustomer).count()}")

    except Exception as e:
        print(f"❌ Error generating test data: {e}")
        import traceback
        traceback.print_exc()
        tenant_db.rollback()
        master_db.rollback()
    finally:
        tenant_db.close()
        master_db.close()


if __name__ == "__main__":
    seed_test_data()
