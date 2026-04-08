"""Notification model definition."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class Notification(BaseModel):
    """User notification records (email, sms, whatsapp, in-app)."""

    __tablename__ = "notifications"

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    channel = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(40), default="QUEUED", nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
