"""Celery application foundation.

Provides Redis-backed Celery setup for asynchronous task execution.
"""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app import create_app


# ======================================
# SECTION: Core Service Logic
# ======================================
def make_celery() -> Celery:
    """Create and configure Celery instance from Flask config."""
    flask_app = create_app()

    celery_instance = Celery(
        "crm2_tasks",
        broker=flask_app.config["CELERY_BROKER_URL"],
        backend=flask_app.config["CELERY_RESULT_BACKEND"],
        include=[
            "tasks.lead_tasks",
            "tasks.notification_tasks",
            "tasks.ml_tasks",
            "app.documents.tasks",
            "app.automation_engine.celery_tasks",
        ],
    )

    celery_instance.conf.update(
        task_track_started=True,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        beat_schedule={
            # Weekly retraining architecture placeholder:
            # Runs every Sunday at 02:00 UTC.
            "weekly-model-retraining": {
                "task": "tasks.ml_tasks.weekly_model_retraining",
                "schedule": crontab(hour=2, minute=0, day_of_week="sunday"),
            },
            "send-scheduled-reminders": {
                "task": "app.automation_engine.celery_tasks.send_scheduled_reminder",
                "schedule": crontab(minute="*/15"),
            },
            "send-callback-alerts": {
                "task": "app.automation_engine.celery_tasks.send_callback_alert",
                "schedule": crontab(minute="*/30"),
            },
            "daily-branch-summary": {
                "task": "app.automation_engine.celery_tasks.daily_branch_summary",
                "schedule": crontab(hour=18, minute=0),
            },
            "stale-lead-reengagement": {
                "task": "app.automation_engine.celery_tasks.stale_lead_reengagement",
                "schedule": crontab(hour=9, minute=0),
            },
        },
    )

    class FlaskContextTask(celery_instance.Task):
        """Run each task inside Flask app context."""

        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_instance.Task = FlaskContextTask
    return celery_instance


celery_app = make_celery()


# ======================================
# SECTION: Helper Functions
# ======================================
# N/A for this module.


# ======================================
# SECTION: Calculators
# ======================================
# N/A for task bootstrap module.
