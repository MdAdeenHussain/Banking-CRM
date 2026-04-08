"""Rule-based fraud detection heuristics for uploaded documents."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.documents.models import FRAUD_FLAG_WEIGHTS, FraudRiskLevel
from app.models.document import Document


# ==========================================
# SECTION: Core Logic
# ==========================================
class DocumentFraudEngine:
    """Runs deterministic fraud checks and computes fraud score."""

    PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id

    def run_all_checks(
        self,
        *,
        document: Document,
        ocr_data: dict[str, Any] | None = None,
        bank_statement_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute all fraud checks and return score + flags payload."""
        flags: dict[str, Any] = {}
        parsed = ocr_data or {}

        pan = parsed.get("extracted_pan")
        aadhaar = parsed.get("extracted_aadhaar")
        salary_slip = parsed.get("salary_amount")
        bank_salary = (bank_statement_data or {}).get("credited_salary")

        if pan and not self.verify_pan_format(pan):
            flags["invalid_pan_format"] = f"PAN format invalid: {pan}"

        if aadhaar and not self.verify_aadhaar_format(str(aadhaar)):
            flags["invalid_aadhaar_format"] = f"Aadhaar format invalid: {aadhaar}"

        if salary_slip is not None and bank_salary is not None and self.salary_mismatch(float(salary_slip), float(bank_salary)):
            flags["salary_bank_mismatch"] = (
                f"Salary mismatch exceeds 20% (slip={salary_slip}, bank={bank_salary})"
            )

        if self.duplicate_document(document.file_hash):
            flags["duplicate_file_hash"] = "Same file hash exists in current tenant."

        metadata_flag = self.check_pdf_metadata(document.file_path)
        if metadata_flag:
            flags["edited_pdf_metadata"] = metadata_flag

        if self.image_tamper_check(document.file_path):
            flags["image_tamper_suspected"] = "Basic image tamper heuristic triggered."

        score, risk_level = self.compute_fraud_score(flags)
        return {
            "fraud_score": score,
            "risk_level": risk_level,
            "flags": flags,
        }


# ==========================================
# SECTION: Validation
# ==========================================
    def verify_pan_format(self, pan: str) -> bool:
        """Regex validation for PAN format."""
        return bool(self.PAN_REGEX.match((pan or "").upper()))

    def verify_aadhaar_format(self, aadhaar: str) -> bool:
        """Validate Aadhaar as 12-digit numeric string."""
        value = (aadhaar or "").strip()
        return value.isdigit() and len(value) == 12


# ==========================================
# SECTION: Fraud Checks
# ==========================================
    def salary_mismatch(self, salary_slip: float, bank_statement: float) -> bool:
        """Flag mismatch when absolute difference >20% of salary slip."""
        if salary_slip <= 0:
            return False
        delta_ratio = abs(salary_slip - bank_statement) / salary_slip
        return delta_ratio > 0.20

    def duplicate_document(self, file_hash: str | None) -> bool:
        """Check if same hash already exists for tenant."""
        if not file_hash:
            return False

        query = Document.query.filter_by(
            tenant_id=self.tenant_id,
            file_hash=file_hash,
            is_deleted=False,
        )
        return query.count() > 1

    def check_pdf_metadata(self, file_path: str) -> str | None:
        """Basic PDF metadata heuristic.

        Rule-based placeholder:
        - if path implies pdf and filename contains edited/final_v* markers,
          treat as suspicious metadata indicator.
        """
        extension = Path(file_path or "").suffix.lower()
        name = Path(file_path or "").name.lower()

        if extension != ".pdf":
            return None

        suspicious_tokens = ["edited", "final_v", "scanfix", "modified"]
        if any(token in name for token in suspicious_tokens):
            return "PDF metadata heuristic flagged possible edited file."

        return None

    def image_tamper_check(self, file_path: str | None = None) -> bool:
        """Basic image tampering placeholder.

        Future versions can add ELA/frequency checks. Phase 5 keeps this
        deterministic and lightweight.
        """
        extension = Path(file_path or "").suffix.lower()
        if extension not in {".jpg", ".jpeg", ".png"}:
            return False

        name = Path(file_path or "").name.lower()
        return any(token in name for token in ["retouch", "photoshop", "edited"])

    def compute_fraud_score(self, flags: dict[str, Any]) -> tuple[int, str]:
        """Compute weighted fraud score (0-100) and risk level."""
        score = 0
        for flag_key in flags:
            score += int(FRAUD_FLAG_WEIGHTS.get(flag_key, 10))

        score = max(0, min(100, score))

        if score > 70:
            risk = FraudRiskLevel.HIGH
        elif score >= 40:
            risk = FraudRiskLevel.MEDIUM
        else:
            risk = FraudRiskLevel.LOW

        return score, risk
