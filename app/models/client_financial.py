"""Client Financial Model"""
from app.extensions import db
from datetime import datetime
import uuid


class ClientFinancial(db.Model):
    """Client Financial Details"""
    __tablename__ = 'client_financials'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False, unique=True)
    loan_amount_sanctioned = db.Column(db.Float, nullable=True)
    loan_amount_disbursed = db.Column(db.Float, nullable=True)
    disbursed_date = db.Column(db.DateTime, nullable=True)
    loan_account_number = db.Column(db.String(50), unique=True, nullable=True, index=True)
    emi_amount = db.Column(db.Float, nullable=True)
    emi_start_date = db.Column(db.DateTime, nullable=True)
    loan_tenure = db.Column(db.Integer, nullable=True)  # in months
    interest_rate = db.Column(db.Float, nullable=True)  # percentage
    sanction_validity = db.Column(db.DateTime, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)