"""
app/customers/models.py
Customer model for KYC and 360-degree customer view.
"""

from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import Index, UniqueConstraint
from app.extensions import db
from app.common.mixins import BaseTenantModel, utcnow
from uuid import uuid4


class Customer(BaseTenantModel):
    """
    Customer (KYC) profile - unified 360-degree view.
    Linked to leads and applications.
    """
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "pan", name="uq_customer_tenant_pan"),
        UniqueConstraint("tenant_id", "mobile", name="uq_customer_tenant_mobile"),
        Index("idx_customer_pan", "pan"),
        Index("idx_customer_mobile", "mobile"),
    )

    # Override tenant_id with ForeignKey constraint
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Identity
    name = db.Column(db.String(255), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    
    # KYC Documents
    pan = db.Column(
        db.String(20),
        nullable=False,
        comment="PAN number (unique per tenant)"
    )
    aadhaar = db.Column(
        db.String(20),
        nullable=True,
        comment="Aadhaar number (masked in logs)"
    )
    
    # Address
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    
    # Employment
    occupation = db.Column(
        db.String(100),
        nullable=True,
        comment="Job title or occupation"
    )
    employer = db.Column(
        db.String(255),
        nullable=True,
        comment="Company/employer name"
    )
    employment_type = db.Column(
        db.String(50),
        nullable=True,
        comment="SALARIED, SELF_EMPLOYED, BUSINESS, STUDENT, HOMEMAKER, etc."
    )
    
    # Income & Liabilities
    monthly_income = db.Column(
        db.Numeric(15, 2),
        nullable=True,
        comment="Monthly net income"
    )
    existing_emis = db.Column(
        db.Numeric(15, 2),
        nullable=True,
        comment="Total monthly EMI obligations"
    )
    liabilities = db.Column(
        JSON,
        nullable=True,
        comment="Existing loans/liabilities details"
    )
    
    # Credit Info
    credit_score = db.Column(
        db.Integer,
        nullable=True,
        comment="CIBIL or other bureau credit score"
    )
    bureau_checked_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="When bureau was last pulled"
    )
    
    # Verification Status
    kyc_status = db.Column(
        db.String(50),
        default="PENDING",
        comment="PENDING, VERIFIED, REJECTED, EXPIRED"
    )
    kyc_verified_at = db.Column(db.DateTime, nullable=True)
    
    # Additional Info
    custom_data = db.Column(
        JSON,
        nullable=True,
        comment="Additional flexible customer data"
    )

    def __repr__(self):
        return f"<Customer {self.name} ({self.pan})>"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "name": self.name,
            "mobile": self.mobile,
            "email": self.email,
            "pan": self.pan,
            "aadhaar": self.aadhaar if self.aadhaar else None,  # Masked
            "city": self.city,
            "occupation": self.occupation,
            "employer": self.employer,
            "monthly_income": float(self.monthly_income) if self.monthly_income else None,
            "existing_emis": float(self.existing_emis) if self.existing_emis else None,
            "credit_score": self.credit_score,
            "kyc_status": self.kyc_status,
        })
        return data
