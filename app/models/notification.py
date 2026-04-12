"""
LoanAxis CRM — Notification Model

In-app notifications for lead assignments, status changes,
task reminders, payout updates, etc.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text

from app.models.base import BaseModel


NOTIFICATION_TYPES = [
    "lead_assigned", "lead_status_changed", "document_uploaded",
    "task_due_today", "task_overdue", "payout_received",
    "payout_pending", "commission_credited",
    "new_employee_joined", "login_from_new_device",
    "system", "info",
]


class Notification(BaseModel):
    """An in-app notification for a user."""

    __tablename__ = "notifications"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # ── Content ─────────────────────────────────────────────
    type = Column(String(40), nullable=False, default="info")
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=True)

    # ── Related Entity ──────────────────────────────────────
    related_model = Column(String(50), nullable=True)  # e.g., "lead", "task"
    related_id = Column(String(36), nullable=True)

    # ── Read State ──────────────────────────────────────────
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    def mark_read(self) -> None:
        """Mark notification as read."""
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)

    @property
    def icon(self) -> str:
        """Return Lucide icon name for notification type."""
        icons = {
            "lead_assigned": "user-plus",
            "lead_status_changed": "git-branch",
            "document_uploaded": "file-up",
            "task_due_today": "clock",
            "task_overdue": "alert-triangle",
            "payout_received": "indian-rupee",
            "payout_pending": "hourglass",
            "commission_credited": "wallet",
            "new_employee_joined": "user-check",
            "login_from_new_device": "shield-alert",
            "system": "settings",
            "info": "info",
        }
        return icons.get(self.type, "bell")

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "body": self.body,
            "related_model": self.related_model,
            "related_id": self.related_id,
            "is_read": self.is_read,
            "icon": self.icon,
        })
        return base
