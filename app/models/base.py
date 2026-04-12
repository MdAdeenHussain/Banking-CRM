"""
LoanAxis CRM — Base Model Mixin

Provides UUID primary key, timestamps, and soft-delete functionality
inherited by all domain models.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.extensions import db


def generate_uuid():
    """Generate a new UUID4 string for use as primary key."""
    return str(uuid.uuid4())


class BaseModel(db.Model):
    """
    Abstract base model providing:
    - UUID primary key (string-based for SQLite compatibility)
    - created_at / updated_at timestamps
    - Soft delete (is_deleted + deleted_at)
    """

    __abstract__ = True

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def soft_delete(self):
        """Mark record as deleted without removing from database."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None

    def to_dict(self) -> dict:
        """
        Base dictionary representation.
        Subclasses should override and extend this.
        """
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"
