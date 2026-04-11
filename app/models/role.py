"""Role Model for RBAC"""
from app.extensions import db
from datetime import datetime
import uuid


class Role(db.Model):
    """Role Model for RBAC"""
    __tablename__ = 'roles'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)  # SUPER_ADMIN, ADMIN, EMPLOYEE
    description = db.Column(db.Text, nullable=True)
    permissions = db.Column(db.JSON, default={})  # JSON array of permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Default Permissions Structure
    SUPER_ADMIN_PERMS = {
        'users': ['create', 'read', 'update', 'delete'],
        'leads': ['create', 'read', 'update', 'delete'],
        'commissions': ['create', 'read', 'update', 'delete'],
        'employees': ['create', 'read', 'update', 'delete'],
        'admin': ['create', 'read', 'update', 'delete'],
        'analytics': ['read'],
        'reports': ['create', 'read', 'export'],
        'audit_logs': ['read'],
        'system_settings': ['update']
    }
    
    ADMIN_PERMS = {
        'leads': ['create', 'read', 'update'],
        'employees': ['read', 'update'],
        'commissions': ['read'],
        'reports': ['create', 'read', 'export'],
        'tasks': ['create', 'read', 'update']
    }
    
    EMPLOYEE_PERMS = {
        'leads': ['create', 'read', 'update'],
        'documents': ['upload', 'download'],
        'tasks': ['create', 'read', 'update'],
        'commissions': ['read']
    }
    
    def has_permission(self, module, action):
        """Check if role has permission"""
        return module in self.permissions and action in self.permissions[module]