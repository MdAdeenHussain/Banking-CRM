"""Banking DSA CRM — Analytics Routes"""
from flask import render_template, jsonify
from flask_login import login_required
from app.blueprints.analytics import analytics_bp
from app.blueprints.analytics.services import (
    monthly_leads_data, conversion_funnel_data, lead_source_breakdown,
    loan_type_distribution, commission_trend_data, employee_performance_data,
    cibil_distribution,
)
from app.utils.auth_helpers import require_permission


@analytics_bp.route("/")
@login_required
@require_permission("analytics.view")
def index():
    return render_template("analytics/index.html")


@analytics_bp.route("/api/monthly-leads")
@login_required
def api_monthly_leads():
    return jsonify(monthly_leads_data())


@analytics_bp.route("/api/conversion-funnel")
@login_required
def api_conversion_funnel():
    return jsonify(conversion_funnel_data())


@analytics_bp.route("/api/lead-sources")
@login_required
def api_lead_sources():
    return jsonify(lead_source_breakdown())


@analytics_bp.route("/api/loan-types")
@login_required
def api_loan_types():
    return jsonify(loan_type_distribution())


@analytics_bp.route("/api/commission-trend")
@login_required
def api_commission_trend():
    return jsonify(commission_trend_data())


@analytics_bp.route("/api/employee-performance")
@login_required
def api_employee_performance():
    return jsonify(employee_performance_data())


@analytics_bp.route("/api/cibil-distribution")
@login_required
def api_cibil_distribution():
    return jsonify(cibil_distribution())
