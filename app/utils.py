"""
app/utils.py
Utility functions used across the application.
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import g, request, jsonify


# ============================================================================
# UUID GENERATION
# ============================================================================
def generate_uuid():
    """Generate a UUID v4."""
    return uuid.uuid4()


# ============================================================================
# PASSWORD HASHING
# ============================================================================
def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password (bcrypt hash)
    """
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    import bcrypt
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


# ============================================================================
# TOKEN GENERATION
# ============================================================================
def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure token.
    
    Args:
        length: Token length in bytes
    
    Returns:
        Hex-encoded secure token
    """
    return secrets.token_hex(length)


# ============================================================================
# PAGINATION
# ============================================================================
class Pagination:
    """Pagination helper for queries."""
    
    def __init__(self, items, page=1, per_page=20):
        """
        Initialize pagination.
        
        Args:
            items: Query or list of items
            page: Current page number (1-indexed)
            per_page: Items per page
        """
        self.items = items
        self.page = max(1, page)
        self.per_page = min(100, max(1, per_page))

    def paginate(self):
        """
        Execute pagination.
        
        Returns:
            dict with items, total, page, pages
        """
        if hasattr(self.items, "count"):
            # SQLAlchemy query
            total = self.items.count()
            items = self.items.limit(self.per_page).offset(
                (self.page - 1) * self.per_page
            ).all()
        else:
            # List
            total = len(self.items)
            start = (self.page - 1) * self.per_page
            end = start + self.per_page
            items = self.items[start:end]

        pages = (total + self.per_page - 1) // self.per_page

        return {
            "items": items,
            "total": total,
            "page": self.page,
            "pages": pages,
            "per_page": self.per_page,
        }


def paginate_query(query, page=1, per_page=20):
    """
    Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        Pagination dict
    """
    pagination = Pagination(query, page, per_page)
    return pagination.paginate()


# ============================================================================
# REQUEST HELPERS
# ============================================================================
def get_pagination_params():
    """
    Extract pagination parameters from query string.
    
    Returns:
        Tuple of (page, per_page)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return page, per_page


def get_tenant_id_from_request():
    """
    Extract tenant_id from current request context.
    
    Returns:
        UUID of current tenant
    """
    if hasattr(g, "tenant_id"):
        return g.tenant_id
    return None


def get_user_id_from_request():
    """
    Extract user_id from current request context.
    
    Returns:
        UUID of current user
    """
    if hasattr(g, "user_id"):
        return g.user_id
    return None


# ============================================================================
# RESPONSE HELPERS
# ============================================================================
def paginated_response(items, total, page, pages, per_page, message="Success"):
    """
    Create a standardized paginated API response.
    
    Args:
        items: List of items
        total: Total count
        page: Current page
        pages: Total pages
        per_page: Items per page
        message: Success message
    
    Returns:
        JSON response dict
    """
    return {
        "status": "success",
        "message": message,
        "data": items,
        "pagination": {
            "total": total,
            "page": page,
            "pages": pages,
            "per_page": per_page,
        }
    }


def success_response(data, message="Success", status_code=200):
    """
    Create a success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
    
    Returns:
        Tuple of (response dict, status code)
    """
    return {
        "status": "success",
        "message": message,
        "data": data
    }, status_code


def error_response(message, status_code=400, details=None):
    """
    Create an error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Additional error details
    
    Returns:
        Tuple of (response dict, status code)
    """
    response = {
        "status": "error",
        "message": message,
    }
    if details:
        response["details"] = details
    return response, status_code


# ============================================================================
# STRING SANITIZATION
# ============================================================================
def sanitize_input(value: str) -> str:
    """
    Sanitize user input to prevent XSS.
    
    Args:
        value: Raw user input
    
    Returns:
        Sanitized string
    """
    from flask import escape
    if not isinstance(value, str):
        return value
    return escape(value)


# ============================================================================
# EMAIL VALIDATION
# ============================================================================
def is_valid_email(email: str) -> bool:
    """
    Simple email validation.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid email format
    """
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


# ============================================================================
# PHONE VALIDATION
# ============================================================================
def is_valid_phone(phone: str) -> bool:
    """
    Validate Indian phone number (10 digits).
    
    Args:
        phone: Phone number
    
    Returns:
        True if valid format (10 digits)
    """
    import re
    pattern = r"^[6-9]\d{9}$"
    return re.match(pattern, phone) is not None


# ============================================================================
# TIME UTILITIES
# ============================================================================
def utcnow():
    """Get current UTC time."""
    return datetime.utcnow()


def days_since(datetime_obj):
    """
    Calculate days elapsed since datetime.
    
    Args:
        datetime_obj: datetime object
    
    Returns:
        Number of days elapsed
    """
    if datetime_obj is None:
        return None
    delta = datetime.utcnow() - datetime_obj
    return delta.days


# ============================================================================
# ENUM HELPERS
# ============================================================================
def get_enum_values(enum_class):
    """
    Get all values from an Enum class.
    
    Args:
        enum_class: Enum class
    
    Returns:
        List of enum values
    """
    return [item.value for item in enum_class]


def enum_to_choices(enum_class):
    """
    Convert Enum to list of (value, display) tuples for forms.
    
    Args:
        enum_class: Enum class
    
    Returns:
        List of (value, display) tuples
    """
    return [(item.value, item.name.replace("_", " ").title()) for item in enum_class]
