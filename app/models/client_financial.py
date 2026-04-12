"""
LoanAxis CRM — Client Financial Model

One-to-one with Lead, created after Sanctioned/Disbursed stage.
Stores sanctioned/disbursed loan details, EMI info, and processing fees.
"""

from sqlalchemy import Column, String, Boolean, Float, Integer, DateTime, ForeignKey, Text

from app.models.base import BaseModel


class ClientFinancial(BaseModel):
    """Financial details of a sanctioned/disbursed loan for a lead."""

    __tablename__ = "client_financials"

    lead_id = Column(
        String(36), ForeignKey("leads.id"),
        nullable=False, unique=True, index=True
    )

    # ── Loan Amounts ────────────────────────────────────────
    loan_amount_sanctioned = Column(Float, nullable=True)
    loan_amount_disbursed = Column(Float, nullable=True)
    disbursed_date = Column(DateTime(timezone=True), nullable=True)

    # ── Account Details ─────────────────────────────────────
    loan_account_number = Column(String(50), nullable=True, index=True)

    # ── EMI Details ─────────────────────────────────────────
    emi_amount = Column(Float, nullable=True)
    emi_start_date = Column(DateTime(timezone=True), nullable=True)
    loan_tenure_months = Column(Integer, nullable=True)
    interest_rate_pa = Column(Float, nullable=True)

    # ── Processing ──────────────────────────────────────────
    sanction_validity_date = Column(DateTime(timezone=True), nullable=True)
    processing_fee_charged = Column(Float, nullable=True)

    # ── Insurance ───────────────────────────────────────────
    insurance_taken = Column(Boolean, default=False, nullable=False)
    insurance_amount = Column(Float, nullable=True)

    # ── Notes ───────────────────────────────────────────────
    remarks = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "lead_id": self.lead_id,
            "loan_amount_sanctioned": self.loan_amount_sanctioned,
            "loan_amount_disbursed": self.loan_amount_disbursed,
            "disbursed_date": self.disbursed_date.isoformat() if self.disbursed_date else None,
            "loan_account_number": self.loan_account_number,
            "emi_amount": self.emi_amount,
            "loan_tenure_months": self.loan_tenure_months,
            "interest_rate_pa": self.interest_rate_pa,
            "insurance_taken": self.insurance_taken,
        })
        return base
