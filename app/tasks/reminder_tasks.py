"""LoanAxis CRM — Reminder Celery Tasks"""
from datetime import datetime, timezone
from app.extensions import celery, db
from app.models.task import Task
from app.utils.notifications import notify_task_due


@celery.task(name="tasks.send_due_reminders")
def send_due_reminders():
    """Send notifications for tasks due today. Runs every 30 min via Celery Beat."""
    today = datetime.now(timezone.utc).date()
    tasks = Task.query.filter(
        Task.is_deleted == False, Task.due_date == today,
        Task.status != "Done", Task.reminder_sent == False,
    ).all()
    for task in tasks:
        notify_task_due(task, task.assigned_to)
        task.reminder_sent = True
        task.reminder_sent_at = datetime.now(timezone.utc)
    db.session.commit()
    return f"Sent {len(tasks)} reminders"


@celery.task(name="tasks.check_overdue_tasks")
def check_overdue_tasks():
    """Flag overdue tasks. Runs daily."""
    today = datetime.now(timezone.utc).date()
    overdue = Task.query.filter(
        Task.is_deleted == False, Task.due_date < today,
        Task.status.notin_(["Done", "Overdue"]),
    ).all()
    for task in overdue:
        task.status = "Overdue"
    db.session.commit()
    return f"Flagged {len(overdue)} overdue tasks"
