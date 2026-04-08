"""Lead module route controllers."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms import LeadCreateForm
from app.services.lead_service import LeadService


# =====================================
# SECTION: Blueprint Definition
# =====================================
leads_bp = Blueprint("leads", __name__)


# =====================================
# SECTION: Lead Routes
# =====================================
@leads_bp.get("/leads")
@login_required
def leads_list():
    leads = LeadService.list_leads(current_user.tenant_id)
    return render_template("leads/leads_list.html", leads=leads)


@leads_bp.route("/leads/create", methods=["GET", "POST"])
@login_required
def lead_create():
    form = LeadCreateForm()

    if request.method == "POST":
        payload = {
            "customer_name": form.customer_name.data or request.form.get("customer_name"),
            "mobile": form.mobile.data or request.form.get("mobile"),
            "email": form.email.data or request.form.get("email"),
            "loan_type": form.loan_type.data or request.form.get("loan_type"),
            "loan_amount": form.loan_amount.data or request.form.get("loan_amount"),
            "source": form.source.data or request.form.get("source"),
            "assigned_agent": form.assigned_agent.data or request.form.get("assigned_agent"),
        }

        if not payload["customer_name"] or not payload["mobile"]:
            flash("Customer name and mobile are required.", "danger")
            return render_template("leads/lead_create.html", form=form)

        LeadService.create_lead(current_user.tenant_id, payload)
        flash("Lead created successfully.", "success")
        return redirect(url_for("leads.leads_list"))

    return render_template("leads/lead_create.html", form=form)


@leads_bp.get("/leads/<int:lead_id>")
@login_required
def lead_detail(lead_id: int):
    # Placeholder detail view (template currently uses static mock data).
    return render_template("leads/lead_detail.html", lead_id=lead_id)


@leads_bp.get("/leads/pipeline")
@login_required
def lead_pipeline():
    pipeline = LeadService.get_pipeline_data(current_user.tenant_id)
    return render_template("leads/lead_pipeline.html", pipeline=pipeline)
