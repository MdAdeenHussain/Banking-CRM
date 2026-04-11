"""Activity Log Model"""
from app.extensions import db
from datetime import datetime
import uuid


class ActivityLog(db.Model):
    """Activity Timeline"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False, index=True)
    activity_type = db.Column(db.String(100), nullable=False)  # status_change, document_upload, note_added, task_created
    description = db.Column(db.Text, nullable=False)
    created_by_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)