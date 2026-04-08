"""
app/customers/__init__.py
Customers module blueprint.
"""

from flask import Blueprint

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")

# PHASE_2_HOOK: Import routes
