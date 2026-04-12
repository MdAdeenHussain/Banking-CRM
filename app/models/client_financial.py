"""Client Financial Model"""
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import DateTime
from sqlalchemy.sql import func
import uuid


class ClientFinancial(db.Model):
    """Client Financial Details"""
    __tablename__ = 'client_financials'
    
    id = db.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    lead_id = db.Column(PGUUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False, unique=True)
    loan_amount_sanctioned = db.Column(db.Float, nullable=True)
    loan_amount_disbursed = db.Column(db.Float, nullable=True)
    disbursed_date = db.Column(DateTime(timezone=True), nullable=True)
    loan_account_number = db.Column(db.String(50), unique=True, nullable=True, index=True)
    emi_amount = db.Column(db.Float, nullable=True)
    emi_start_date = db.Column(DateTime(timezone=True), nullable=True)
    loan_tenure = db.Column(db.Integer, nullable=True)  # in months
    interest_rate = db.Column(db.Float, nullable=True)  # percentage
    sanction_validity = db.Column(DateTime(timezone=True), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)