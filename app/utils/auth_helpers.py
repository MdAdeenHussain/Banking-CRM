"""
LoanAxis CRM — Auth Helpers

Decorators and utilities for role-based access control.
Used by every protected route to enforce permissions.
"""

from functools import wraps
from typing import Callable

from flask import abort, flash, redirect, url_for, request
from flask_login import current_user

from app.config.permissions import has_permission, get_role_display_name


def require_role(*roles: str) -> Callable:
    """
    Decorator to restrict route access to specific roles.

    Usage:
        @require_role('super_admin', 'admin')
        def manage_employees():
            ...

    Returns 403 if the user's role is not in the allowed list.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login", next=request.url))

            if not current_user.is_active:
                flash("Your account has been deactivated. Contact your administrator.", "danger")
                return redirect(url_for("auth.login"))

            if current_user.role not in roles:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_permission(permission: str) -> Callable:
    """
    Decorator to restrict route access based on granular permissions.

    Usage:
        @require_permission('leads.create')
        def create_lead():
            ...

    Uses the centralized ROLE_PERMISSIONS config for checking.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login", next=request.url))

            if not current_user.is_active:
                flash("Your account has been deactivated.", "danger")
                return redirect(url_for("auth.login"))

            if not has_permission(current_user.role, permission):
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_lead_access(lead, action: str = "view") -> bool:
    """
    Check if the current user can access a specific lead.

    Rules:
        - Super Admin: full access to all leads
        - Admin: access to leads in their branch
        - Employee: access to own assigned leads only
    """
    if not current_user.is_authenticated:
        return False

    if current_user.role == "super_admin":
        return True

    if current_user.role == "admin":
        # Admin can access leads in their branch
        if lead.branch_id == current_user.branch_id:
            return True
        # Admin can also access leads assigned to them
        if lead.assigned_admin_id == current_user.id:
            return True
        return False

    if current_user.role == "employee":
        # Employee can only access their assigned leads
        if action == "view":
            return lead.assigned_executive_id == current_user.id
        if action == "update":
            return lead.assigned_executive_id == current_user.id
        return False

    return False


def get_user_display_info() -> dict:
    """
    Get display information for the current user.
    Used in templates for navbar/sidebar rendering.
    """
    if not current_user.is_authenticated:
        return {}

    return {
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "role_display": get_role_display_name(current_user.role),
        "employee_id": current_user.employee_id,
        "profile_photo": current_user.profile_photo_path,
        "is_super_admin": current_user.is_super_admin,
        "is_admin": current_user.is_admin,
    }
