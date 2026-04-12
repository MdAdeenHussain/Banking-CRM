"""User/Authentication Model"""
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import DateTime
from sqlalchemy.sql import func
import uuid


class User(db.Model):
    """User/Authentication Model"""
    __tablename__ = 'users'
    
    id = db.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_2fa_enabled = db.Column(db.Boolean, default=False)
    last_login = db.Column(DateTime(timezone=True), nullable=True)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    
    # Foreign Keys
    role_id = db.Column(PGUUID(as_uuid=True), db.ForeignKey('roles.id'), nullable=False)
    employee_id = db.Column(PGUUID(as_uuid=True), db.ForeignKey('employees.id'), nullable=True)
    
    # Relationships
    role = db.relationship('Role', backref='users')
    employee = db.relationship('Employee', backref='user', uselist=False)
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'full_name': self.full_name,
            'mobile': self.mobile,
            'role': self.role.name if self.role else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }