"""
app/auth/__init__.py
Authentication module blueprint.
"""

from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Import routes to register them with blueprint
from app.auth import routes
