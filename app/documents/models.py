"""Document intelligence domain models and constants.

This module keeps rule-based document pipeline constants in one place
so routes/services/tasks can share the same vocabulary.
"""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ==========================================
# SECTION: Core Logic
# ==========================================
class OCRStatus:
    """Allowed OCR processing states for documents."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class VerificationStatus:
    """Human verification workflow statuses."""

    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class FraudRiskLevel:
    """Fraud risk buckets derived from numeric fraud score."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class OCRExtractionResult:
    """Structured OCR output saved into `ocr_data_json`."""

    raw_text: str
    extracted_pan: str | None = None
    extracted_aadhaar: str | None = None
    salary_amount: float | None = None
    company_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe dictionary for DB storage."""
        return {
            "raw_text": self.raw_text,
            "extracted_pan": self.extracted_pan,
            "extracted_aadhaar": self.extracted_aadhaar,
            "salary_amount": self.salary_amount,
            "company_name": self.company_name,
            "metadata": self.metadata,
        }


# ==========================================
# SECTION: Validation
# ==========================================
ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}


# ==========================================
# SECTION: Fraud Checks
# ==========================================
FRAUD_FLAG_WEIGHTS = {
    "invalid_pan_format": 20,
    "invalid_aadhaar_format": 20,
    "salary_bank_mismatch": 25,
    "duplicate_file_hash": 25,
    "edited_pdf_metadata": 20,
    "image_tamper_suspected": 20,
}
