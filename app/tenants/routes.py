"""
app/tenants/routes.py
Tenant management routes (registration, configuration).
PHASE_2_HOOK: Complete implementation in Subphase 4.
"""

from flask import request, jsonify, g
from app.tenants import tenants_bp
from app.decorators import login_required, tenant_required, super_admin_required

# ============================================================================
# PLACEHOLDER ROUTE (Real implementation in Subphase 4)
# ============================================================================

@tenants_bp.route("/health", methods=["GET"])
def tenant_health():
    """Health check for tenant module."""
    return {"status": "Tenant module ready"}, 200
