"""LoanAxis CRM — Export Routes"""
from flask import Response, flash, redirect, url_for
from flask_login import login_required, current_user
from app.blueprints.exports import exports_bp
from app.blueprints.exports.services import export_leads, export_commissions, export_employees
from app.models.lead import Lead
from app.models.commission import Commission
from app.models.user import User
from app.utils.auth_helpers import require_role
from datetime import datetime


@exports_bp.route("/leads")
@login_required
@require_role("super_admin", "admin")
def leads_xlsx():
    leads = Lead.query.filter_by(is_deleted=False).all()
    output = export_leads(leads)
    date_str = datetime.now().strftime("%Y-%m-%d")
    return Response(output.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=leads_{date_str}.xlsx"})


@exports_bp.route("/commissions")
@login_required
@require_role("super_admin", "admin")
def commissions_csv():
    comms = Commission.query.filter_by(is_deleted=False).all()
    output = export_commissions(comms)
    date_str = datetime.now().strftime("%Y-%m-%d")
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=commissions_{date_str}.csv"})


@exports_bp.route("/employees")
@login_required
@require_role("super_admin")
def employees_xlsx():
    users = User.query.filter_by(is_deleted=False).all()
    output = export_employees(users)
    date_str = datetime.now().strftime("%Y-%m-%d")
    return Response(output.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=employees_{date_str}.xlsx"})
