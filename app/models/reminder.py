"""Reminder Model for Tasks"""
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import DateTime
from sqlalchemy.sql import func
import uuid


class Reminder(db.Model):
    """Task Reminders"""
    __tablename__ = 'reminders'
    
    id = db.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    task_id = db.Column(PGUUID(as_uuid=True), db.ForeignKey('tasks.id'), nullable=False)
    remind_at = db.Column(DateTime(timezone=True), nullable=False, index=True)
    reminded = db.Column(db.Boolean, default=False)
    reminder_type = db.Column(db.String(50), default='email')  # email, notification, sms
    created_at = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    task = db.relationship('Task', backref='reminders')
    
    def __repr__(self):
        return f'<Reminder {self.task_id}>'
