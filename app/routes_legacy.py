"""Global route architecture for Phase 1.

All routes currently render static templates as the foundation layer.
Business rules and data-driven logic will be introduced in later phases.
"""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


# -----------------------------------------------------------------------------
# Public SaaS Website Routes
# -----------------------------------------------------------------------------
@main_bp.route("/")
def home():
    """Public landing page."""
    return render_template("public/index.html")


@main_bp.route("/features")
def features():
    """Public features page."""
    return render_template("public/features.html")


@main_bp.route("/pricing")
def pricing():
    """Public pricing page."""
    return render_template("public/pricing.html")


@main_bp.route("/solutions")
def solutions():
    """Public solutions page."""
    return render_template("public/solutions.html")


@main_bp.route("/security")
def security():
    """Public security & trust page."""
    return render_template("public/security.html")


@main_bp.route("/contact")
def contact():
    """Public contact page."""
    return render_template("public/contact.html")


@main_bp.route("/demo-booking")
def demo_booking():
    """Public demo booking page."""
    return render_template("public/demo_booking.html")


# -----------------------------------------------------------------------------
# Authentication Routes
# -----------------------------------------------------------------------------
@main_bp.route("/login")
def login():
    """Tenant/user login page."""
    return render_template("auth/login.html")


@main_bp.route("/register/tenant")
def register_tenant():
    """Tenant registration page."""
    return render_template("auth/register_tenant.html")


@main_bp.route("/register/user")
def register_user():
    """User registration page."""
    return render_template("auth/register_user.html")


# -----------------------------------------------------------------------------
# Dashboard Routes
# -----------------------------------------------------------------------------
@main_bp.route("/dashboard/owner")
def dashboard_owner():
    """Owner dashboard shell."""
    return render_template("dashboard/owner_dashboard.html")


@main_bp.route("/dashboard/branch")
def dashboard_branch():
    """Branch dashboard shell."""
    return render_template("dashboard/branch_dashboard.html")


@main_bp.route("/dashboard/agent")
def dashboard_agent():
    """Agent dashboard shell."""
    return render_template("dashboard/agent_dashboard.html")


@main_bp.route("/dashboard/calls")
def dashboard_calls():
    """Calls operations dashboard shell."""
    return render_template("dashboard/calls_dashboard.html")


@main_bp.route("/dashboard/platform")
def dashboard_platform():
    """Platform/super-admin dashboard shell."""
    return render_template("dashboard/platform_dashboard.html")


# -----------------------------------------------------------------------------
# CRM Core Routes
# -----------------------------------------------------------------------------
@main_bp.route("/leads")
def leads():
    """Lead management list page."""
    return render_template("leads/leads_list.html")


@main_bp.route("/customers")
def customers():
    """Customer management list page."""
    return render_template("customers/customers_list.html")
