"""Task Model"""
from app.extensions import db
from datetime import datetime
import uuid


class Task(db.Model):
    """Task Management"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=True, index=True)
    task_type = db.Column(db.String(50), nullable=False)  # customer_followup, pending_documents, payout_followup, emi_reminder, disbursal_confirmation
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assigned_to_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('employees.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    status = db.Column(db.String(20), default='open')  # open, in_progress, completed, overdue
    completed_at = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)