"""Dashboard route controllers for role-based screens."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, render_template
from flask_login import login_required

from app.decorators import role_required


# =====================================
# SECTION: Blueprint Definition
# =====================================
dashboard_bp = Blueprint("dashboard", __name__)


# =====================================
# SECTION: Dashboard Routes
# =====================================
@dashboard_bp.get("/dashboard/owner")
@role_required("owner", "platform")
def owner_dashboard():
    return render_template("dashboard/owner_dashboard.html")


@dashboard_bp.get("/dashboard/branch")
@role_required("branch", "owner", "platform")
def branch_dashboard():
    return render_template("dashboard/branch_dashboard.html")


@dashboard_bp.get("/dashboard/agent")
@role_required("agent", "branch", "owner", "platform")
def agent_dashboard():
    return render_template("dashboard/agent_dashboard.html")


@dashboard_bp.get("/dashboard/calls")
@login_required
def calls_dashboard():
    return render_template("dashboard/calls_dashboard.html")


@dashboard_bp.get("/dashboard/platform")
@role_required("platform", "owner")
def platform_dashboard():
    return render_template("dashboard/platform_dashboard.html")
