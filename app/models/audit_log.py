"""Audit log model definition."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class AuditLog(BaseModel):
    """Stores sensitive activity traces for compliance and debugging."""

    __tablename__ = "audit_logs"

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(120), nullable=False)
    entity = db.Column(db.String(120), nullable=False)
    entity_id = db.Column(db.String(120), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(60), nullable=True)
