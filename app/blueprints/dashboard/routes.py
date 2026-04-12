"""
LoanAxis CRM — Dashboard Routes

Main dashboard with bento grid KPI cards, charts, and quick actions.
"""

from flask import render_template, jsonify
from flask_login import login_required, current_user

from app.blueprints.dashboard import dashboard_bp
from app.blueprints.dashboard.services import (
    get_kpi_data, get_recent_leads, get_tasks_due_today,
    get_pipeline_summary, get_monthly_lead_data,
)
from app.config.permissions import get_role_display_name


@dashboard_bp.route("/")
@login_required
def index():
    """Main dashboard page with bento grid layout."""
    kpi_data = get_kpi_data(current_user)
    recent_leads = get_recent_leads(current_user, limit=10)
    tasks_due = get_tasks_due_today(current_user)
    pipeline_summary = get_pipeline_summary(current_user)

    # Greeting based on time
    from datetime import datetime, timezone
    hour = datetime.now(timezone.utc).hour + 5  # IST offset
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    return render_template(
        "dashboard/index.html",
        kpi=kpi_data,
        recent_leads=recent_leads,
        tasks_due=tasks_due,
        pipeline_summary=pipeline_summary,
        greeting=greeting,
        role_display=get_role_display_name(current_user.role),
    )


@dashboard_bp.route("/api/kpi")
@login_required
def api_kpi():
    """JSON endpoint for KPI data (used by AJAX refresh)."""
    return jsonify(get_kpi_data(current_user))


@dashboard_bp.route("/api/pipeline-summary")
@login_required
def api_pipeline_summary():
    """JSON endpoint for pipeline funnel data."""
    return jsonify(get_pipeline_summary(current_user))


@dashboard_bp.route("/api/monthly-leads")
@login_required
def api_monthly_leads():
    """JSON endpoint for monthly lead chart data."""
    return jsonify(get_monthly_lead_data(current_user))
