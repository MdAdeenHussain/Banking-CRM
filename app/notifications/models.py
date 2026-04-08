"""
app/notifications/models.py
Notification model for in-app alerts and notifications.
"""

from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import Index
from app.extensions import db
from app.common.mixins import BaseTenantModel, utcnow
from uuid import uuid4


class Notification(BaseTenantModel):
    """
    In-app notification for users.
    Supports various types: assignments, follow-ups, status changes, system messages.
    """
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notification_user", "user_id"),
        Index("idx_notification_read", "is_read"),
        Index("idx_notification_created", "created_at"),
    )

    # Override tenant_id with ForeignKey constraint
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Recipient user ID"
    )
    
    # Notification Content
    message = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Notification Type
    notification_type = db.Column(
        db.String(50),
        nullable=False,
        index=True,
        comment="ASSIGNMENT, FOLLOW_UP, STATUS_CHANGE, SYSTEM, ALERT"
    )
    
    # Related Entity (for linking)
    related_entity_type = db.Column(
        db.String(50),
        nullable=True,
        comment="Entity type: Lead, Application, etc."
    )
    related_entity_id = db.Column(
        db.String(36),
        nullable=True,
        comment="ID of related entity"
    )
    
    # Status
    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )
    read_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="When user read the notification"
    )
    
    # Priority
    priority = db.Column(
        db.String(20),
        default="NORMAL",
        comment="LOW, NORMAL, HIGH, URGENT"
    )
    
    # Additional Data
    custom_data = db.Column(
        JSON,
        nullable=True,
        comment="Additional data (action buttons, etc.)"
    )
    
    # Action URL
    action_url = db.Column(
        db.String(500),
        nullable=True,
        comment="URL to navigate when clicked"
    )

    # Relationships
    user = db.relationship("User", backref="notifications")

    def __repr__(self):
        return f"<Notification user={self.user_id} type={self.notification_type}>"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "user_id": str(self.user_id),
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "priority": self.priority,
            "action_url": self.action_url,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": str(self.related_entity_id) if self.related_entity_id else None,
        })
        return data
