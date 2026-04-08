"""Task package exports for Celery workers."""

from app.documents.tasks import process_document_ocr
from tasks.celery_app import celery_app

try:
    from tasks.ml_tasks import weekly_model_retraining
except Exception:  # pragma: no cover - optional import guard for local setups
    weekly_model_retraining = None

__all__ = ["celery_app", "process_document_ocr", "weekly_model_retraining"]
