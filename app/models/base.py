"""Base model utilities.

All SQLAlchemy entities inherit from BaseModel to get shared columns
and helper behaviors used across the SaaS platform.
"""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db


# =====================================
# SECTION: Model Definition
# =====================================
class BaseModel(db.Model):
    """Abstract base model with common metadata columns."""

    __abstract__ = True

    id = db.Column(db.BigInteger, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # =====================================
    # SECTION: Helper Methods
    # =====================================
    def soft_delete(self) -> None:
        """Soft-delete helper for future archival workflows."""
        self.is_deleted = True
        self.is_active = False
