"""Billing model definition."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class Billing(BaseModel):
    """Tenant subscription and billing status record."""

    __tablename__ = "billings"

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    plan_name = db.Column(db.String(80), nullable=False)
    monthly_amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(40), default="active", nullable=False)
    renewal_date = db.Column(db.Date, nullable=True)

    # Future AI placeholders:
    # - usage_prediction_placeholder
