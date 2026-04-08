"""Task package exports for Celery workers."""

from tasks.celery_app import celery_app

__all__ = ["celery_app"]
