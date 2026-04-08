"""
app/common/mixins.py
Base mixins for all database models.
Every model in the system inherits from these to ensure consistent structure.
"""

from uuid import uuid4
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String
from app.extensions import db
from sqlalchemy import Index


def utcnow():
    """Get current UTC time."""
    return datetime.utcnow()


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps to a model.
    """
    created_at = db.Column(
        db.DateTime,
        default=utcnow,
        nullable=False,
        index=True
    )
    updated_at = db.Column(
        db.DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
        index=True
    )


class TenantMixin:
    """
    Mixin that adds tenant_id to a model for multi-tenant isolation.
    
    CRITICAL: All queries must filter by tenant_id to prevent cross-tenant data leaks.
    Example:
        Lead.query.filter_by(tenant_id=g.tenant_id).all()
    """
    tenant_id = db.Column(
        String(36),  # UUID as string for SQLite compatibility
        nullable=False,
        index=True
    )


class AuditMixin:
    """
    Mixin that adds audit and soft-delete fields to a model.
    """
    created_by = db.Column(
        String(36),  # UUID as string
        nullable=True,
        comment="User UUID who created this record"
    )
    updated_by = db.Column(
        String(36),  # UUID as string
        nullable=True,
        comment="User UUID who last updated this record"
    )
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Flag to disable record without deletion"
    )
    is_deleted = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Soft delete flag - always filter by is_deleted=False"
    )


class BaseTenantModel(db.Model):
    """
    Abstract base model for all tenant-scoped database tables.
    
    Automatically includes:
    - id (UUID primary key)
    - tenant_id (for multi-tenant isolation)
    - created_at, updated_at (timestamps)
    - created_by, updated_by (audit fields)
    - is_active, is_deleted (status flags)
    
    CRITICAL RULE:
    Every query must include .filter_by(tenant_id=g.tenant_id) or equivalent.
    This is MANDATORY for data isolation.
    
    Example model:
        class Lead(BaseTenantModel):
            __tablename__ = "leads"
            name = db.Column(db.String(255), nullable=False)
    
    Example query:
        leads = Lead.query.filter_by(tenant_id=g.tenant_id, is_deleted=False).all()
    """
    __abstract__ = True

    # Primary Key - use String for SQLite compatibility
    id = db.Column(
        String(36),  # UUID as string for SQLite compatibility
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    # Mixins
    # Inherit timestamp fields
    created_at = db.Column(
        db.DateTime,
        default=utcnow,
        nullable=False,
        index=True
    )
    updated_at = db.Column(
        db.DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
        index=True
    )

    # Tenant isolation - use String for SQLite compatibility
    tenant_id = db.Column(
        String(36),  # UUID as string for SQLite compatibility
        nullable=False,
        index=True
    )

    # Audit fields - use String for SQLite compatibility
    created_by = db.Column(
        String(36),  # UUID as string
        nullable=True
    )
    updated_by = db.Column(
        String(36),  # UUID as string
        nullable=True
    )

    # Status flags
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        index=True
    )
    is_deleted = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )

    def to_dict(self):
        """
        Convert model instance to dictionary (for JSON serialization).
        Override in subclasses for custom serialization.
        """
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "is_active": self.is_active,
            "is_deleted": self.is_deleted,
        }

    def __repr__(self):
        """String representation for debugging."""
        return f"<{self.__class__.__name__} id={self.id} tenant_id={self.tenant_id}>"
