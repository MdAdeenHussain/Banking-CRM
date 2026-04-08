"""
app/errors.py
Custom exception classes for the application.
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException


class APIError(Exception):
    """
    Base API error class.
    Can be caught by error handler to return JSON response.
    """
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert to dictionary for JSON response."""
        rv = dict(self.payload or ())
        rv["error"] = self.message
        return rv


class ValidationError(APIError):
    """Validation error (422)."""
    def __init__(self, message, payload=None):
        super().__init__(message, 422, payload)


class AuthenticationError(APIError):
    """Authentication error (401)."""
    def __init__(self, message="Unauthorized", payload=None):
        super().__init__(message, 401, payload)


class AuthorizationError(APIError):
    """Authorization error (403) - user not allowed."""
    def __init__(self, message="Forbidden", payload=None):
        super().__init__(message, 403, payload)


class NotFoundError(APIError):
    """Resource not found (404)."""
    def __init__(self, message="Not found", payload=None):
        super().__init__(message, 404, payload)


class ConflictError(APIError):
    """Resource conflict (409)."""
    def __init__(self, message, payload=None):
        super().__init__(message, 409, payload)


class TenantError(APIError):
    """Tenant isolation violation."""
    def __init__(self, message="Tenant access denied", payload=None):
        super().__init__(message, 403, payload)


class RateLimitError(APIError):
    """Rate limit exceeded (429)."""
    def __init__(self, message="Too many requests", payload=None):
        super().__init__(message, 429, payload)


class ServerError(APIError):
    """Internal server error (500)."""
    def __init__(self, message="Internal server error", payload=None):
        super().__init__(message, 500, payload)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

def register_error_handlers(app):
    """Register error handlers with Flask app."""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle APIError exceptions."""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request."""
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized."""
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden."""
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found."""
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity."""
        return jsonify({"error": "Unprocessable entity"}), 422

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Too Many Requests."""
        return jsonify({"error": "Too many requests"}), 429

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        from app.extensions import db
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
