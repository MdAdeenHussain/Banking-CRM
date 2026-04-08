"""Tenant model definition.

A tenant represents one DSA organization in this multi-tenant SaaS.
"""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class Tenant(BaseModel):
    """Tenant workspace model."""

    __tablename__ = "tenants"

    company_name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    logo_url = db.Column(db.String(500), nullable=True)
    subscription_plan = db.Column(db.String(50), default="starter", nullable=False)
    primary_color = db.Column(db.String(20), default="#2563EB", nullable=False)

    # =====================================
    # SECTION: Relationships
    # =====================================
    users = db.relationship("User", back_populates="tenant", lazy="dynamic")

    # Future AI placeholders:
    # - ai_credit_balance
    # - model_provider_preferences
