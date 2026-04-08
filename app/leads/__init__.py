"""
app/leads/__init__.py
Leads module blueprint.
"""

from flask import Blueprint

leads_bp = Blueprint("leads", __name__, url_prefix="/leads")

# Import routes to register them with blueprint
from app.leads import routes
