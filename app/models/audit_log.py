"""Audit Log Model"""
from app.extensions import db
from datetime import datetime
import uuid


class AuditLog(db.Model):
    """Audit Logs for Compliance"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)  # CREATE, READ, UPDATE, DELETE
    module = db.Column(db.String(50), nullable=False)  # leads, commissions, employees, etc.
    entity_id = db.Column(db.String(100), nullable=True)
    old_data = db.Column(db.JSON, nullable=True)
    new_data = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')