# Common Testing Scenarios with Test Data

## Quick Login Reference

All test users password: `1234`

| Email | Team | Use Case |
|-------|------|----------|
| m1admin | team_customers_products | Admin - Full access to Module 1 |
| sales | team_customers_products | Regular user - Customers & Products |
| m2admin | team_invoices_companies | Admin - Full access to Module 2 |
| finance | team_invoices_companies | Regular user - Invoices & Companies |
| support | team_calls_alarms | Support staff - Calls & Alarms |
| viewer | team_accounts_all | View-only user - Limited access |

---

## Module 1: Customers, Products, Calls & Alarms

### Scenario 1: Basic Customer Management

**Login:** `sales` / `1234`

**Steps:**
1. Go to Customers
2. View list - should see Alice, Bob, Charlie (team_customers_products team)
3. Click on Alice "Active_filter1_filter2" - view customer details
4. Notice assigned products: Premium (status: going), Consultation (status: attended)
5. View call history - should see call from -2 days
6. View alarms - scheduled for +7 days

**What to check:**
- Customer filter properties displayed correctly (filter_1, filter_2)
- Product links show status/attendance correctly
- Call dates and notes visible
- Alarms scheduled for future

### Scenario 2: Product Management

**Login:** `m1admin` / `1234`

**Steps:**
1. Go to Products
2. View all 5 test products:
   - prod_service_premium (1500) - filter_1
   - prod_consultation_standard (500) - filter_2
   - prod_support_basic (200) - filter_3, filter_4
   - prod_training_advanced (3000) - filter_5
   - prod_free_trial (0) - filter_1, filter_2
3. Click on prod_service_premium - view linked customers:
   - Alice: Going
   - Diana: Maybe
4. Edit a product, save changes

**What to check:**
- Product list displays with types and prices
- Customer links and statuses correct
- Price points vary appropriately (free to 3000)
- Filter flags visible and correct

### Scenario 3: Filtering by Customer Properties

**Login:** `sales_team@test.com`

**Steps:**
1. Go to Customers
2. Apply filter for "filter_1" - should show:
   - Alice (filter_1, filter_2)
   - Charlie (filter_1, filter_4, filter_5)
   - Fiona (filter_1) - from other team
3. Clear filter, apply "filter_5" - should show:
   - Charlie
   - Diana
   - Ethan
4. Apply multiple filters

**What to check:**
- Filters work correctly
- Right customers appear for each filter
- Team filtering respected
- Multi-filter combinations work

### Scenario 4: Call Management

**Login:** `support` / `1234`

**Steps:**
1. Go to Calls
2. View 4 test calls:
   - Alice: -2 days, "Initial consultation call"
   - Bob: -5 days, "Follow-up call"
   - Diana: -1 day, "Urgent support call" (Diana is in same team)
   - Ethan: today, "VIP account review" (Ethan is in same team)
3. Click on Diana's call - view details
4. Create new call for one of these customers
5. Update a call's status/note

**What to check:**
- Calls appear for correct team
- Dates and notes display properly
- Can view/edit call details
- New calls can be created

### Scenario 5: Alarm Management

**Login:** `support` / `1234`

**Steps:**
1. Go to Alarms
2. View 3 test alarms:
   - Alice's renewal meeting (+7 days)
   - Diana's training follow-up (+3 days)
   - Ethan's quarterly review (+14 days)
3. Note that some have products linked, some don't
4. Create a new alarm for a customer in this team
5. Check alarm reminders are scheduled correctly

**What to check:**
- Alarms display with correct dates
- Product links optional and correct
- Can filter by date range
- Reminder dates in future as expected

### Scenario 6: Product Assignment to Customers

**Login:** `sales_team@test.com`

**Steps:**
1. Go to Customers → Alice
2. View products section showing:
   - prod_service_premium: Going (status 3)
   - prod_consultation_standard: Attended (status 5)
3. Go to Products → prod_support_basic
4. View assigned customers:
   - Bob: Not Going (status 1)
5. Try assigning a different product to a customer
6. Update product status (going → attended, etc.)

**What to check:**
- Product-customer relationships clear
- Different status values work (not going=1, maybe=2, going=3, paid=4, attended=5)
- Assignments can be created/updated
- Relationship works from both directions

---

## Module 2: Invoices & Companies

### Scenario 7: Invoice Management

**Login:** `m2admin` / `1234`

**Steps:**
1. Go to Invoices
2. View 4 test invoices:
   - #1001 (30 days ago) - Acme Corp
   - #1002 (15 days ago) - Tech Solutions
   - #2001 (7 days ago) - Global Services
   - #1003 (today) - Acme Corp
3. Filter by date range - recent invoices
4. Click on invoice #1001 - view details (company, date, team)
5. Create new invoice linked to a company

**What to check:**
- Invoice numbers increment properly
- Linked companies correct
- Dates display and filter correctly
- Team filtering works
- Can create new invoices

### Scenario 8: Company Management

**Login:** `finance` / `1234`

**Steps:**
1. Go to Companies
2. View 2 companies in this team:
   - Acme Corp (billing@acme.com)
   - Tech Solutions (accounts@techsol.com)
3. Click on Acme Corp - view:
   - 2 invoices linked (#1001, #1003)
   - Contact details
   - Comments
4. Edit company contact info
5. Add a new company

**What to check:**
- Company info displays correctly
- Linked invoices show correctly
- Can edit company details
- New companies can be added
- Contact info validated (email, phone)

### Scenario 9: Cross-Team Data Isolation

**Login as:** `finance_user@test.com` (team_invoices_companies)

**Steps:**
1. Go to Customers - should NOT see:
   - Alice, Bob, Charlie (team_customers_products)
   - Diana, Ethan (team_calls_alarms)
2. Should see:
   - Fiona (team_invoices_companies)
   - Possibly George (team_accounts_all)
3. Go to Invoices - should see invoices from team_invoices_companies
4. **Switch team if possible** - data changes

**What to check:**
- Team filtering enforced
- No data leakage between teams
- Can only see customers/data from own team
- Admin users see all (if applicable)

### Scenario 10: Finance Workflow

**Login:** `m2admin` / `1234`

**Steps:**
1. Go to Companies → Acme Corp
2. View linked invoices (2)
3. Go to Invoices → create new one for Acme
4. Go back to Companies - new invoice appears
5. Filter invoices by company, by date range
6. Export or view invoice details

**What to check:**
- Companies and invoices properly linked
- Bidirectional relationship works
- Can filter efficiently
- Data consistency maintained

---

## Role & Permission Testing

### Scenario 11: Admin vs Regular User

**Login as admin:**
`admin_m1@test.com` (admin=1, roles: customers, products)

**Expected abilities:**
- Create, read, update, delete all records
- Assign users to teams
- Manage all data regardless of filters

**Login as regular user:**
`sales_team@test.com` (admin=0, roles: customers, products)

**Expected abilities:**
- View/edit customers and products (role-based)
- Cannot delete users
- Cannot change system settings
- Own team data only (usually)

**Test:** Try editing a customer as both users - permissions should differ

### Scenario 12: Vertical Access Control

**Login:** `finance` / `1234`

**Has access to:**
- invoices vertical (role=ADMIN)
- companies vertical (role=ADMIN)

**Should NOT have access to:**
- customers vertical
- products vertical
- calls vertical
- alarms vertical

**Test:**
1. Try navigating to /customers - should be blocked or empty
2. Try /products - should be blocked or empty
3. Try /invoices - should work fully
4. Try /companies - should work fully

---

## Common Issue Detection

### ✅ Everything Working Correctly When:

- Test users can login with test credentials
- Data appears with correct dates (relative dates calculated properly)
- Filters work and show appropriate records
- Can navigate between related records (customer → products → invoices)
- Team filtering prevents data leakage
- Alarms show future dates correctly
- Call statuses display appropriately
- Product prices vary as expected

### ⚠️ Potential Issues:

| Issue | Check |
|-------|-------|
| No test data visible | Run `seed_test_data()` or restart app |
| Wrong team data appears | Check team_id foreign keys |
| Dates in past/wrong format | Verify datetime calculations, timezone |
| Filters not working | Check filter column names (is_filter_1, etc.) |
| Data duplication on restart | Verify idempotency check works |
| Users can't login | Check GlobalUser/User link via global_user_id |
| Roles not working | Verify roles dict format: {"vertical": 0b0001} |
| Cross-team data visible | Check where clauses for team_id filtering |

---

## Quick Data Checks

**Use these searches to verify test data:**

```bash
# Check test teams exist
python backend/scripts/inspect_db.py rows teams

# Check test customers (filter by name pattern)
python backend/scripts/inspect_db.py rows customers | grep -E "Alice|Bob|Charlie"

# Check test users
python backend/scripts/inspect_db.py rows users | grep "test.com\|_team\|admin_"

# Check products (should see 5)
python backend/scripts/inspect_db.py rows products | wc -l

# Check calls (should see 4)
python backend/scripts/inspect_db.py rows calls

# Verify relationships
python backend/scripts/inspect_db.py rows product_customers
```
