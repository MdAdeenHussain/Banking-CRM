"""Reminder Model for Tasks"""
from app.extensions import db
from datetime import datetime
import uuid


class Reminder(db.Model):
    """Task Reminders"""
    __tablename__ = 'reminders'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('tasks.id'), nullable=False)
    remind_at = db.Column(db.DateTime, nullable=False, index=True)
    reminded = db.Column(db.Boolean, default=False)
    reminder_type = db.Column(db.String(50), default='email')  # email, notification, sms
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    task = db.relationship('Task', backref='reminders')
    
    def __repr__(self):
        return f'<Reminder {self.task_id}>'
