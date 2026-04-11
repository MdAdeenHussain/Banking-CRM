"""Audit Service for logging"""
from app.models.audit_log import AuditLog
from app.extensions import db
from datetime import datetime
import uuid


class AuditService:
    """Service for audit logging"""
    
    @staticmethod
    def log_action(user_id, action, resource, resource_id, details=''):
        """Log an action in the audit trail"""
        try:
            audit_log = AuditLog(
                id=uuid.uuid4(),
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=str(resource_id),
                details=details,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            return True
        
        except Exception as e:
            print(f"Audit log failed: {str(e)}")
            return False
    
    @staticmethod
    def get_audit_logs(resource=None, action=None, limit=100):
        """Get audit logs with optional filters"""
        query = AuditLog.query
        
        if resource:
            query = query.filter_by(resource=resource)
        
        if action:
            query = query.filter_by(action=action)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
