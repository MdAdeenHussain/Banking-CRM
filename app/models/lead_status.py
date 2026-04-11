"""Lead Status Model"""
from app.extensions import db
from datetime import datetime
import uuid


class LeadStatus(db.Model):
    """Lead Status Pipeline"""
    __tablename__ = 'lead_statuses'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False, index=True)  # new_lead, contacted, documents_pending, documents_received, bank_login_done, sanctioned, disbursed, rejected, closed
    description = db.Column(db.Text, nullable=True)
    changed_by_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    changed_by = db.relationship('User', backref='status_changes')
    
    STATUS_CHOICES = [
        'new_lead',
        'contacted',
        'documents_pending',
        'documents_received',
        'bank_login_done',
        'sanctioned',
        'disbursed',
        'rejected',
        'closed'
    ]