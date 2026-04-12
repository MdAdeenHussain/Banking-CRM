"""LoanAxis CRM — Commission Routes"""
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.blueprints.commissions import commissions_bp
from app.blueprints.commissions.forms import CommissionForm
from app.blueprints.commissions.services import create_commission, get_payout_summary
from app.models.commission import Commission
from app.models.lead import Lead
from app.utils.auth_helpers import require_permission


@commissions_bp.route("/")
@login_required
@require_permission("commissions.view")
def index():
    page = request.args.get("page", 1, type=int)
    query = Commission.query.filter(Commission.is_deleted == False)
    if current_user.role == "employee":
        query = query.filter(Commission.employee_id == current_user.id)
    pagination = query.order_by(Commission.created_at.desc()).paginate(page=page, per_page=25)
    summary = get_payout_summary(current_user)
    return render_template("commissions/index.html", commissions=pagination.items,
                           pagination=pagination, summary=summary)


@commissions_bp.route("/new/<lead_id>", methods=["GET", "POST"])
@login_required
@require_permission("commissions.view")
def new(lead_id):
    if current_user.role == "employee":
        abort(403)
    lead = Lead.query.get_or_404(lead_id)
    form = CommissionForm()
    if form.validate_on_submit():
        comm = create_commission(
            data={f.name: f.data for f in form if f.name not in ("csrf_token", "submit")},
            lead_id=lead_id,
            employee_id=lead.assigned_executive_id,
        )
        flash("Commission record created!", "success")
        return redirect(url_for("commissions.detail", commission_id=comm.id))
    return render_template("commissions/detail.html", form=form, lead=lead, commission=None)


@commissions_bp.route("/<commission_id>")
@login_required
@require_permission("commissions.view")
def detail(commission_id):
    comm = Commission.query.get_or_404(commission_id)
    if current_user.role == "employee" and comm.employee_id != current_user.id:
        abort(403)
    lead = Lead.query.get(comm.lead_id)
    return render_template("commissions/detail.html", commission=comm, lead=lead, form=None)
