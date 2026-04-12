"""
LoanAxis CRM — Role-Based Access Control (RBAC) Configuration

Centralized permission definitions. All route-level access checks
go through has_permission() — never hardcode role strings in routes.

Permission syntax:
    "module.*"            → all actions on module
    "module.action"       → specific action
    "module.own.action"   → only on own records
    "*"                   → superuser / all permissions
"""

from typing import Optional

# ── Permission Definitions ──────────────────────────────────────

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "super_admin": ["*"],  # Full access to everything

    "admin": [
        # Lead management
        "leads.*",
        # Employee management (create employees only, not admins)
        "employees.view",
        "employees.create",
        "employees.edit",
        "employees.deactivate",
        # Task management
        "tasks.*",
        # Document management
        "documents.*",
        # Commission viewing (not editing rates)
        "commissions.view",
        "commissions.summary",
        # Invoice viewing
        "invoices.view",
        "invoices.create",
        # Reports (branch scope)
        "reports.view",
        "reports.create",
        # Notifications
        "notifications.*",
        # Export (branch level)
        "exports.leads",
        "exports.commissions",
        "exports.employees",
        # Bank applications
        "bank_applications.*",
        # Remarks
        "remarks.*",
        # Analytics
        "analytics.view",
    ],

    "employee": [
        # Lead management (own leads only)
        "leads.create",
        "leads.own.view",
        "leads.own.update",
        # Document management (own leads)
        "documents.upload",
        "documents.own.view",
        # Task management (own tasks)
        "tasks.own.view",
        "tasks.own.update",
        # Commission viewing (own, read-only)
        "commissions.own.view",
        # Remarks (own leads)
        "remarks.create",
        "remarks.own.view",
        # Notifications (own)
        "notifications.own.*",
        # Bank applications (own leads)
        "bank_applications.own.view",
    ],
}

# ── Role Display Names ──────────────────────────────────────────

ROLE_DISPLAY_NAMES: dict[str, str] = {
    "super_admin": "Director / CRM Owner",
    "admin": "Operations Manager",
    "employee": "Loan Relationship Executive",
}

# ── Role Hierarchy (higher number = more privilege) ─────────────

ROLE_HIERARCHY: dict[str, int] = {
    "employee": 1,
    "admin": 2,
    "super_admin": 3,
}


def has_permission(user_role: str, required_permission: str) -> bool:
    """
    Check if a role has a specific permission.

    Supports wildcard matching:
        - "*" matches everything
        - "leads.*" matches "leads.create", "leads.view", etc.
        - Exact match: "leads.create" matches "leads.create"

    Args:
        user_role: The user's role string (e.g., "super_admin")
        required_permission: The permission to check (e.g., "leads.create")

    Returns:
        True if the role has the required permission
    """
    if user_role not in ROLE_PERMISSIONS:
        return False

    permissions = ROLE_PERMISSIONS[user_role]

    for perm in permissions:
        # Superuser wildcard
        if perm == "*":
            return True

        # Exact match
        if perm == required_permission:
            return True

        # Wildcard match: "leads.*" matches "leads.create"
        if perm.endswith(".*"):
            prefix = perm[:-2]  # Remove ".*"
            if required_permission.startswith(prefix + "."):
                return True
            # Also match the module itself
            if required_permission == prefix:
                return True

    return False


def get_role_display_name(role: str) -> str:
    """Get the human-readable display name for a role."""
    return ROLE_DISPLAY_NAMES.get(role, role.replace("_", " ").title())


def is_role_higher(role_a: str, role_b: str) -> bool:
    """Check if role_a is strictly higher than role_b in the hierarchy."""
    return ROLE_HIERARCHY.get(role_a, 0) > ROLE_HIERARCHY.get(role_b, 0)


def can_manage_role(manager_role: str, target_role: str) -> bool:
    """
    Check if a manager with manager_role can manage users of target_role.

    Rules:
        - super_admin can manage admin and employee
        - admin can manage employee only
        - employee cannot manage anyone
    """
    if manager_role == "super_admin":
        return target_role in ("admin", "employee")
    if manager_role == "admin":
        return target_role == "employee"
    return False


def get_manageable_roles(user_role: str) -> list[str]:
    """Get list of roles that a user with the given role can create/manage."""
    if user_role == "super_admin":
        return ["admin", "employee"]
    if user_role == "admin":
        return ["employee"]
    return []


def get_all_permissions_for_role(role: str) -> list[str]:
    """Get the flat list of permissions for a role."""
    return ROLE_PERMISSIONS.get(role, [])
