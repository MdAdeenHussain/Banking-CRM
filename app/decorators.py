"""Reusable decorators for authorization and tenant-safe access."""

# =====================================
# SECTION: Imports
# =====================================
from functools import wraps

from flask import abort
from flask_login import current_user, login_required


# =====================================
# SECTION: Decorator Definitions
# =====================================
def role_required(*allowed_roles: str):
    """Ensure authenticated user has an allowed role."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in allowed_roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapper

    return decorator
