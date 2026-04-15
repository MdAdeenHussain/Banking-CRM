"""LoanAxis CRM — Task Routes"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.tasks import tasks_bp
from app.blueprints.tasks.forms import TaskForm
from app.blueprints.tasks.services import create_task, mark_done, get_tasks_for_user
from app.models.user import User
from app.models.task import Task


@tasks_bp.route("/")
@login_required
def index():
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)
    pagination = get_tasks_for_user(current_user, status=status or None, page=page)
    return render_template("tasks/index.html", tasks=pagination.items, pagination=pagination,
                           current_status=status)


@tasks_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = TaskForm()
    users = User.query.filter_by(is_deleted=False, is_active_flag=True).all()
    form.assigned_to.choices = [(u.id, f"{u.full_name} ({u.employee_id})") for u in users]

    if form.validate_on_submit():
        task = create_task(
            data={f.name: f.data for f in form if f.name not in ("csrf_token", "submit")},
            created_by_id=current_user.id,
        )
        flash(f"Task '{task.title}' created!", "success")
        return redirect(url_for("tasks.index"))
    return render_template("tasks/new.html", form=form)


@tasks_bp.route("/<task_id>/complete", methods=["POST"])
@login_required
def complete(task_id):
    note = request.form.get("completion_note", "")
    mark_done(task_id, note)
    flash("Task marked as completed!", "success")
    return redirect(url_for("tasks.index"))
