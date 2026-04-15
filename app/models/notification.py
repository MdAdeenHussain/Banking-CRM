from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db
from app.models.base import BaseModel


NOTIFICATION_TYPES = [
    "lead_assigned",
    "lead_status_changed",
    "document_uploaded",
    "task_due_today",
    "task_overdue",
    "payout_received",
    "payout_pending",
    "commission_credited",
    "new_employee_joined",
    "login_from_new_device",
    "system",
    "info",
]


class Notification(BaseModel):
    """An in-app notification for a user."""

    __tablename__ = "notifications"

    user_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    type = db.Column(
        db.Enum(*NOTIFICATION_TYPES, name="notif_type_enum"),
        nullable=False,
        default="info",
    )
    title = db.Column(db.String(300), nullable=False)
    body = db.Column(db.Text, nullable=True)
    related_model = db.Column(db.String(50), nullable=True)
    related_id = db.Column(PGUUID(as_uuid=True), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def mark_read(self) -> None:
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)

    @property
    def icon(self) -> str:
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
        base.update(
            {
                "user_id": str(self.user_id),
                "type": self.type,
                "title": self.title,
                "body": self.body,
                "related_model": self.related_model,
                "related_id": str(self.related_id) if self.related_id else None,
                "is_read": self.is_read,
                "icon": self.icon,
            }
        )
        return base
