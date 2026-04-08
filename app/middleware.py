"""
app/middleware.py
Flask middleware for tenant injection, error handling, and request processing.
"""

from flask import g, request, abort, jsonify, session
from flask_login import current_user
from functools import wraps
import logging
import jwt
import os
from uuid import UUID

logger = logging.getLogger(__name__)


def inject_tenant():
    """
    CRITICAL: Inject tenant_id into g from:
    1. JWT claims (API calls with Authorization header)
    2. Session (web session from Flask-Login)
    3. Request attribute (from blueprint before_request)
    
    Must be set before ANY database query.
    
    Sets:
        g.tenant_id: UUID of current tenant
        g.user_id: UUID of current user
        g.user_roles: List of user role names
        g.request_ip: Client IP address
        g.user_agent: Client user agent
    
    Raises:
        401: If tenant cannot be identified
    """
    g.tenant_id = None
    g.user_id = None
    g.user_roles = []
    g.request_ip = request.remote_addr or "unknown"
    g.user_agent = request.headers.get("User-Agent", "unknown")
    
    # Route 1: Check Flask-Login session (web routes)
    if current_user.is_authenticated:
        g.user_id = current_user.id
        g.tenant_id = current_user.tenant_id
        
        # Get roles from user_roles relationship
        from app.auth.models import UserRole
        user_roles = UserRole.query.filter_by(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            is_active=True
        ).all()
        g.user_roles = [ur.role.name for ur in user_roles] if user_roles else []
        
        logger.debug(f"Tenant injected from session: {g.tenant_id}")
        return
    
    # Route 2: Check JWT token in Authorization header (API calls)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            # Parse "Bearer <token>"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret")
                
                payload = jwt.decode(token, secret_key, algorithms=["HS256"])
                
                g.user_id = UUID(payload.get("user_id"))
                g.tenant_id = UUID(payload.get("tenant_id"))
                
                # Optionally fetch roles from database for JWT
                from app.auth.models import UserRole
                user_roles = UserRole.query.filter_by(
                    user_id=g.user_id,
                    tenant_id=g.tenant_id,
                    is_active=True
                ).all()
                g.user_roles = [ur.role.name for ur in user_roles] if user_roles else []
                
                logger.debug(f"Tenant injected from JWT: {g.tenant_id}")
                return
        except (jwt.DecodeError, jwt.ExpiredSignatureError, ValueError, KeyError) as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            pass
    
    # Route 3: Check X-Tenant-ID header (for testing/admin)
    tenant_id_header = request.headers.get("X-Tenant-ID")
    if tenant_id_header:
        try:
            g.tenant_id = UUID(tenant_id_header)
            logger.debug(f"Tenant injected from header: {g.tenant_id}")
            return
        except ValueError:
            logger.warning(f"Invalid tenant ID in header: {tenant_id_header}")
    
    # If we reach here, tenant could not be identified
    # For login/register routes, this is OK
    # For protected routes, decorators will check g.tenant_id
    logger.debug("No tenant identified for this request")


def check_tenant_isolation():
    """
    Verify that cross-tenant data access is impossible.
    All ORM queries must filter by tenant_id.
    
    This is a safety check for development.
    """
    # PHASE_2_HOOK: Add database query inspection
    pass


def register_middleware(app):
    """
    Register all middleware with Flask app.
    
    Args:
        app: Flask application instance
    
    Note: before_request hook is registered in app.__init__.py
    """
    
    @app.after_request
    def after_request_handler(response):
        """Execute after each request."""
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request."""
        return jsonify({"status": "error", "message": "Bad request"}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized."""
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden."""
        return jsonify({"status": "error", "message": "Forbidden"}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found."""
        return jsonify({"status": "error", "message": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        from app.extensions import db
        db.session.rollback()
        logger.error(f"Internal error: {str(error)}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
