"""
LoanAxis CRM — Remark Model

Call notes, follow-up remarks, WhatsApp logs, and visit notes
attached to leads.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


REMARK_TYPES = ["General", "Call", "WhatsApp", "Email", "Visit"]

CALL_OUTCOMES = [
    "Connected", "No Answer", "Busy", "Switched Off",
    "Wrong Number", "Call Back Later", "Interested",
    "Not Interested", "Converted",
]


class Remark(BaseModel):
    """A remark or note attached to a lead."""

    __tablename__ = "remarks"

    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)

    # ── Content ─────────────────────────────────────────────
    remark_type = Column(String(20), nullable=False, default="General")
    content = Column(Text, nullable=False)

    # ── Call-specific fields ────────────────────────────────
    call_duration_min = Column(Integer, nullable=True)
    call_outcome = Column(String(30), nullable=True)

    # ── Author ──────────────────────────────────────────────
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    # ── Relationships ───────────────────────────────────────
    author = relationship("User", foreign_keys=[created_by])

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "lead_id": self.lead_id,
            "remark_type": self.remark_type,
            "content": self.content,
            "call_duration_min": self.call_duration_min,
            "call_outcome": self.call_outcome,
            "created_by": self.created_by,
        })
        return base
