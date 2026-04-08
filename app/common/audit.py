"""
app/common/audit.py
Audit logging model and utilities.
Every mutation (CREATE, UPDATE, DELETE) is logged here for compliance.
"""

from sqlalchemy.dialects.postgresql import UUID, JSON
from app.extensions import db
from app.common.mixins import BaseTenantModel
from app.constants import AuditAction
import json


class AuditLog(BaseTenantModel):
    """
    Immutable audit log table.
    Records every mutation for compliance and forensics.
    """
    __tablename__ = "audit_logs"

    # Override tenant_id with ForeignKey constraint
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Entity being modified
    entity_type = db.Column(
        db.String(100),
        nullable=False,
        index=True,
        comment="Table name or entity type (e.g. 'Lead', 'User')"
    )
    entity_id = db.Column(
        db.String(36),
        nullable=False,
        index=True,
        comment="ID of the entity being modified"
    )

    # Action details
    action = db.Column(
        db.String(50),
        nullable=False,
        index=True,
        comment="Action type: CREATE, UPDATE, DELETE, ASSIGN, STATUS_CHANGE"
    )

    # Old and new values (JSON)
    old_values = db.Column(
        JSON,
        nullable=True,
        comment="Previous values (for UPDATE/DELETE)"
    )
    new_values = db.Column(
        JSON,
        nullable=True,
        comment="New values (for CREATE/UPDATE)"
    )

    # Change reason (optional)
    reason = db.Column(
        db.String(500),
        nullable=True,
        comment="Human-readable reason for the change"
    )

    # Request tracking
    ip_address = db.Column(
        db.String(50),
        nullable=True,
        comment="Client IP address"
    )
    user_agent = db.Column(
        db.String(500),
        nullable=True,
        comment="Client user agent string"
    )

    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type}:{self.entity_id}>"

    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id),
            "action": self.action,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "reason": self.reason,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        })
        return data


# ============================================================================
# AUDIT LOG SERVICE
# ============================================================================
class AuditLogService:
    """
    Service for writing audit logs.
    
    PHASE_2_HOOK: Integrate with @audit_log decorator to automatically log mutations.
    """

    @staticmethod
    def log_action(
        tenant_id,
        user_id,
        entity_type,
        entity_id,
        action,
        old_values=None,
        new_values=None,
        reason=None,
        ip_address=None,
        user_agent=None
    ):
        """
        Write audit log entry.
        
        Args:
            tenant_id: Tenant UUID
            user_id: User UUID who made the change
            entity_type: Entity being changed (e.g. 'Lead')
            entity_id: ID of entity
            action: AuditAction enum
            old_values: Dict of old field values (for UPDATE/DELETE)
            new_values: Dict of new field values (for CREATE/UPDATE)
            reason: Human-readable reason
            ip_address: Client IP
            user_agent: Client user agent
        
        Returns:
            AuditLog instance
        """
        log = AuditLog(
            tenant_id=tenant_id,
            created_by=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action if isinstance(action, str) else action.value,
            old_values=old_values,
            new_values=new_values,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(log)
        db.session.commit()
        return log

    @staticmethod
    def list_entity_changes(entity_type, entity_id, tenant_id, limit=100):
        """
        Retrieve all changes to a specific entity.
        
        Args:
            entity_type: Entity type to search
            entity_id: Entity ID
            tenant_id: Tenant UUID
            limit: Maximum number of records
        
        Returns:
            List of AuditLog records
        """
        return AuditLog.query.filter_by(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            is_deleted=False
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def list_user_actions(user_id, tenant_id, limit=100):
        """
        Retrieve all actions by a specific user.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            limit: Maximum number of records
        
        Returns:
            List of AuditLog records
        """
        return AuditLog.query.filter_by(
            tenant_id=tenant_id,
            created_by=user_id,
            is_deleted=False
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
