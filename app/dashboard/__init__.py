"""
app/dashboard/__init__.py
Dashboard module blueprint.
"""

from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# Import routes to register them with blueprint
from app.dashboard import routes
