"""Customer module route controllers."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms import CustomerCreateForm
from app.services.customer_service import CustomerService


# =====================================
# SECTION: Blueprint Definition
# =====================================
customers_bp = Blueprint("customers", __name__)


# =====================================
# SECTION: Customer Routes
# =====================================
@customers_bp.get("/customers")
@login_required
def customers_list():
    customers = CustomerService.list_customers(current_user.tenant_id)
    return render_template("customers/customers_list.html", customers=customers)


@customers_bp.route("/customers/create", methods=["POST"])
@login_required
def customer_create():
    form = CustomerCreateForm()
    payload = {
        "full_name": form.full_name.data or request.form.get("full_name"),
        "mobile": form.mobile.data or request.form.get("mobile"),
        "email": form.email.data or request.form.get("email"),
        "occupation": form.occupation.data or request.form.get("occupation"),
        "monthly_income": form.monthly_income.data or request.form.get("monthly_income"),
        "existing_emis": form.existing_emis.data or request.form.get("existing_emis"),
        "pan": form.pan.data or request.form.get("pan"),
        "aadhaar": form.aadhaar.data or request.form.get("aadhaar"),
        "risk_score_placeholder": form.risk_score_placeholder.data or request.form.get("risk_score_placeholder"),
    }

    if not payload["full_name"] or not payload["mobile"]:
        flash("Full name and mobile are required.", "danger")
        return redirect(url_for("customers.customers_list"))

    CustomerService.create_customer(current_user.tenant_id, payload)
    flash("Customer created successfully.", "success")
    return redirect(url_for("customers.customers_list"))


@customers_bp.get("/customers/<int:customer_id>")
@login_required
def customer_profile(customer_id: int):
    customer = CustomerService.get_customer_profile(current_user.tenant_id, customer_id)
    return render_template("customers/customer_profile.html", customer=customer)
