# Environment Variables Reference

**Load: when configuring the app for development, staging, or production**

| Var | Default | Notes |
|-----|---------|-------|
| `DATABASE_URL` | required | default tenant DB, e.g. `sqlite:////dbdata/app.db` |
| `MASTER_DATABASE_URL` | `DATABASE_URL` | master DB (GlobalUser, Tenant, LoginToken) |
| `DEBUG` | `false` | disables Jinja cache, enables hot reload |
| `JWT_SECRET_KEY` | `supersecret-jwt-key` | change in production |
| `SESSION_SECRET` | `super-secret-key` | change in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | WS token lifetime |
| `ADMIN_EMAIL` | `admin@localhost` | seeded on first start |
| `ADMIN_PASSWORD` | `1234` | seeded on first start |
| `APP_BASE_URL` | `http://localhost:8010` | used in 2FA email links |
| `SMTP_HOST` | `""` | leave empty to disable email |
| `SMTP_PORT` | `587` | |
| `SMTP_USER` | `""` | |
| `SMTP_PASSWORD` | `""` | |
| `SMTP_FROM` | `ADMIN_EMAIL` | sender address |
| `ENABLED_VERTICALS` | _(all)_ | comma-separated slugs to load, e.g. `customers,calls,admin` |
