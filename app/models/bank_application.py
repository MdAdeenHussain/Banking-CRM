"""
LoanAxis CRM — Bank Application Model

Tracks individual bank/NBFC applications per lead.
A single lead can have multiple bank applications.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text

from app.models.base import BaseModel


APPLICATION_STATUSES = [
    "Pending", "Submitted", "Processing", "Approved", "Rejected",
]

PAYOUT_CYCLES = ["Monthly", "On Disbursal", "Quarterly"]

CORPORATE_PARTNERS = [
    "Andromeda", "DSA Direct", "Ruloans", "BankBazaar", "Other",
]


class BankApplication(BaseModel):
    """A bank/NBFC application submitted for a lead."""

    __tablename__ = "bank_applications"

    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)
    bank_partner_id = Column(
        String(36), ForeignKey("bank_partners.id"), nullable=True
    )

    # ── Application Details ─────────────────────────────────
    bank_name = Column(String(150), nullable=True)
    nbfc_name = Column(String(150), nullable=True)
    corporate_partner = Column(String(50), nullable=True)
    app_reference_number = Column(String(100), nullable=True)
    applied_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="Pending")

    # ── Commission Details ──────────────────────────────────
    commission_rate_pct = Column(Float, nullable=True)
    expected_commission = Column(Float, nullable=True)
    payout_cycle = Column(String(20), nullable=True)

    # ── Payout Tracking ─────────────────────────────────────
    payout_received_date = Column(DateTime(timezone=True), nullable=True)
    payout_amount_received = Column(Float, nullable=True, default=0.0)
    pending_payout = Column(Float, nullable=True, default=0.0)

    # ── Notes ───────────────────────────────────────────────
    remarks = Column(Text, nullable=True)

    # ── Relationships ───────────────────────────────────────
    from sqlalchemy.orm import relationship
    bank_partner = relationship("BankPartner", backref="applications")

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "lead_id": self.lead_id,
            "bank_partner_id": self.bank_partner_id,
            "bank_name": self.bank_name,
            "corporate_partner": self.corporate_partner,
            "app_reference_number": self.app_reference_number,
            "status": self.status,
            "commission_rate_pct": self.commission_rate_pct,
            "expected_commission": self.expected_commission,
            "payout_cycle": self.payout_cycle,
            "payout_amount_received": self.payout_amount_received,
            "pending_payout": self.pending_payout,
        })
        return base
