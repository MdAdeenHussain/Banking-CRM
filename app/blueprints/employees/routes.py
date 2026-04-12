"""LoanAxis CRM — Employee Routes"""
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.blueprints.employees import employees_bp
from app.blueprints.employees.forms import EmployeeForm
from app.blueprints.employees.services import create_employee, get_performance_summary
from app.models.user import User
from app.models.branch import Branch
from app.config.permissions import get_manageable_roles, can_manage_role
from app.utils.auth_helpers import require_role


@employees_bp.route("/")
@login_required
@require_role("super_admin", "admin")
def index():
    query = User.query.filter(User.is_deleted == False)
    if current_user.role == "admin":
        query = query.filter(User.role == "employee")
        if current_user.branch_id:
            query = query.filter(User.branch_id == current_user.branch_id)
    employees = query.order_by(User.full_name).all()
    return render_template("employees/index.html", employees=employees)


@employees_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_role("super_admin", "admin")
def new():
    form = EmployeeForm()
    manageable = get_manageable_roles(current_user.role)
    form.role.choices = [(r, r.replace("_", " ").title()) for r in manageable]
    branches = Branch.query.filter_by(is_active=True, is_deleted=False).all()
    form.branch_id.choices = [("", "Select Branch")] + [(b.id, b.name) for b in branches]

    if form.validate_on_submit():
        if not can_manage_role(current_user.role, form.role.data):
            abort(403)
        try:
            user = create_employee(
                {f.name: f.data for f in form if f.name not in ("csrf_token", "submit")},
                created_by_id=current_user.id,
            )
            flash(f"Employee {user.full_name} ({user.employee_id}) created!", "success")
            return redirect(url_for("employees.index"))
        except ValueError as e:
            flash(str(e), "danger")
    return render_template("employees/new.html", form=form)


@employees_bp.route("/<user_id>")
@login_required
@require_role("super_admin", "admin")
def profile(user_id):
    user = User.query.get_or_404(user_id)
    perf = get_performance_summary(user_id)
    return render_template("employees/profile.html", employee=user, performance=perf)


@employees_bp.route("/<user_id>/deactivate", methods=["POST"])
@login_required
@require_role("super_admin", "admin")
def deactivate(user_id):
    from datetime import datetime, timezone
    from app.extensions import db
    user = User.query.get_or_404(user_id)
    if not can_manage_role(current_user.role, user.role):
        abort(403)
    user.is_active = False
    user.deactivated_at = datetime.now(timezone.utc)
    user.deactivation_reason = request.form.get("reason", "")
    db.session.commit()
    flash(f"{user.full_name} has been deactivated.", "warning")
    return redirect(url_for("employees.index"))
