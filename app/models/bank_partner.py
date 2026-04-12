"""
LoanAxis CRM — Bank Partner Model

Represents banks, NBFCs, and corporate partners that the DSA works with.
"""

from sqlalchemy import Column, String, Boolean, Float, ForeignKey, Table

from app.extensions import db
from app.models.base import BaseModel


# ── Association table for User ↔ BankPartner (M2M) ──────────────
user_bank_partners = Table(
    "user_bank_partners",
    db.metadata,
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("bank_partner_id", String(36), ForeignKey("bank_partners.id"), primary_key=True),
)


class BankPartner(BaseModel):
    """A bank, NBFC, or corporate partner for loan distribution."""

    __tablename__ = "bank_partners"

    name = Column(String(150), nullable=False, unique=True)
    type = Column(String(20), nullable=False, default="Bank")  # Bank | NBFC | Corporate
    contact_person = Column(String(150), nullable=True)
    contact_mobile = Column(String(15), nullable=True)
    contact_email = Column(String(255), nullable=True)
    commission_rate_default_pct = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "name": self.name,
            "type": self.type,
            "contact_person": self.contact_person,
            "contact_mobile": self.contact_mobile,
            "commission_rate_default_pct": self.commission_rate_default_pct,
            "is_active": self.is_active,
        })
        return base
