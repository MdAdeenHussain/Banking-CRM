"""LoanAxis CRM — Notification Services"""
from app.extensions import db
from app.models.notification import Notification


def get_unread_count(user_id):
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def get_recent_notifications(user_id, limit=10):
    return Notification.query.filter_by(user_id=user_id).order_by(
        Notification.created_at.desc()).limit(limit).all()


def mark_all_read(user_id):
    from datetime import datetime, timezone
    Notification.query.filter_by(user_id=user_id, is_read=False).update({
        "is_read": True, "read_at": datetime.now(timezone.utc)
    })
    db.session.commit()
