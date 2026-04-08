"""Task package exports for Celery workers."""

from app.documents.tasks import process_document_ocr
from tasks.celery_app import celery_app

try:
    from tasks.ml_tasks import weekly_model_retraining
except Exception:  # pragma: no cover - optional import guard for local setups
    weekly_model_retraining = None

try:
    from app.automation_engine.celery_tasks import (
        daily_branch_summary,
        send_callback_alert,
        send_scheduled_reminder,
        stale_lead_reengagement,
    )
except Exception:  # pragma: no cover - optional import guard for local setups
    send_scheduled_reminder = None
    send_callback_alert = None
    daily_branch_summary = None
    stale_lead_reengagement = None

__all__ = [
    "celery_app",
    "process_document_ocr",
    "weekly_model_retraining",
    "send_scheduled_reminder",
    "send_callback_alert",
    "daily_branch_summary",
    "stale_lead_reengagement",
]
