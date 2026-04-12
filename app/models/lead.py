"""
LoanAxis CRM — Lead & LeadStatusHistory Models

Core CRM entity: a customer lead with full loan application data,
pipeline tracking, and assignment management.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Boolean, Float, Integer, DateTime,
    ForeignKey, Text, Index,
)
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import BaseModel


# ── Enum-like constants (stored as strings for SQLite compat) ───

LOAN_TYPES = [
    "Personal", "Business", "Home", "Mortgage", "LAP",
    "Credit Card", "Vehicle", "Education", "Top-up",
]

PIPELINE_STAGES = [
    "New Lead", "Contacted", "Docs Pending", "Docs Received",
    "Bank Login Done", "Sanctioned", "Disbursed", "Rejected", "Closed",
]

PIPELINE_STAGE_COLORS = {
    "New Lead": "gray",
    "Contacted": "blue",
    "Docs Pending": "amber",
    "Docs Received": "indigo",
    "Bank Login Done": "purple",
    "Sanctioned": "teal",
    "Disbursed": "green",
    "Rejected": "red",
    "Closed": "dark",
}

PRIORITY_TAGS = ["Hot", "Warm", "Cold"]

LEAD_SOURCES = [
    "Walk-in", "Referral", "Online Portal", "Cold Call",
    "WhatsApp", "Social Media", "Corporate Tie-up", "Other",
]


class Lead(BaseModel):
    """
    A customer lead in the loan distribution pipeline.

    Tracks personal info, loan details, assignment, and pipeline stage.
    Supports duplicate detection via (mobile_primary, loan_type) composite index.
    """

    __tablename__ = "leads"

    # ── Auto-generated lead number ──────────────────────────
    lead_number = Column(String(20), unique=True, nullable=False)

    # ── Customer Personal Info ──────────────────────────────
    customer_name = Column(String(200), nullable=False)
    mobile_primary = Column(String(15), nullable=False, index=True)
    mobile_alternate = Column(String(15), nullable=True)
    email = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    occupation = Column(String(100), nullable=True)
    employer_name = Column(String(200), nullable=True)
    monthly_income = Column(Float, nullable=True)
    annual_income = Column(Float, nullable=True)

    # ── CIBIL Score ─────────────────────────────────────────
    cibil_score = Column(Integer, nullable=True)

    # ── Loan Details ────────────────────────────────────────
    loan_type = Column(String(30), nullable=False, index=True)
    loan_amount_applied = Column(Float, nullable=True)
    bank_preferred = Column(String(150), nullable=True)

    # ── Lead Source & Priority ──────────────────────────────
    lead_source = Column(String(30), nullable=True)
    priority_tag = Column(String(10), nullable=True, default="Warm")
    is_high_value = Column(Boolean, default=False, nullable=False)

    # ── Duplicate Tracking ──────────────────────────────────
    is_duplicate = Column(Boolean, default=False, nullable=False)
    duplicate_of_lead_id = Column(String(36), ForeignKey("leads.id"), nullable=True)

    # ── Assignment ──────────────────────────────────────────
    assigned_executive_id = Column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    assigned_admin_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=True, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    # ── Pipeline ────────────────────────────────────────────
    pipeline_stage = Column(
        String(30), nullable=False, default="New Lead", index=True
    )
    stage_updated_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # ── Relationships ───────────────────────────────────────
    assigned_executive = relationship(
        "User", foreign_keys=[assigned_executive_id], backref="assigned_leads"
    )
    assigned_admin = relationship(
        "User", foreign_keys=[assigned_admin_id]
    )
    creator = relationship(
        "User", foreign_keys=[created_by]
    )
    branch = relationship("Branch", backref="leads")
    status_history = relationship(
        "LeadStatusHistory", backref="lead", lazy="dynamic",
        cascade="all, delete-orphan", order_by="LeadStatusHistory.changed_at.desc()"
    )
    financials = relationship(
        "ClientFinancial", backref="lead", uselist=False,
        cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document", backref="lead", lazy="dynamic",
        cascade="all, delete-orphan"
    )
    bank_applications = relationship(
        "BankApplication", backref="lead", lazy="dynamic",
        cascade="all, delete-orphan"
    )
    remarks = relationship(
        "Remark", backref="lead", lazy="dynamic",
        cascade="all, delete-orphan", order_by="Remark.created_at.desc()"
    )
    commissions = relationship(
        "Commission", backref="lead", lazy="dynamic",
        cascade="all, delete-orphan"
    )

    # ── Composite index for duplicate detection ─────────────
    __table_args__ = (
        Index("ix_leads_duplicate_check", "mobile_primary", "loan_type"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.lead_number:
            self.lead_number = self._generate_lead_number()
        # Auto-flag high value leads
        if self.loan_amount_applied and self.loan_amount_applied >= 5000000:
            self.is_high_value = True

    @staticmethod
    def _generate_lead_number() -> str:
        """Generate a unique lead number like LD-2026-XXXXX."""
        import random
        year = datetime.now().year
        return f"LD-{year}-{random.randint(10000, 99999)}"

    @property
    def cibil_color(self) -> str:
        """Return color indicator based on CIBIL score."""
        if not self.cibil_score:
            return "gray"
        if self.cibil_score >= 750:
            return "green"
        if self.cibil_score >= 650:
            return "yellow"
        return "red"

    @property
    def stage_color(self) -> str:
        """Return the color for the current pipeline stage."""
        return PIPELINE_STAGE_COLORS.get(self.pipeline_stage, "gray")

    @property
    def days_in_current_stage(self) -> int:
        """Calculate days since the last stage change."""
        if not self.stage_updated_at:
            ref = self.created_at
        else:
            ref = self.stage_updated_at
        if ref:
            delta = datetime.now(timezone.utc) - ref
            return delta.days
        return 0

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "lead_number": self.lead_number,
            "customer_name": self.customer_name,
            "mobile_primary": self.mobile_primary,
            "email": self.email,
            "city": self.city,
            "state": self.state,
            "loan_type": self.loan_type,
            "loan_amount_applied": self.loan_amount_applied,
            "cibil_score": self.cibil_score,
            "cibil_color": self.cibil_color,
            "lead_source": self.lead_source,
            "priority_tag": self.priority_tag,
            "is_high_value": self.is_high_value,
            "pipeline_stage": self.pipeline_stage,
            "stage_color": self.stage_color,
            "days_in_current_stage": self.days_in_current_stage,
            "assigned_executive_id": self.assigned_executive_id,
            "branch_id": self.branch_id,
            "is_active": self.is_active,
        })
        return base


class LeadStatusHistory(BaseModel):
    """Track every pipeline stage change for a lead."""

    __tablename__ = "lead_status_history"

    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)
    from_stage = Column(String(30), nullable=True)
    to_stage = Column(String(30), nullable=False)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    changed_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    note = Column(Text, nullable=True)

    # Relationships
    changer = relationship("User", foreign_keys=[changed_by])
