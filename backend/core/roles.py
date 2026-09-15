"""
Per-vertical role-based access control.

Roles are stored as a JSON dict on User.roles: {"vertical_slug": bitmask_int}
Tenant admins (user.admin=1) bypass all role checks.
"""


def user_has_role(user, vertical_slug: str, role_bit: int) -> bool:
    """
    Check if a user has a specific role in a vertical.

    Args:
        user: User object with admin and roles attributes
        vertical_slug: e.g. "invoices", "products"
        role_bit: bitmask integer, e.g. 0b0001 for ADMIN role

    Returns:
        True if user.admin=1 (tenant admin bypass) OR if the bitmask matches
    """
    if user.admin:
        return True  # tenant admins have all roles
    return bool((user.roles or {}).get(vertical_slug, 0) & role_bit)
