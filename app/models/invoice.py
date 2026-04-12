"""
LoanAxis CRM — Invoice Model

GST-compliant invoice generation for commission payouts.
Line items stored as JSON for flexible schema.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


PAYMENT_STATUSES = ["Unpaid", "Partial", "Paid"]


class Invoice(BaseModel):
    """A GST-compliant invoice for commission payouts."""

    __tablename__ = "invoices"

    # ── Invoice Identity ────────────────────────────────────
    invoice_number = Column(String(30), unique=True, nullable=False)
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)

    # ── Party Details ───────────────────────────────────────
    party_name = Column(String(200), nullable=False)
    party_address = Column(Text, nullable=True)
    party_gstin = Column(String(15), nullable=True)

    # ── Line Items (JSONB) ──────────────────────────────────
    # Format: [{"description": str, "hsn_sac": str, "qty": int,
    #           "rate": float, "amount": float}]
    line_items = Column(JSON, nullable=False, default=list)

    # ── Totals ──────────────────────────────────────────────
    subtotal = Column(Float, nullable=False, default=0.0)
    cgst_rate = Column(Float, nullable=True, default=9.0)
    cgst_amount = Column(Float, nullable=True, default=0.0)
    sgst_rate = Column(Float, nullable=True, default=9.0)
    sgst_amount = Column(Float, nullable=True, default=0.0)
    igst_rate = Column(Float, nullable=True, default=0.0)
    igst_amount = Column(Float, nullable=True, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    amount_in_words = Column(String(500), nullable=True)

    # ── Payment ─────────────────────────────────────────────
    payment_status = Column(String(20), nullable=False, default="Unpaid")
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(200), nullable=True)
    paid_date = Column(DateTime(timezone=True), nullable=True)

    # ── Notes ───────────────────────────────────────────────
    notes = Column(Text, nullable=True)

    # ── Meta ────────────────────────────────────────────────
    generated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    commission_id = Column(String(36), nullable=True)  # Not FK to avoid circular
    pdf_path = Column(String(500), nullable=True)

    # ── Relationships ───────────────────────────────────────
    generator = relationship("User", foreign_keys=[generated_by])

    def calculate_totals(self) -> None:
        """Calculate subtotal and GST amounts from line items."""
        items = self.line_items or []
        self.subtotal = round(sum(item.get("amount", 0) for item in items), 2)

        # Determine GST type (CGST+SGST for intra-state, IGST for inter-state)
        if self.igst_rate and self.igst_rate > 0:
            self.igst_amount = round(self.subtotal * self.igst_rate / 100, 2)
            self.cgst_amount = 0.0
            self.sgst_amount = 0.0
            self.total_amount = round(self.subtotal + self.igst_amount, 2)
        else:
            self.cgst_amount = round(self.subtotal * (self.cgst_rate or 0) / 100, 2)
            self.sgst_amount = round(self.subtotal * (self.sgst_rate or 0) / 100, 2)
            self.igst_amount = 0.0
            self.total_amount = round(
                self.subtotal + self.cgst_amount + self.sgst_amount, 2
            )

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "party_name": self.party_name,
            "party_gstin": self.party_gstin,
            "subtotal": self.subtotal,
            "total_amount": self.total_amount,
            "payment_status": self.payment_status,
            "line_items": self.line_items,
        })
        return base
