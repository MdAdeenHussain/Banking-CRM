"""Lead Status Model"""
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import DateTime
from sqlalchemy.sql import func
import uuid


class LeadStatus(db.Model):
    """Lead Status Pipeline"""
    __tablename__ = 'lead_statuses'
    
    id = db.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    lead_id = db.Column(PGUUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False, index=True)  # new_lead, contacted, documents_pending, documents_received, bank_login_done, sanctioned, disbursed, rejected, closed
    description = db.Column(db.Text, nullable=True)
    changed_by_id = db.Column(PGUUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
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