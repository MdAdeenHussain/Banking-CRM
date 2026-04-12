"""Audit Log Model"""
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy import DateTime
from sqlalchemy.sql import func
import uuid


class AuditLog(db.Model):
    """Audit Logs for Compliance"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = db.Column(PGUUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)  # CREATE, READ, UPDATE, DELETE
    module = db.Column(db.String(50), nullable=False)  # leads, commissions, employees, etc.
    entity_id = db.Column(db.String(100), nullable=True)
    old_data = db.Column(JSONB, nullable=True)
    new_data = db.Column(JSONB, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)