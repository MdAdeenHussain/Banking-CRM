"""General utility helpers.

Keeps shared helper functions centralized and reusable across
routes, services, and future API modules.
"""

# =====================================
# SECTION: Imports
# =====================================
from datetime import datetime, timezone

from flask import g


# =====================================
# SECTION: Helper Functions
# =====================================
def utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def api_response(*, status: str, message: str, data: dict | list | None = None) -> dict:
    """Return API-friendly response dictionary.

    This structure is ready for future JSON endpoints while still
    being simple for beginners to understand.
    """
    return {
        "status": status,
        "message": message,
        "data": data or {},
        "request_id": getattr(g, "request_id", None),
        "timestamp": utc_now_iso(),
    }


def current_tenant_id() -> int | None:
    """Read tenant ID from request context set by middleware."""
    return getattr(g, "tenant_id", None)
