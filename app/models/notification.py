"""Notification Model"""
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import DateTime
from sqlalchemy.sql import func
import uuid


class Notification(db.Model):
    """Notification Management"""
    __tablename__ = 'notifications'
    
    id = db.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    recipient_id = db.Column(PGUUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # task_assignment, commission_approval, etc
    read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(DateTime(timezone=True), nullable=True)
    action_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    recipient = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.title}>'
