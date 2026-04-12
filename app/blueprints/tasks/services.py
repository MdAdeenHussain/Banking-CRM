"""LoanAxis CRM — Task Services"""
from datetime import datetime, timezone
from app.extensions import db
from app.models.task import Task
from app.models.user import User


def create_task(data, created_by_id):
    task = Task(
        task_type=data["task_type"], title=data["title"],
        description=data.get("description"), lead_id=data.get("lead_id") or None,
        assigned_to=data["assigned_to"], created_by=created_by_id,
        due_date=data["due_date"], due_time=data.get("due_time"),
        priority=data.get("priority", "Medium"),
    )
    db.session.add(task)
    db.session.commit()
    return task


def mark_done(task_id, note=None):
    task = Task.query.get_or_404(task_id)
    task.mark_complete(note)
    db.session.commit()
    return task


def get_due_today(user):
    today = datetime.now(timezone.utc).date()
    q = Task.query.filter(Task.is_deleted == False, Task.due_date == today, Task.status != "Done")
    if user.role == "employee":
        q = q.filter(Task.assigned_to == user.id)
    return q.all()


def get_tasks_for_user(user, status=None, page=1, per_page=25):
    q = Task.query.filter(Task.is_deleted == False)
    if user.role == "employee":
        q = q.filter(Task.assigned_to == user.id)
    if status:
        q = q.filter(Task.status == status)
    return q.order_by(Task.due_date.asc()).paginate(page=page, per_page=per_page, error_out=False)
