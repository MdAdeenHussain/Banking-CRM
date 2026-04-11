"""Commission Tracker Model"""
from app.extensions import db
from datetime import datetime
import uuid


class CommissionTracker(db.Model):
    """Commission Tracking"""
    __tablename__ = 'commission_trackers'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False, index=True)
    bank_application_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('bank_applications.id'), nullable=True)
    gross_commission = db.Column(db.Float, nullable=False)
    employee_share = db.Column(db.Float, nullable=False)
    admin_share = db.Column(db.Float, nullable=False)
    company_share = db.Column(db.Float, nullable=False)
    net_payout = db.Column(db.Float, nullable=False)
    is_pending = db.Column(db.Boolean, default=True, index=True)
    payoff_date = db.Column(db.DateTime, nullable=True)
    received_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)