"""Customer model definition."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class Customer(BaseModel):
    """Customer profile for KYC and financial data."""

    __tablename__ = "customers"

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    pan = db.Column(db.String(20), nullable=True)
    aadhaar = db.Column(db.String(20), nullable=True)
    occupation = db.Column(db.String(120), nullable=True)
    monthly_income = db.Column(db.Numeric(14, 2), nullable=True)
    existing_emis = db.Column(db.Numeric(14, 2), nullable=True)
    risk_score_placeholder = db.Column(db.Float, nullable=True)

    # =====================================
    # SECTION: Relationships
    # =====================================
    applications = db.relationship("Application", back_populates="customer", lazy="dynamic")
