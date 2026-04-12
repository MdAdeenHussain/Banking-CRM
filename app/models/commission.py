"""
LoanAxis CRM — Commission Model

Tracks commission splits per disbursed lead: gross, TDS deduction,
company/admin/employee shares, and payout status.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


PAYOUT_STATUSES = ["Pending", "Partial", "Received"]


class Commission(BaseModel):
    """Commission record for a disbursed lead."""

    __tablename__ = "commissions"

    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)
    bank_application_id = Column(
        String(36), ForeignKey("bank_applications.id"), nullable=True
    )

    # ── Gross Commission ────────────────────────────────────
    gross_commission = Column(Float, nullable=False, default=0.0)

    # ── TDS Deduction ───────────────────────────────────────
    tds_rate_pct = Column(Float, nullable=True, default=5.0)
    tds_amount = Column(Float, nullable=True, default=0.0)
    net_after_tds = Column(Float, nullable=True, default=0.0)

    # ── Company Share ───────────────────────────────────────
    company_share_pct = Column(Float, nullable=True, default=40.0)
    company_amount = Column(Float, nullable=True, default=0.0)

    # ── Admin Share ─────────────────────────────────────────
    admin_share_pct = Column(Float, nullable=True, default=20.0)
    admin_amount = Column(Float, nullable=True, default=0.0)

    # ── Employee Share ──────────────────────────────────────
    employee_share_pct = Column(Float, nullable=True, default=40.0)
    employee_amount = Column(Float, nullable=True, default=0.0)
    employee_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    # ── Payout Tracking ─────────────────────────────────────
    payout_status = Column(String(20), nullable=False, default="Pending")
    payout_received_date = Column(DateTime(timezone=True), nullable=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True)
    payment_reference = Column(String(200), nullable=True)

    # ── Notes ───────────────────────────────────────────────
    remarks = Column(Text, nullable=True)

    # ── Relationships ───────────────────────────────────────
    employee = relationship("User", foreign_keys=[employee_id], backref="commissions")
    bank_application = relationship("BankApplication", backref="commission")
    invoice = relationship("Invoice", backref="commissions")

    def calculate_splits(self) -> None:
        """
        Calculate all commission splits from gross commission.

        Flow: Gross → TDS deduction → Net split among company/admin/employee.
        """
        # TDS deduction
        self.tds_amount = round(self.gross_commission * (self.tds_rate_pct or 0) / 100, 2)
        self.net_after_tds = round(self.gross_commission - self.tds_amount, 2)

        # Split the net amount
        self.company_amount = round(
            self.net_after_tds * (self.company_share_pct or 0) / 100, 2
        )
        self.admin_amount = round(
            self.net_after_tds * (self.admin_share_pct or 0) / 100, 2
        )
        self.employee_amount = round(
            self.net_after_tds * (self.employee_share_pct or 0) / 100, 2
        )

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "lead_id": self.lead_id,
            "gross_commission": self.gross_commission,
            "tds_rate_pct": self.tds_rate_pct,
            "tds_amount": self.tds_amount,
            "net_after_tds": self.net_after_tds,
            "company_share_pct": self.company_share_pct,
            "company_amount": self.company_amount,
            "admin_share_pct": self.admin_share_pct,
            "admin_amount": self.admin_amount,
            "employee_share_pct": self.employee_share_pct,
            "employee_amount": self.employee_amount,
            "payout_status": self.payout_status,
            "employee_id": self.employee_id,
        })
        return base
