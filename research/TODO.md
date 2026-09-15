# TODO

## Per-Vertical Role-Based Access Control

**Goal:** Extend `user.admin` flag to support modular, per-vertical roles while maintaining backward compatibility.

**Design:**
- Keep `user.admin` (Integer: 0/1) for tenant-wide admin check — existing behavior unchanged
- Add `user.roles` (JSON: `{"vertical_slug": bitmask}`) for per-vertical permissions
- Each vertical defines its own role bit constants (e.g., `INVOICING_ADMIN_BIT = 0b0100`)
- Roles are stackable per vertical (user can have multiple bits set)
- Tenant admins (`user.admin=1`) bypass all vertical role checks

**Implementation:**

- [ ] Add `roles` column to User model (JSON, default={})
- [ ] Create `core/roles.py` — `user_has_role(user, vertical_slug, role_bit)` helper
- [ ] Add `require_vertical_role(vertical_slug, role_bit)` FastAPI dependency to `core/auth.py`
- [ ] Update vertical manifests to define role constants (e.g., `verticals/invoices/roles.py`)
- [ ] Update routers that need per-vertical access control
- [ ] Migration: add roles column with default={}
- [ ] Update admin UI to manage per-vertical roles

**Backward Compatibility:** Existing `admin=1` users work as-is; new role features are opt-in per vertical.

---



