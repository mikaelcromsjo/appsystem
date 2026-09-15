# Test Data System Implementation Summary

## Overview

I've created a comprehensive test data generation system that automatically creates realistic test data on application startup. This includes users, teams, customers, products, calls, alarms, companies, and invoices with meaningful names that indicate their properties.

## What Was Created

### 1. **Test Data Generator Script**
**File:** `backend/scripts/generate_test_data.py`

- Automatically runs on app startup
- Idempotent (won't duplicate data on restart)
- Creates realistic test data with meaningful naming conventions
- Supports easy expansion for new verticals

**Includes:**
- 2 Accounts (Module 1 & 2 groupings)
- 4 Teams (customers+products, calls+alarms, invoices+companies, accounts)
- 7 Customers with filter properties
- 5 Products with varying prices and types
- 6 Product-Customer assignments with different statuses
- 4 Calls with dates and notes
- 3 Alarms with future reminder dates
- 3 Companies with contact info
- 4 Invoices with numbers and dates
- 6 Test Users with different roles and team assignments

### 2. **Integration with Startup**
**File Modified:** `backend/main.py`

Added automatic test data generation to the startup event:
```python
from scripts.generate_test_data import seed_test_data
seed_test_data()  # Called during app startup
```

### 3. **Documentation**

#### **TEST_DATA.md** - Comprehensive Reference
- Complete inventory of all test data created
- Naming conventions explained
- Data structure tables showing all records
- Usage instructions (automatic, manual, programmatic)
- Testing scenarios for each module

#### **TEST_SCENARIOS.md** - Practical Testing Guide
- 12 detailed testing scenarios covering both modules
- Quick login reference for all test users
- Step-by-step instructions for common workflows
- Permission testing examples
- Issue detection guide
- Quick data verification commands

#### **CLAUDE.md** - Updated
- Added reference to TEST_DATA.md in documentation

## Naming Conventions

All test data follows intuitive naming patterns:

### Teams
- `team_customers_products` - Module 1 team
- `team_calls_alarms` - Module 1 support team
- `team_invoices_companies` - Module 2 finance team
- `team_accounts_all` - Module 2 accounts team

### Users
- `m1admin` - Admin for Module 1
- `m2admin` - Admin for Module 2
- `sales` - Sales user with customers & products
- `support` - Support staff (calls & alarms)
- `finance` - Finance (invoices & companies)
- `viewer` - View-only user

All users have password: `1234`

### Customers
Names indicate their properties:
- `Alice_Active_filter1_filter2` - Has filter_1 and filter_2
- `Bob_Basic_filter3` - Has only filter_3
- `Charlie_Complex_filter1_filter4_filter5` - Multiple filters

### Products
- `prod_service_premium` (1500) - Premium service type
- `prod_consultation_standard` (500) - Standard consultation
- `prod_support_basic` (200) - Basic support package
- `prod_training_advanced` (3000) - Advanced training
- `prod_free_trial` (0) - Free entry point

### Companies
- `Acme Corp` - Main invoice contact
- `Tech Solutions` - Preferred vendor
- `Global Services` - Partner company

## Test Coverage

### Module 1: Customers, Products, Calls, Alarms
✅ 3 customers in customer-focused team
✅ 5 products with various characteristics
✅ 6 customer-product relationships with different statuses
✅ 4 calls with historical dates
✅ 3 alarms with future reminders
✅ Team isolation and role-based access

### Module 2: Invoices, Companies, Accounts
✅ 3 companies with contact information
✅ 4 invoices with sequential numbering
✅ Different team assignments
✅ Team isolation and role-based access

## Key Features

### 1. **Automatic Generation**
- Runs silently on startup if data doesn't exist
- No manual intervention required
- Perfect for fresh database recreation

### 2. **Idempotency**
- Checks for existing test data before creating
- Safe to restart app without duplicating data
- Can manually trigger by deleting test teams

### 3. **Realistic Data**
- Dates calculated relative to current time
- Proper relationships between entities
- Meaningful property assignments
- Varied statuses and filters

### 4. **Descriptive Naming**
- Names clearly indicate properties
- Easy to search for specific test data
- Self-documenting
- Patterns make sense across all entities

### 5. **Extensible**
- Easy to add more test data for new verticals
- Patterns established for consistency
- Comments in code for future developers
- Modular structure

## How to Use

### 1. **Automatic (On Startup)**
```bash
docker-compose up
# or
cd backend
uvicorn main:app --reload
```

Test data is automatically generated on first startup.

### 2. **Manual Regeneration**
```bash
# Delete existing test teams to trigger regeneration
python backend/scripts/inspect_db.py delete_teams team_customers_products

# Restart app
docker-compose up
```

### 3. **Programmatic**
```python
from scripts.generate_test_data import seed_test_data
seed_test_data()
```

### 4. **Verification**
```bash
python backend/scripts/inspect_db.py rows customers
python backend/scripts/inspect_db.py rows users
```

## Test User Reference

| Email | Role | Team | Password |
|-------|------|------|----------|
| m1admin | Admin | team_customers_products | 1234 |
| m2admin | Admin | team_invoices_companies | 1234 |
| sales | User | team_customers_products | 1234 |
| support | User | team_calls_alarms | 1234 |
| finance | User | team_invoices_companies | 1234 |
| viewer | User | team_accounts_all | 1234 |

## Adding New Test Data

To add test data for additional verticals:

1. **Create team in script:**
```python
team_new = Team(name="team_new_vertical", account_id=account_1.id)
tenant_db.add(team_new)
tenant_db.flush()
```

2. **Create sample records:**
```python
new_records = [NewModel(...), NewModel(...)]
tenant_db.add_all(new_records)
```

3. **Create test user:**
```python
test_users_data.append({
    "email": "user_newvertical@test.com",
    "username": "user_newvertical",
    "team_id": team_new.id,
    "roles": {"newvertical": 0b0001},
    ...
})
```

4. **Restart application**

## Files Modified

### Created:
- ✅ `backend/scripts/generate_test_data.py` (350+ lines)
- ✅ `docs/TEST_DATA.md` (350+ lines)
- ✅ `docs/TEST_SCENARIOS.md` (500+ lines)

### Modified:
- ✅ `backend/main.py` - Added 2 lines to call seed_test_data()
- ✅ `CLAUDE.md` - Added documentation reference

## Database State

### On Fresh Start:
1. Master DB: GlobalUser (admin@localhost) + Tenant (default)
2. Tenant DB: Team (Admin) + User (admin local account)
3. Test Data: All teams, customers, products, users, etc.

### Important Notes:
- Test data is marked with descriptive names
- Doesn't conflict with manually-created records
- Can coexist with production data
- Easy to identify and delete if needed

## Testing Quick Start

### Login:
- Email: `sales`
- Password: `1234`
- Team: team_customers_products

### Explore:
1. Go to Customers - see 3 test customers
2. Click on Alice - view products and calls
3. Go to Products - see 5 test products
4. Go to Calls - see calls for this team
5. Go to Alarms - see scheduled reminders

### Try Module 2:
- Switch to `finance` / `1234`
- Access invoices and companies

## Benefits

✅ **No Manual Setup** - Everything ready on startup
✅ **Consistent Naming** - Easy to understand test data
✅ **Complete Coverage** - All entities represented
✅ **Role Testing** - Multiple user types for permission testing
✅ **Relationship Testing** - Proper M2M, FK, and team assignments
✅ **Easy Extension** - Simple to add more data for new verticals
✅ **Safe** - Idempotent, no duplicate data
✅ **Well Documented** - Three docs covering all scenarios

## Next Steps

1. **Run the application:**
   ```bash
   docker-compose up
   ```

2. **Login with a test user** (see table above)

3. **Follow scenarios in TEST_SCENARIOS.md** for structured testing

4. **Check TEST_DATA.md** for complete inventory of what's available

5. **Add more test data** for new verticals as needed

## Support

If you need to:
- **Regenerate data:** Delete test teams and restart
- **Add more data:** Follow the pattern in generate_test_data.py
- **Understand relationships:** Check TEST_DATA.md tables
- **Test specific flows:** Use TEST_SCENARIOS.md step-by-step guides
- **Verify data:** Use inspect_db.py to query records
