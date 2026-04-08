"""
app/notifications/__init__.py
Notifications module blueprint.
"""

from flask import Blueprint

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

# PHASE_2_HOOK: Import routes
