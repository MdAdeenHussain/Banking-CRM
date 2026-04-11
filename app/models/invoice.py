"""Invoice Model"""
from app.extensions import db
from datetime import datetime
import uuid


class Invoice(db.Model):
    """Invoice Generation"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    lead_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False)
    invoice_type = db.Column(db.String(50), nullable=False)  # customer_charge, service_fee, commission, payout
    amount = db.Column(db.Float, nullable=False)
    gst_rate = db.Column(db.Float, default=18.0)
    gst_amount = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')  # pending, partial, completed
    payment_received_date = db.Column(db.DateTime, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)  # bank_transfer, cheque, cash, online
    notes = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref='invoices')