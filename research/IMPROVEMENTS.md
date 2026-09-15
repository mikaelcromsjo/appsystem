# Plan for New Verticals

This plan is written to be easy to implement in Python and easy to extend with Claude Code. It is intentionally **general** so the system can support new award types, new business models, and new verticals without large refactors.

## Design goals

- Keep each business area isolated in its own vertical.
- Reuse the same CRUD, HTMX, filters, and rows/reload patterns everywhere.
- Avoid hardcoding reward logic to one compensation model.
- Support future award types such as direct sale rewards, team rewards, lead rewards, milestone rewards, campaign rewards, and vendor-funded rewards.
- Support future business models such as single-vendor sales, multi-vendor sales, partner sales, affiliate flows, booking flows, subscriptions, and service-based payouts.
- Prefer configuration and data-driven rules over special-case code.

## Shared design rules for all new verticals

Every new vertical should follow the same structure:

- `verticals/<slug>/__init__.py`
- `routers/<slug>.py`
- `models/<entity>.py`
- `templates/<slug>/list.html`
- `templates/<slug>/rows.html`
- `templates/<slug>/info.html`
- `templates/<slug>/edit.html`
- `functions/<domain>.py` for business logic

Each vertical should support:

- list page
- rows fragment
- info/detail view
- edit/create view
- upsert endpoint
- delete/archive endpoint if relevant
- session-based filters
- HTMX reload events
- use of `extra` JSON for flexible metadata

## General modelling principle

Do **not** model awards too narrowly.

Instead of building one model for each reward type, use a general structure:

- one model for the **event or achievement**
- one model for the **award/reward record**
- one model for the **payout or settlement**
- optional configuration models for plans, rules, and templates

This allows the system to support future models without schema churn.

## Core new verticals

## Leads

### Purpose

Track sales opportunities before they become customers, invoices, or payouts.

### Why this should be general

A lead may come from:

- a user
- a team
- a campaign
- a funnel
- a landing page
- a vendor
- an import
- an external integration

A lead may later be used for:

- conversion analytics
- ownership tracking
- reward triggers
- routing
- automation
- quality scoring

### Recommended shape

Use a `Lead` model that stays generic:

- owner
- team
- status
- source
- source_type
- campaign
- related customer if created later
- extra metadata

Avoid hardcoding lead sources into fixed columns. Prefer enums plus `extra`.

### Recommended endpoints

- `GET /leads/`
- `GET /leads/rows`
- `GET /leads/{id}`
- `GET /leads/{id}/edit`
- `POST /leads/upsert`
- `POST /leads/{id}/archive`

### Notes for Claude Code

- Follow the same list + rows pattern as customers.
- Support filters for owner, team, status, source, campaign, date range.
- Keep source handling extensible.
- Do not assume leads always come from one funnel model.

---

## Rewards

### Purpose

Store all earned value in a general ledger-like structure.

### Why this should be general

The system may later support:

- sale commission
- team bonus
- lead conversion reward
- invitation reward
- milestone reward
- streak reward
- vendor-sponsored reward
- campaign bonus
- manual adjustment
- penalty or clawback

If each one becomes its own table, the system will become hard to maintain.

### Recommended shape

Use one generic `Reward` or `AwardRecord` model with fields like:

- user_id
- team_id
- type
- status
- amount
- currency
- source_object_type
- source_object_id
- plan_key
- rule_key
- period_start
- period_end
- extra

This makes it possible to attach rewards to any future domain object.

### Important rule

Keep `type` broad and configurable.  
Do not encode business meaning only in Python logic.  
Store rule references so rewards can be traced back to plan configuration.

### Recommended endpoints

- `GET /rewards/`
- `GET /rewards/rows`
- `GET /rewards/{id}`
- `POST /rewards/recompute`
- `POST /rewards/{id}/approve`
- `POST /rewards/{id}/cancel`

### Notes for Claude Code

- Build this as a generic ledger vertical, not just “commission list”.
- Make filters work on type, status, user, team, period, source object, and plan.
- Make it safe for future negative entries such as corrections and clawbacks.

---

## Payouts

### Purpose

Group reward records into actual payment outputs.

### Why this should be general

Different organisations may pay in different ways:

- bank transfer
- internal balance
- manual payout
- payroll-style payout
- umbrella company
- gift card
- crypto or wallet-based payout
- invoice credit
- external provider API

The reward engine and payout engine should not be tightly coupled.

### Recommended shape

Use a `Payout` model plus optional `PayoutItem` linkage or `reward.payout_id`.

Suggested generic fields:

- recipient user
- payout method
- provider
- status
- total amount
- currency
- reference id
- period start/end
- extra

### Recommended endpoints

- `GET /payouts/`
- `GET /payouts/rows`
- `GET /payouts/{id}`
- `POST /payouts/generate`
- `POST /payouts/{id}/mark-processing`
- `POST /payouts/{id}/mark-paid`
- `POST /payouts/{id}/fail`

### Notes for Claude Code

- Keep payout generation as a function-layer concern.
- Do not assume one payout provider.
- Use adapter-style provider functions for external integrations.

---

## Reward Plans

### Purpose

Store reusable and configurable earning logic.

### Why this is needed

To remain adaptable, the system should not hardcode all compensation logic in routers or model methods.

Examples of future plans:

- fixed amount per sale
- percentage of invoice
- tiered commission
- team pool distribution
- reward only after paid invoice
- reward only after attendance
- split reward between owner and closer
- first-touch attribution
- last-touch attribution
- hybrid attribution

### Recommended shape

Use a `RewardPlan` model and possibly a `RewardRule` model.

A plan can define:

- applicable object types
- eligibility conditions
- formula type
- rate or amount
- thresholds
- stacking rules
- validity dates
- target scope (global, tenant, vendor, team, campaign)

Store flexible rule config in JSON.

### Recommended endpoints

- `GET /reward-plans/`
- `GET /reward-plans/rows`
- `GET /reward-plans/{id}`
- `GET /reward-plans/{id}/edit`
- `POST /reward-plans/upsert`

### Notes for Claude Code

- Make plans data-driven.
- Validation logic should exist, but formulas should not require schema changes for each new plan.
- Avoid embedding all rules in switch statements.

---

## Team Performance

### Purpose

Provide team-level visibility and support team-based reward models.

### Why this should be general

Some organisations will reward:

- total team revenue
- team conversion rate
- number of activated sellers
- number of qualified leads
- attendance or event completions
- monthly goals
- campaign outcomes

The team view should not assume only one KPI matters.

### Recommended shape

This can start as a reporting vertical using existing models and later add cached stats tables if needed.

Support metrics derived from:

- leads
- customers
- calls
- invoices
- rewards
- payouts

### Recommended endpoints

- `GET /team-performance/`
- `GET /team-performance/rows`
- `GET /team-performance/{team_id}`
- `GET /team-performance/{team_id}/members`

### Notes for Claude Code

- Keep the aggregation logic in `functions/teams_metrics.py`.
- Make KPI cards configurable.
- Do not hardcode “revenue only”.

---

## Campaigns

### Purpose

Track organised selling efforts, funnels, promotions, or referral pushes.

### Why this should be general

A campaign might be:

- a funnel
- a seasonal promotion
- a script test
- a referral drive
- a vendor-funded initiative
- a team challenge

Campaigns can later influence:

- lead routing
- rewards
- dashboards
- messaging
- A/B testing

### Recommended shape

Use a `Campaign` model with:

- name
- status
- owner
- type
- date range
- reward plan reference
- source settings
- extra

### Recommended endpoints

- `GET /campaigns/`
- `GET /campaigns/rows`
- `GET /campaigns/{id}`
- `POST /campaigns/upsert`

### Notes for Claude Code

- Do not assume campaigns are only marketing campaigns.
- Keep them generic enough to represent funnels and internal incentive programs.

---

## Vendors

### Purpose

Represent external product or service providers in a multi-vendor system.

### Why this should be general

Future vendor relationships may include:

- fixed catalog products
- services
- one-off offers
- subscription products
- event-based products
- payout sharing rules
- custom reward plans per vendor

### Recommended shape

Use a `Vendor` model with:

- name
- status
- contact info
- payout preferences
- default reward plan
- external references
- extra

Products should optionally point to a vendor.

### Recommended endpoints

- `GET /vendors/`
- `GET /vendors/rows`
- `GET /vendors/{id}`
- `POST /vendors/upsert`

### Notes for Claude Code

- Keep vendor config separate from reward execution.
- Allow vendor-specific overrides via plans or config.

---

## Invitations

### Purpose

Support inviting friends or co-workers into the organisation in a structured way.

### Why this should be general

Invitations may later support:

- no reward
- one-time reward
- staged reward
- team placement
- approval workflow
- email invite
- SMS invite
- referral link invite

### Recommended shape

Use an `Invitation` model with:

- inviter
- invitee contact
- tenant
- target team
- status
- token or key
- accepted_at
- extra

### Recommended endpoints

- `GET /invitations/`
- `GET /invitations/rows`
- `POST /invitations/upsert`
- `POST /invitations/{id}/resend`
- `POST /invitations/{id}/cancel`

### Notes for Claude Code

- Do not couple invitation completion directly to reward creation.
- Let invitation acceptance emit domain events or trigger service functions.

---

## Optional support verticals

## Rule Templates

A reusable configuration library for plans, campaign settings, scoring models, and payout methods.

## Analytics

A dedicated vertical for dashboards across leads, rewards, payouts, teams, and campaigns.

## Audit Log

A general event history vertical for compliance, debugging, and support.

## General implementation strategy for Claude Code

## 1. Build generic entities first

Implement in this order:

1. Leads
2. Rewards
3. Payouts
4. Reward Plans
5. Team Performance
6. Campaigns
7. Vendors
8. Invitations

This order keeps the core event → reward → payout flow intact.

## 2. Put business logic in functions, not routers

Routers should stay thin.

Examples:

- `functions/leads.py`
- `functions/rewards.py`
- `functions/payouts.py`
- `functions/reward_plans.py`
- `functions/teams_metrics.py`

Claude should avoid large routers with embedded business rules.

## 3. Prefer composition over special-case schema

Good:

- `Reward.type = "team_bonus"`
- `Reward.source_object_type = "invoice"`
- `Reward.extra = {...}`

Bad:

- one table per reward type
- one router per micro-variant
- many nullable columns for every future model

## 4. Make all list views follow the same HTMX contract

Every list-style vertical should have:

- shell page
- rows endpoint
- rows reload event
- session filter storage

Event convention:

- `<slug>RowsReload`

This keeps generated code predictable and reusable.

## 5. Use `extra` for future-proofing

Use `extra` for:

- experimental scoring values
- campaign metadata
- external ids
- provider-specific settings
- plan formula config
- attribution data

But do not hide critical relational data inside `extra` if it should be queryable.

## 6. Keep awards model-driven, not hardcoded

The system should be able to add a new award model by:

- creating or editing a plan
- linking a campaign/vendor/team to that plan
- updating service logic if truly needed

It should **not** require a new table or router every time.

## Suggested coding prompt style for Claude Code

When asking Claude to build a vertical, use prompts like:

- “Create a new vertical named `rewards` using the existing vertical manifest, router, HTMX rows pattern, and CRUD upsert conventions.”
- “Keep the data model generic enough to support future reward types and plan-based logic.”
- “Put all calculation logic in `functions/rewards.py`, not in the router.”
- “Use `extra` JSON for extensible metadata.”
- “Support filters via session and rows reload via `HX-Trigger`.”

## Final architectural rule

The system should treat **awards as configurable outcomes of business events**, not as fixed hardcoded features.

That means:

- business events can grow
- reward rules can grow
- payout models can grow
- vendor models can grow
- sales flows can grow

without changing the overall architecture.

If a new award idea appears later, the first question should be:

**“Can this be expressed as a new rule, plan, source type, or event type in the existing generic model?”**

If the answer is yes, the architecture is working.