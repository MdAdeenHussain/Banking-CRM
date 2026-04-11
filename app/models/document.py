"""Document Model"""
from app.extensions import db
from datetime import datetime
import uuid


class Document(db.Model):
    """Document Management"""
    __tablename__ = 'documents'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=False, index=True)
    document_type = db.Column(db.String(50), nullable=False)  # sanction_letter, kyc, bank_statement, salary_slip, agreement, disbursal_proof, loan_account_letter
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    file_type = db.Column(db.String(20), nullable=False)  # pdf, jpg, png, doc, docx
    version = db.Column(db.Integer, default=1)
    uploaded_by_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verified_by_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])
    verified_by = db.relationship('User', foreign_keys=[verified_by_id])