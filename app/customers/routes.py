"""
app/customers/routes.py
Customer management routes (CRM customer 360 profiles).
PHASE_2_HOOK: Complete implementation in Subphase 5.
"""

from flask import request, jsonify, g
from app.customers import customers_bp
from app.decorators import login_required, tenant_required

# ============================================================================
# CUSTOMER LIST
# ============================================================================

@customers_bp.route("", methods=["GET"])
@login_required
@tenant_required
def list_customers():
    """GET /customers - List all customers."""
    # PHASE_2_HOOK: Pagination, search, filters
    return {"message": "Customer list implementation pending"}, 200


# ============================================================================
# CUSTOMER DETAIL
# ============================================================================

@customers_bp.route("/<customer_id>", methods=["GET"])
@login_required
@tenant_required
def get_customer(customer_id):
    """GET /customers/<uuid> - Get customer 360 profile."""
    # PHASE_2_HOOK: Full profile with linked leads
    return {"message": "Customer detail implementation pending"}, 200


# ============================================================================
# CUSTOMER UPDATE
# ============================================================================

@customers_bp.route("/<customer_id>", methods=["PUT"])
@login_required
@tenant_required
def update_customer(customer_id):
    """PUT /customers/<uuid> - Update customer profile."""
    # PHASE_2_HOOK: Update KYC fields
    return {"message": "Customer update implementation pending"}, 200
