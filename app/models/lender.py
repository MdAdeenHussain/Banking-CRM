"""Lender model definition."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class Lender(BaseModel):
    """Lender benchmark data per tenant."""

    __tablename__ = "lenders"

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    lender_name = db.Column(db.String(150), nullable=False)
    interest_rate = db.Column(db.Numeric(6, 3), nullable=True)
    approval_percentage = db.Column(db.Float, nullable=True)
    speed_score = db.Column(db.Float, nullable=True)
    ease_score = db.Column(db.Float, nullable=True)
