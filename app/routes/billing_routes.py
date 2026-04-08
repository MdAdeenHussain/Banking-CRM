"""Billing module route controllers."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, render_template
from flask_login import login_required


# =====================================
# SECTION: Blueprint Definition
# =====================================
billing_bp = Blueprint("billing", __name__)


# =====================================
# SECTION: Billing Routes
# =====================================
@billing_bp.get("/billing")
@login_required
def billing_dashboard():
    return render_template("billing/billing_dashboard.html")
