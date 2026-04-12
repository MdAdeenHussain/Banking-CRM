"""Banking DSA CRM — Admin Routes"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import BranchForm, SystemSettingsForm
from app.blueprints.admin.services import get_full_user_table, get_audit_logs, create_branch
from app.models.branch import Branch
from app.models.audit_log import AUDITED_TABLES
from app.utils.auth_helpers import require_role


@admin_bp.route("/users")
@login_required
@require_role("super_admin")
def users():
    all_users = get_full_user_table()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/audit-logs")
@login_required
@require_role("super_admin")
def audit_logs():
    page = request.args.get("page", 1, type=int)
    table_filter = request.args.get("table", "")
    action_filter = request.args.get("action", "")
    pagination = get_audit_logs(page, table_filter=table_filter or None, action_filter=action_filter or None)
    return render_template("admin/audit_logs.html", logs=pagination.items, pagination=pagination,
                           audited_tables=sorted(AUDITED_TABLES), current_table=table_filter,
                           current_action=action_filter)


@admin_bp.route("/branches", methods=["GET", "POST"])
@login_required
@require_role("super_admin")
def branches():
    form = BranchForm()
    if form.validate_on_submit():
        create_branch({f.name: f.data for f in form if f.name not in ("csrf_token", "submit")})
        flash("Branch created!", "success")
        return redirect(url_for("admin.branches"))
    all_branches = Branch.query.filter_by(is_deleted=False).all()
    return render_template("admin/branches.html", branches=all_branches, form=form)


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
@require_role("super_admin")
def settings():
    form = SystemSettingsForm()
    if form.validate_on_submit():
        flash("Settings saved!", "success")
    return render_template("admin/settings.html", form=form)
