import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.extensions import db


class BaseModel(db.Model):
    """
    Abstract base model. Provides UUID PK, timestamps,
    and soft-delete for all child models.
    Uses PostgreSQL-native UUID and TIMESTAMPTZ.
    """

    __abstract__ = True

    id = db.Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    created_at = db.Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = db.Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    is_deleted = db.Column(
        Boolean,
        default=False,
        nullable=False,
    )
    deleted_at = db.Column(
        DateTime(timezone=True),
        nullable=True,
    )

    def soft_delete(self):
        """Mark record as deleted without removing from DB."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Return serializable dict of all columns."""
        result = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, uuid.UUID):
                val = str(val)
            elif isinstance(val, datetime):
                val = val.isoformat()
            result[col.name] = val
        return result
