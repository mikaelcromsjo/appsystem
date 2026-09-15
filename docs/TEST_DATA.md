# Test Data System

## Overview

The test data generator (`backend/scripts/generate_test_data.py`) creates a realistic set of test data for development and testing. It runs automatically on application startup in development mode.

## What Gets Created

### Naming Convention

All test entities follow naming conventions that indicate their properties:

- **Teams**: `team_<modules>` - e.g., `team_customers_products` indicates Module 1
- **Users**: `user_<role>_<team>` - e.g., `user_admin_sales` indicates admin role
- **Customers**: `cust_<status>_<properties>` - e.g., `cust_active_filter1_filter2`
- **Products**: `prod_<type>_<price>` - e.g., `prod_service_1000`

This makes it easy to understand what each test record represents.

## Data Structure

### Accounts (2 total)

| ID | Name | Purpose |
|----|------|---------|
| 1 | Account 1 - Module 1 | Contains teams for Module 1 (customers, products, calls, alarms) |
| 2 | Account 2 - Module 2 | Contains teams for Module 2 (invoices, companies, accounts) |

### Teams (4 total)

#### Module 1 Teams

| Name | Account | Verticals | Purpose |
|------|---------|-----------|---------|
| `team_customers_products` | Account 1 | customers, products | Sales/product management |
| `team_calls_alarms` | Account 1 | calls, alarms | Support/reminder management |

#### Module 2 Teams

| Name | Account | Verticals | Purpose |
|------|---------|-----------|---------|
| `team_invoices_companies` | Account 2 | invoices, companies | Finance/billing |
| `team_accounts_all` | Account 2 | accounts | Account management |

### Customers (7 total)

| Team | Name | User ID | Filter Properties | Status |
|------|------|---------|-------------------|--------|
| team_customers_products | Alice Active_filter1_filter2 | alice_001 | filter_1, filter_2 | VIP customer |
| team_customers_products | Bob Basic_filter3 | bob_002 | filter_3 | Standard customer |
| team_customers_products | Charlie Complex_... | charlie_003 | filter_1, filter_4, filter_5 | High-value customer |
| team_calls_alarms | Diana Urgent_... | diana_004 | filter_2, filter_3 | Support priority |
| team_calls_alarms | Ethan VIP_... | ethan_005 | filter_1, filter_5 | VIP account |
| team_invoices_companies | Fiona Invoice_client | fiona_006 | filter_1 | Invoice test |
| team_accounts_all | George Company_contact | george_007 | filter_2 | Account test |

### Products (5 total)

| Name | Type | Price | Filters | Features |
|------|------|-------|---------|----------|
| prod_service_premium | service | 1500 | filter_1 | Premium tier |
| prod_consultation_standard | consultation | 500 | filter_2 | Standard option |
| prod_support_basic | support | 200 | filter_3, filter_4 | Basic support |
| prod_training_advanced | training | 3000 | filter_5 | Advanced course |
| prod_free_trial | trial | 0 | filter_1, filter_2 | Free entry point |

### Links (ProductCustomer) (6 total)

| Customer | Product | Status | Status Name |
|----------|---------|--------|------------|
| Alice | prod_service_premium | 3 | Going |
| Alice | prod_consultation_standard | 5 | Attended |
| Bob | prod_support_basic | 1 | Not going |
| Charlie | prod_training_advanced | 3 | Going |
| Diana | prod_service_premium | 2 | Maybe |
| Ethan | prod_free_trial | 4 | Paid |

### Calls (4 total)

| Customer | Team | Date | Status | Note |
|----------|------|------|--------|------|
| Alice | team_customers_products | -2 days | [1] | Initial consultation call |
| Bob | team_customers_products | -5 days | [2] | Follow-up call |
| Diana | team_calls_alarms | -1 day | [1] | Urgent support call |
| Ethan | team_calls_alarms | today | [0] | VIP account review |

### Alarms (3 total)

| Customer | Team | Product | Alert Date | Note |
|----------|------|---------|------------|------|
| Alice | team_customers_products | prod_service_premium | +7 days | Schedule renewal meeting |
| Diana | team_calls_alarms | prod_training_advanced | +3 days | Training completion follow-up |
| Ethan | team_calls_alarms | (none) | +14 days | Quarterly business review |

### Companies (3 total)

| Name | Team | Email | Notes |
|------|------|-------|-------|
| Acme Corp | team_invoices_companies | billing@acme.com | Main invoice contact |
| Tech Solutions | team_invoices_companies | accounts@techsol.com | Preferred vendor |
| Global Services | team_accounts_all | support@globalserv.com | Partner company |

### Invoices (4 total)

| Number | Team | Company | Date |
|--------|------|---------|------|
| 1001 | team_invoices_companies | Acme Corp | -30 days |
| 1002 | team_invoices_companies | Tech Solutions | -15 days |
| 2001 | team_accounts_all | Global Services | -7 days |
| 1003 | team_invoices_companies | Acme Corp | today |

### Test Users (6 total)

All test users have password: `1234`

| Email | Username | Team | Role | Admin | Verticals |
|-------|----------|------|------|-------|-----------|
| m1admin | m1admin | team_customers_products | Admin | ✓ | customers, products |
| m2admin | m2admin | team_invoices_companies | Admin | ✓ | invoices, companies |
| sales | sales | team_customers_products | User | ✗ | customers, products |
| support | support | team_calls_alarms | User | ✗ | calls, alarms |
| finance | finance | team_invoices_companies | User | ✗ | invoices, companies |
| viewer | viewer | team_accounts_all | User | ✗ | (none) |

## Usage

### Automatic Generation

Test data is generated automatically on startup when the app detects it doesn't exist:

```bash
docker-compose up
# or
cd backend
uvicorn main:app --reload
```

The generator checks for existing test teams and skips if found.

### Manual Generation

To regenerate test data (if needed), delete the test teams and restart:

```bash
# Using the inspect_db.py tool
python backend/scripts/inspect_db.py delete_teams team_customers_products team_calls_alarms team_invoices_companies team_accounts_all

# Then restart the application
```

### Programmatic Usage

```python
from scripts.generate_test_data import seed_test_data

seed_test_data()  # Creates test data if not already present
```

## Testing Scenarios

### Module 1: Customer, Product, Calls & Alarms

**Users to test with:**
- `admin_m1@test.com` - Full admin access
- `sales_team@test.com` - Team member access
- `support_team@test.com` - Support team

**Test data:**
- 3 customers with various filter properties
- 5 products with different price points
- 4 calls with different statuses
- 3 alarms with future reminders
- 6 product-customer relationships with varied statuses

**Common workflows:**
1. Create a new customer, assign products, make a call
2. Filter customers by properties (filters 1-5)
3. Manage calls and create alarms
4. Assign customers to products with different statuses

### Module 2: Invoices & Companies

**Users to test with:**
- `admin_m2@test.com` - Full admin access
- `finance_user@test.com` - Finance role
- `limited_access@test.com` - Limited access

**Test data:**
- 3 companies with contact info
- 4 invoices with different dates
- 2 teams for different departments

**Common workflows:**
1. Create invoices linked to companies
2. View invoice history by date
3. Manage company contacts
4. Link customers to company invoices

## Adding More Test Data

To add more test data for new verticals:

1. **Add new team** in the `seed_test_data()` function:
   ```python
   team_new_vertical = Team(
       name="team_vertical_name",
       account_id=account_1.id
   )
   tenant_db.add(team_new_vertical)
   ```

2. **Add sample records** for that vertical with descriptive names
3. **Add test user** with appropriate roles
4. **Restart the application**

The naming convention makes it clear what properties each test record has, making it easy to:
- Find specific test data
- Understand what is being tested
- Add new variations without confusion

## Database State

### Initial State (on startup)

- Default account "Admin" + "Admin" team created by `init_admin_user()`
- Default user: admin@localhost / 1234 (via ADMIN_EMAIL / ADMIN_PASSWORD env)
- Test data added by `seed_test_data()`

### Idempotency

The `seed_test_data()` function checks for existing test teams before creating:

```python
existing_team = tenant_db.query(Team).filter_by(name="team_customers_products").first()
if existing_team:
    print("ℹ️  Test data already exists. Skipping generation.")
    return
```

This prevents duplicate data on repeated restarts.

## Development Tips

- **Test user emails** are easy to remember: `{role}_{team}@test.com`
- **Customer names** indicate their properties: `Alice_Active_filter1_filter2` shows filters
- **Product names** show type and price: `prod_service_1000` is a service product at 1000 price
- **Team names** indicate modules: `team_invoices_companies` shows what's in that team

This naming scheme makes it easy to write tests that reference specific test data by pattern.
