"""
app/dashboard/routes.py
Dashboard routes (role-specific KPI views).
PHASE_2_HOOK: Complete implementation in Subphase 5.
"""

from flask import render_template, jsonify, g, redirect, url_for
from app.dashboard import dashboard_bp
from app.decorators import login_required, tenant_required, role_required
from app.constants import UserRole

# ============================================================================
# ROOT DASHBOARD
# ============================================================================

@dashboard_bp.route("", methods=["GET"])
@login_required
@tenant_required
def dashboard():
    """GET /dashboard - Route to role-specific dashboard."""
    # Redirect based on user role
    user_role = g.current_user.primary_role
    
    if user_role in [UserRole.TENANT_ADMIN.value, UserRole.SUPER_ADMIN.value]:
        return redirect(url_for("dashboard.owner_dashboard"))
    elif user_role == UserRole.BRANCH_MANAGER.value:
        return redirect(url_for("dashboard.branch_dashboard"))
    elif user_role in [UserRole.AGENT.value, UserRole.TELECALLER.value]:
        return redirect(url_for("dashboard.agent_dashboard"))
    else:
        # Default: show leads list
        return redirect(url_for("leads.list_leads"))

# ============================================================================
# OWNER DASHBOARD
# ============================================================================

@dashboard_bp.route("/owner", methods=["GET"])
@login_required
@tenant_required
@role_required(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)
def owner_dashboard():
    """GET /dashboard/owner - Tenant admin dashboard."""
    # PHASE_2_HOOK: Calculate tenant-wide KPIs
    return {"message": "Owner dashboard implementation pending"}, 200


# ============================================================================
# BRANCH MANAGER DASHBOARD
# ============================================================================

@dashboard_bp.route("/branch", methods=["GET"])
@login_required
@tenant_required
@role_required(UserRole.BRANCH_MANAGER)
def branch_dashboard():
    """GET /dashboard/branch - Branch manager dashboard."""
    # PHASE_2_HOOK: Calculate branch-specific KPIs
    return {"message": "Branch dashboard implementation pending"}, 200


# ============================================================================
# AGENT DASHBOARD
# ============================================================================

@dashboard_bp.route("/agent", methods=["GET"])
@login_required
@tenant_required
@role_required(UserRole.AGENT, UserRole.TELECALLER)
def agent_dashboard():
    """GET /dashboard/agent - Agent personal dashboard."""
    # PHASE_2_HOOK: Calculate agent-specific KPIs
    return {"message": "Agent dashboard implementation pending"}, 200


# ============================================================================
# PLATFORM DASHBOARD (Super Admin)
# ============================================================================

@dashboard_bp.route("/platform", methods=["GET"])
@login_required
@role_required(UserRole.SUPER_ADMIN)
def platform_dashboard():
    """GET /dashboard/platform - Platform admin dashboard."""
    # PHASE_3_HOOK: Multi-tenant usage, billing, error logs
    return {"message": "Platform dashboard implementation pending"}, 200
