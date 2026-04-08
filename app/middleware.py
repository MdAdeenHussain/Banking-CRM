"""Request/response middleware layer.

This module keeps request lifecycle hooks centralized so they are
simple to extend with observability, tenancy controls, and security.
"""

# =====================================
# SECTION: Imports
# =====================================
import uuid

from flask import Flask, g
from flask_login import current_user


# =====================================
# SECTION: Middleware Registration
# =====================================
def register_middleware(app: Flask) -> None:
    """Register before/after request hooks."""

    @app.before_request
    def inject_request_context() -> None:
        """Attach common context to each request.

        - request_id: useful for logs/troubleshooting
        - tenant_id: used by tenant-safe service filters
        """
        g.request_id = str(uuid.uuid4())

        if current_user.is_authenticated:
            g.tenant_id = current_user.tenant_id
        else:
            g.tenant_id = None

    @app.after_request
    def attach_response_headers(response):
        """Attach standard headers to outgoing responses."""
        response.headers["X-Request-ID"] = getattr(g, "request_id", "unknown")
        return response
