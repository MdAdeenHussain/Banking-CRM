"""
app/tenants/__init__.py
Tenants module blueprint.
"""

from flask import Blueprint

tenants_bp = Blueprint("tenants", __name__, url_prefix="/tenants")

# PHASE_2_HOOK: Import routes
