"""
app/decorators.py
Route decorators for authentication, authorization, and audit logging.
"""

from functools import wraps
from flask import g, jsonify, request
from flask_login import current_user
from app.errors import AuthenticationError, AuthorizationError, TenantError
from app.constants import UserRole


# ============================================================================
# AUTHENTICATION DECORATOR
# ============================================================================
def login_required(f):
    """
    Ensure user is logged in (session or JWT).
    Works for both web routes (session) and API routes (JWT).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in via session (web)
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        
        # Check JWT token (API)
        # PHASE_2_HOOK: Implement JWT verification from headers
        # For now, require session-based login
        raise AuthenticationError("Please log in to access this resource")
    
    return decorated_function


# ============================================================================
# TENANT ISOLATION DECORATOR
# ============================================================================
def tenant_required(f):
    """
    Ensure tenant_id is set in g (by middleware).
    If tenant_id is missing, user is not properly authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, "tenant_id") or g.tenant_id is None:
            raise TenantError("Tenant not identified in request")
        return f(*args, **kwargs)
    
    return decorated_function


# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================
def role_required(*allowed_roles):
    """
    Ensure user has one of the allowed roles.
    
    Args:
        *allowed_roles: Variable number of UserRole enum values
    
    Example:
        @route("/admin")
        @role_required(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)
        def admin_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Ensure user is logged in
            if not current_user.is_authenticated:
                raise AuthenticationError("Authentication required")
            
            # Ensure tenant is set
            if not hasattr(g, "tenant_id") or g.tenant_id is None:
                raise TenantError("Tenant not identified")
            
            # Fetch user roles from g (set by middleware)
            # PHASE_2_HOOK: Implement g.user_roles in middleware
            user_roles = getattr(g, "user_roles", [])
            
            # Check if user has any of the allowed roles
            if not any(role in allowed_roles for role in user_roles):
                raise AuthorizationError(
                    f"Your role does not have permission to access this resource. "
                    f"Required roles: {[r.value for r in allowed_roles]}"
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# ============================================================================
# AUDIT LOGGING DECORATOR
# ============================================================================
def audit_log(action):
    """
    Log mutation action to AuditLog table.
    
    Args:
        action: AuditAction enum value (CREATE, UPDATE, DELETE, etc.)
    
    Example:
        @route("/leads/<lead_id>", methods=["PUT"])
        @audit_log(AuditAction.UPDATE)
        def update_lead(lead_id):
            # After route completes, mutation is automatically logged
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # PHASE_2_HOOK: Capture old values before route execution
            # Implement full audit trail with before/after snapshots
            
            result = f(*args, **kwargs)
            
            # PHASE_2_HOOK: Log action to AuditLog table
            # Extract entity type/id from route args or result
            # Log: user_id, tenant_id, entity_type, entity_id, action, old_values, new_values, IP, user_agent
            
            return result
        
        return decorated_function
    return decorator


# ============================================================================
# SUPER ADMIN ONLY
# ============================================================================
def super_admin_required(f):
    """
    Ensure user is a super_admin.
    Only super_admin can access platform-level features.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            raise AuthenticationError("Authentication required")
        
        # Check if user is super_admin
        # PHASE_2_HOOK: Verify against g.user_roles or user.roles
        user_roles = getattr(g, "user_roles", [])
        if UserRole.SUPER_ADMIN not in user_roles:
            raise AuthorizationError("Super admin access required")
        
        return f(*args, **kwargs)
    
    return decorated_function


# ============================================================================
# TENANT ADMIN REQUIRED
# ============================================================================
def tenant_admin_required(f):
    """
    Ensure user is tenant_admin or super_admin for their tenant.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            raise AuthenticationError("Authentication required")
        
        user_roles = getattr(g, "user_roles", [])
        allowed = [UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN]
        
        if not any(role in allowed for role in user_roles):
            raise AuthorizationError("Tenant admin access required")
        
        return f(*args, **kwargs)
    
    return decorated_function


# ============================================================================
# RATE LIMITING DECORATOR (Optional, can use Flask-Limiter)
# ============================================================================
def rate_limit(max_requests=100, time_window=60):
    """
    Simple rate limiting decorator (rough implementation).
    For production, use Flask-Limiter.
    
    Args:
        max_requests: Maximum requests allowed
        time_window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # PHASE_2_HOOK: Implement with Redis at app level
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# ============================================================================
# RESPONSE WRAPPER (Optional)
# ============================================================================
def json_response(f):
    """
    Ensure route returns JSON (if not already JSON).
    Useful for standardizing error responses.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        # If already response tuple, return as-is
        if isinstance(result, tuple):
            return result
        # Otherwise wrap in success response
        return jsonify({"status": "success", "data": result}), 200
    
    return decorated_function
