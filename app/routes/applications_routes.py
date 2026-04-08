"""Application module route controllers."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.services.application_service import ApplicationService


# =====================================
# SECTION: Blueprint Definition
# =====================================
applications_bp = Blueprint("applications", __name__)


# =====================================
# SECTION: Application Routes
# =====================================
@applications_bp.get("/applications")
@login_required
def applications_list():
    applications = ApplicationService.list_applications(current_user.tenant_id)
    return render_template("applications/applications_list.html", applications=applications)


@applications_bp.get("/applications/workflow")
@login_required
def application_workflow():
    return render_template("applications/application_workflow.html")


@applications_bp.get("/eligibility")
@login_required
def eligibility_calculator():
    """Render eligibility calculator page."""
    return render_template("eligibility/eligibility_calculator.html")


@applications_bp.get("/lenders/compare")
@login_required
def lender_compare():
    """Render lender comparison page."""
    return render_template("lenders/lender_compare.html")
