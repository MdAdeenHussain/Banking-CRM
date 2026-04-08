"""Loan application model definition."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class Application(BaseModel):
    """Loan application entity."""

    __tablename__ = "applications"

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id = db.Column(db.BigInteger, db.ForeignKey("customers.id"), nullable=False, index=True)
    loan_type = db.Column(db.String(80), nullable=False)
    loan_amount = db.Column(db.Numeric(14, 2), nullable=False)
    status = db.Column(db.String(60), default="active", nullable=False)
    current_stage = db.Column(db.String(60), default="INITIATED", nullable=False)

    # =====================================
    # SECTION: Relationships
    # =====================================
    customer = db.relationship("Customer", back_populates="applications")

    # Future AI placeholders:
    # - underwriting_summary_placeholder
