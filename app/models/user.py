"""User model definition with authentication helpers."""

# =====================================
# SECTION: Imports
# =====================================
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class User(UserMixin, BaseModel):
    """Application user (owner, branch, agent, platform)."""

    __tablename__ = "users"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="agent", nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # =====================================
    # SECTION: Relationships
    # =====================================
    tenant = db.relationship("Tenant", back_populates="users")

    # =====================================
    # SECTION: Helper Methods
    # =====================================
    def set_password(self, raw_password: str) -> None:
        """Store hashed password (never plain text)."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verify supplied password against stored hash."""
        return check_password_hash(self.password_hash, raw_password)
