# 🧩 AppSystem

> One platform for call center, invoicing, and team operations — built so teams see only what their role needs, and new modules snap in without touching the core.

[![Live Demo](https://img.shields.io/badge/demo-system.ia--ai.se-e94560?style=for-the-badge)](https://system.ia-ai.se)
[![ia-ai.se](https://img.shields.io/badge/ia--ai.se-website-e94560?style=for-the-badge)](https://ia-ai.se)
[![Contact](https://img.shields.io/badge/email-mikael.cromsjo%40gmail.com-e94560?style=for-the-badge)](mailto:mikael.cromsjo@gmail.com)

---

## What is this?

A modular framework for running team-based business operations under one roof, with proper multi-tenant isolation and role-based team access. Every business module — Customers, Invoices, Call Center — is a self-contained **vertical**: its own routes, templates, and permissions, auto-discovered and added to navigation with no changes to core code.

- 📞 **Call Center** — live customer queue, real-time WebSocket call handling and logging
- ⏰ **Alarms & Reminders** — scheduled reminders tied to customers/products, background scheduler
- 🧾 **Invoicing & Companies** — sequential invoice numbering, client records, bank account details
- 👥 **Customers & Products** — shared customer database, product catalog, per-customer status tracking
- 🗂️ **Teams & Roles** — per-module roles by team; one team runs Call Center + Alarms, another only Invoices + Companies
- 🌐 **Multi-tenant by design** — every tenant gets an isolated database; a Global Admin oversees all tenants and users from one panel
- 🔐 **Secure login** — email + password, optional two-factor verification via a one-time magic link

## Stack

FastAPI · Jinja2 + HTMX + Alpine.js · TailwindCSS · SQLite

## Running it

```bash
docker compose up -d
```

- App: `http://localhost:8070`
- See `docs/CONFIG.md` for the full environment variable reference (`JWT_SECRET_KEY`, `SESSION_SECRET`, `APP_BASE_URL`, SMTP settings for 2FA emails, etc.)

## Building a new module

```
backend/verticals/<name>/
  __init__.py   # manifest: slug, label, order, routes
  router.py
  templates/
```

Restart — the module is discovered automatically, with roles applied. See `docs/PATTERNS_ADVANCED.md`.

---

<div align="center">

[ia-ai.se](https://ia-ai.se) · [mikael.cromsjo@gmail.com](mailto:mikael.cromsjo@gmail.com)

</div>
