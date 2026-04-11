"""Bank Application Model"""
from app.extensions import db
from datetime import datetime
import uuid


class BankApplication(db.Model):
    """Bank/Corporate Application Form"""
    __tablename__ = 'bank_applications'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False, index=True)
    bank_name = db.Column(db.String(100), nullable=False, index=True)
    application_reference = db.Column(db.String(100), nullable=False, unique=True)
    commission_rate = db.Column(db.Float, nullable=False)  # percentage
    commission_amount = db.Column(db.Float, nullable=False)
    payout_cycle = db.Column(db.String(50), nullable=False)  # daily, weekly, monthly
    payout_pending = db.Column(db.Boolean, default=True)
    payout_received_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)