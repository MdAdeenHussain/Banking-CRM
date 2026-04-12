"""LoanAxis CRM — Notification Celery Tasks"""
from app.extensions import celery, db
from app.utils.notifications import create_notification


@celery.task(name="tasks.bulk_notify")
def bulk_notify(user_ids, title, body, notification_type="info"):
    """Send notifications to multiple users."""
    for uid in user_ids:
        create_notification(uid, title, body, notification_type)
    db.session.commit()
    return f"Notified {len(user_ids)} users"
