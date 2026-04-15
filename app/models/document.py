import secrets

from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db
from app.models.base import BaseModel


DOCUMENT_TYPES = [
    "Aadhaar",
    "PAN",
    "Passport Photo",
    "Salary Slips",
    "Bank Statements",
    "ITR",
    "Form 16",
    "Business Proof",
    "Property Docs",
    "Sanction Letter",
    "Disbursal Proof",
    "Loan Account Letter",
    "NOC",
    "Agreement",
    "Other",
]


class Document(BaseModel):
    """A document uploaded for a lead, with versioning and verification."""

    __tablename__ = "documents"

    lead_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("leads.id"),
        nullable=False,
        index=True,
    )
    document_type = db.Column(
        db.Enum(*DOCUMENT_TYPES, name="doc_type_enum"),
        nullable=False,
    )
    custom_label = db.Column(db.String(100), nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    file_size_kb = db.Column(db.Float, nullable=True)
    version_number = db.Column(db.Integer, default=1, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verified_by = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
    )
    verification_date = db.Column(db.DateTime(timezone=True), nullable=True)
    expiry_date = db.Column(db.DateTime(timezone=True), nullable=True)
    uploaded_by = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
    )
    uploaded_at = db.Column(db.DateTime(timezone=True), nullable=True)
    access_token = db.Column(db.String(64), unique=True, nullable=False)

    uploader = db.relationship("User", foreign_keys=[uploaded_by])
    verifier = db.relationship("User", foreign_keys=[verified_by])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.access_token:
            self.access_token = secrets.token_urlsafe(48)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "lead_id": str(self.lead_id),
                "document_type": self.document_type,
                "original_filename": self.original_filename,
                "mime_type": self.mime_type,
                "file_size_kb": self.file_size_kb,
                "version_number": self.version_number,
                "is_verified": self.is_verified,
                "access_token": self.access_token,
            }
        )
        return base
