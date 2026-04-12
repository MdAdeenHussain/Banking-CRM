"""
LoanAxis CRM — Lead Routes

CRUD operations, pipeline view, status updates, remarks, and timeline.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user

from app.blueprints.leads import leads_bp
from app.blueprints.leads.forms import LeadForm, StatusUpdateForm, RemarkForm
from app.blueprints.leads.services import (
    create_lead, update_lead, update_stage, get_pipeline_leads,
    get_filtered_leads, get_lead_timeline, add_remark,
)
from app.models.lead import Lead, LOAN_TYPES, PIPELINE_STAGES, LEAD_SOURCES, PRIORITY_TAGS
from app.models.user import User
from app.models.branch import Branch
from app.utils.auth_helpers import require_permission, check_lead_access
from app.utils.duplicate_check import check_duplicate_api


@leads_bp.route("/")
@login_required
@require_permission("leads.create")
def index():
    """Lead list view with advanced filtering."""
    filters = {
        "search": request.args.get("search", ""),
        "pipeline_stage": request.args.get("pipeline_stage", ""),
        "loan_type": request.args.get("loan_type", ""),
        "priority_tag": request.args.get("priority_tag", ""),
        "lead_source": request.args.get("lead_source", ""),
        "assigned_executive_id": request.args.get("assigned_executive_id", ""),
        "date_from": request.args.get("date_from", ""),
        "date_to": request.args.get("date_to", ""),
        "city": request.args.get("city", ""),
        "sort_by": request.args.get("sort_by", "created_at"),
        "sort_dir": request.args.get("sort_dir", "desc"),
    }

    page = request.args.get("page", 1, type=int)
    pagination = get_filtered_leads(current_user, filters, page=page)

    # Get executives for filter dropdown
    executives = User.query.filter_by(
        is_deleted=False, is_active=True
    ).order_by(User.full_name).all()

    return render_template(
        "leads/index.html",
        leads=pagination.items,
        pagination=pagination,
        filters=filters,
        executives=executives,
        loan_types=LOAN_TYPES,
        pipeline_stages=PIPELINE_STAGES,
        lead_sources=LEAD_SOURCES,
        priority_tags=PRIORITY_TAGS,
    )


@leads_bp.route("/pipeline")
@login_required
@require_permission("leads.create")
def pipeline():
    """Kanban pipeline view."""
    pipeline_data = get_pipeline_leads(current_user)

    return render_template(
        "leads/pipeline.html",
        pipeline=pipeline_data,
        pipeline_stages=PIPELINE_STAGES,
    )


@leads_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_permission("leads.create")
def new():
    """Create a new lead."""
    form = LeadForm()

    # Populate executive and branch dropdowns
    executives = User.query.filter_by(is_deleted=False, is_active=True).all()
    form.assigned_executive_id.choices = [("", "Auto-assign")] + [
        (u.id, f"{u.full_name} ({u.employee_id})") for u in executives
    ]
    branches = Branch.query.filter_by(is_active=True, is_deleted=False).all()
    form.branch_id.choices = [("", "Select Branch")] + [
        (b.id, b.name) for b in branches
    ]

    if form.validate_on_submit():
        data = {
            "customer_name": form.customer_name.data,
            "mobile_primary": form.mobile_primary.data,
            "mobile_alternate": form.mobile_alternate.data,
            "email": form.email.data,
            "city": form.city.data,
            "state": form.state.data,
            "pincode": form.pincode.data,
            "occupation": form.occupation.data,
            "employer_name": form.employer_name.data,
            "monthly_income": form.monthly_income.data,
            "annual_income": form.annual_income.data,
            "cibil_score": form.cibil_score.data,
            "loan_type": form.loan_type.data,
            "loan_amount_applied": form.loan_amount_applied.data,
            "bank_preferred": form.bank_preferred.data,
            "lead_source": form.lead_source.data,
            "priority_tag": form.priority_tag.data,
            "assigned_executive_id": form.assigned_executive_id.data or None,
            "branch_id": form.branch_id.data or None,
            "override_duplicate": form.override_duplicate.data,
        }

        lead, warning = create_lead(data, current_user)

        if lead is None:
            flash(warning, "warning")
            return render_template("leads/new.html", form=form)

        if warning:
            flash(warning, "warning")

        flash(f"Lead #{lead.lead_number} created successfully!", "success")
        return redirect(url_for("leads.detail", lead_id=lead.id))

    return render_template("leads/new.html", form=form)


@leads_bp.route("/<lead_id>")
@login_required
def detail(lead_id):
    """Lead detail page with timeline."""
    lead = Lead.query.get_or_404(lead_id)

    if not check_lead_access(lead, "view"):
        abort(403)

    timeline = get_lead_timeline(lead_id)
    status_form = StatusUpdateForm(pipeline_stage=lead.pipeline_stage)
    remark_form = RemarkForm()

    return render_template(
        "leads/detail.html",
        lead=lead,
        timeline=timeline,
        status_form=status_form,
        remark_form=remark_form,
        pipeline_stages=PIPELINE_STAGES,
    )


@leads_bp.route("/<lead_id>/edit", methods=["GET", "POST"])
@login_required
def edit(lead_id):
    """Edit an existing lead."""
    lead = Lead.query.get_or_404(lead_id)

    if not check_lead_access(lead, "update"):
        abort(403)

    form = LeadForm(obj=lead)

    # Populate dropdowns
    executives = User.query.filter_by(is_deleted=False, is_active=True).all()
    form.assigned_executive_id.choices = [("", "Unassigned")] + [
        (u.id, f"{u.full_name} ({u.employee_id})") for u in executives
    ]
    branches = Branch.query.filter_by(is_active=True, is_deleted=False).all()
    form.branch_id.choices = [("", "Select Branch")] + [
        (b.id, b.name) for b in branches
    ]

    if form.validate_on_submit():
        data = {}
        for field in form:
            if field.name not in ("csrf_token", "submit", "override_duplicate", "duplicate_reason"):
                data[field.name] = field.data

        lead = update_lead(lead_id, data)
        flash("Lead updated successfully!", "success")
        return redirect(url_for("leads.detail", lead_id=lead.id))

    return render_template("leads/edit.html", form=form, lead=lead)


@leads_bp.route("/<lead_id>/status", methods=["POST"])
@login_required
def update_status(lead_id):
    """Update lead pipeline stage."""
    lead = Lead.query.get_or_404(lead_id)

    if not check_lead_access(lead, "update"):
        abort(403)

    form = StatusUpdateForm()
    if form.validate_on_submit():
        try:
            update_stage(lead_id, form.pipeline_stage.data, current_user, form.note.data)
            flash(f"Status updated to {form.pipeline_stage.data}.", "success")
        except ValueError as e:
            flash(str(e), "danger")

    return redirect(url_for("leads.detail", lead_id=lead_id))


@leads_bp.route("/<lead_id>/remark", methods=["POST"])
@login_required
def add_lead_remark(lead_id):
    """Add a remark or call note to a lead."""
    lead = Lead.query.get_or_404(lead_id)

    if not check_lead_access(lead, "update"):
        abort(403)

    form = RemarkForm()
    if form.validate_on_submit():
        data = {
            "remark_type": form.remark_type.data,
            "content": form.content.data,
            "call_duration_min": form.call_duration_min.data,
            "call_outcome": form.call_outcome.data,
        }
        add_remark(lead_id, data, current_user)
        flash("Remark added.", "success")

    return redirect(url_for("leads.detail", lead_id=lead_id))


@leads_bp.route("/api/duplicate-check", methods=["POST"])
@login_required
def api_duplicate_check():
    """AJAX endpoint for real-time duplicate detection."""
    data = request.get_json()
    mobile = data.get("mobile_primary", "")
    loan_type = data.get("loan_type", "")

    if not mobile or not loan_type:
        return jsonify({"is_duplicate": False})

    return jsonify(check_duplicate_api(mobile, loan_type))


@leads_bp.route("/api/stage-update", methods=["POST"])
@login_required
def api_stage_update():
    """AJAX endpoint for Kanban drag-and-drop stage updates."""
    data = request.get_json()
    lead_id = data.get("lead_id")
    new_stage = data.get("new_stage")

    if not lead_id or not new_stage:
        return jsonify({"error": "Missing required fields"}), 400

    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    if not check_lead_access(lead, "update"):
        return jsonify({"error": "Permission denied"}), 403

    try:
        update_stage(lead_id, new_stage, current_user)
        return jsonify({"success": True, "new_stage": new_stage})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
