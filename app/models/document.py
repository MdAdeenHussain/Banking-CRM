"""
LoanAxis CRM — Document Model

Manages file uploads per lead with versioning, verification tracking,
and secure token-based access.
"""

import secrets
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


DOCUMENT_TYPES = [
    "Aadhaar", "PAN", "Passport Photo", "Salary Slips",
    "Bank Statements", "ITR", "Form 16", "Business Proof",
    "Property Docs", "Sanction Letter", "Disbursal Proof",
    "Loan Account Letter", "NOC", "Agreement", "Other",
]


class Document(BaseModel):
    """A document uploaded for a lead, with versioning and verification."""

    __tablename__ = "documents"

    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)

    # ── Document Info ───────────────────────────────────────
    document_type = Column(String(50), nullable=False)
    custom_label = Column(String(100), nullable=True)  # For "Other" type
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size_kb = Column(Float, nullable=True)

    # ── Versioning ──────────────────────────────────────────
    version_number = Column(Integer, default=1, nullable=False)

    # ── Verification ────────────────────────────────────────
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)

    # ── Expiry (time-sensitive docs) ────────────────────────
    expiry_date = Column(DateTime(timezone=True), nullable=True)

    # ── Upload Info ─────────────────────────────────────────
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=True)

    # ── Secure Access Token ─────────────────────────────────
    access_token = Column(String(64), unique=True, nullable=False)

    # ── Relationships ───────────────────────────────────────
    uploader = relationship("User", foreign_keys=[uploaded_by])
    verifier = relationship("User", foreign_keys=[verified_by])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.access_token:
            self.access_token = secrets.token_urlsafe(48)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "lead_id": self.lead_id,
            "document_type": self.document_type,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "file_size_kb": self.file_size_kb,
            "version_number": self.version_number,
            "is_verified": self.is_verified,
            "access_token": self.access_token,
        })
        return base
