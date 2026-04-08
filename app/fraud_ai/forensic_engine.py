"""Advanced forensic document analysis for fraud detection."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.documents.fraud_engine import DocumentFraudEngine
from app.models.document import Document


# ==========================================
# SECTION: Fraud Detection
# ==========================================
class ForensicEngine:
    """Performs forensic checks on uploaded documents.

    This extends the Phase 5 rule engine with additional document,
    OCR, and salary-consistency checks.
    """

    FORENSIC_WEIGHTS = {
        "pdf_metadata": 15,
        "font_consistency": 10,
        "duplicate_hash": 20,
        "ocr_name_mismatch": 20,
        "salary_pattern": 20,
        "bank_statement_consistency": 15,
    }

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id
        self.base_engine = DocumentFraudEngine(tenant_id=tenant_id)

    def analyze_document(
        self,
        document: Document,
        *,
        bank_statement_data: dict[str, Any] | None = None,
        application_name: str | None = None,
    ) -> dict[str, Any]:
        """Run the full forensic document analysis pipeline."""
        flags: dict[str, str] = {}
        ocr_data = document.ocr_data_json or {}
        customer = document.customer
        linked_application_name = application_name
        if linked_application_name is None and getattr(document, "application", None) is not None:
            linked_application_name = getattr(document.application.customer, "full_name", None)

        metadata_issue = self.check_pdf_metadata(document.file_path)
        if metadata_issue:
            flags["pdf_metadata"] = metadata_issue

        font_issue = self.check_font_consistency(document)
        if font_issue:
            flags["font_consistency"] = font_issue

        if self.check_duplicate_hash(document.file_hash):
            flags["duplicate_hash"] = "Same document hash appears in multiple tenant records."

        mismatch_issue = self.check_ocr_mismatch(
            ocr_data=ocr_data,
            customer_name=getattr(customer, "full_name", None),
            application_name=linked_application_name,
        )
        if mismatch_issue:
            flags["ocr_name_mismatch"] = mismatch_issue

        salary_issue = self.check_salary_pattern(
            ocr_data=ocr_data,
            bank_statement_data=bank_statement_data or {},
        )
        if salary_issue:
            flags["salary_pattern"] = salary_issue

        bank_issue = self.check_bank_statement_consistency(bank_statement_data or {})
        if bank_issue:
            flags["bank_statement_consistency"] = bank_issue

        document_score = min(
            100,
            sum(self.FORENSIC_WEIGHTS.get(flag, 10) for flag in flags),
        )
        return {
            "document_score": int(document_score),
            "risk_level": self._risk_level(document_score),
            "flags": flags,
        }

    def check_pdf_metadata(self, file_path: str) -> str | None:
        """Check suspicious PDF metadata markers."""
        return self.base_engine.check_pdf_metadata(file_path)

    def check_font_consistency(self, document: Document) -> str | None:
        """Heuristic font consistency check.

        Since Phase 9 stays lightweight, we infer suspicious font edits
        from OCR metadata markers and filename hints.
        """
        metadata = (document.ocr_data_json or {}).get("metadata", {})
        raw_text = str((document.ocr_data_json or {}).get("raw_text", "")).lower()
        filename = Path(document.file_name or "").name.lower()

        if metadata.get("font_issue") is True:
            return "OCR metadata indicates mixed or inconsistent font usage."
        if any(token in filename for token in ["edited", "overlay", "patched"]):
            return "Filename heuristic suggests document overlay/editing."
        if "font changed" in raw_text or "retyped" in raw_text:
            return "OCR text suggests font replacement activity."
        return None

    def check_duplicate_hash(self, file_hash: str | None) -> bool:
        """Check duplicate file hash reuse."""
        return self.base_engine.duplicate_document(file_hash)

    def check_ocr_mismatch(
        self,
        *,
        ocr_data: dict[str, Any],
        customer_name: str | None,
        application_name: str | None,
    ) -> str | None:
        """Compare OCR names against customer and application names."""
        metadata = ocr_data.get("metadata", {})
        ocr_name_candidates = [
            metadata.get("pan_name"),
            metadata.get("aadhaar_name"),
            metadata.get("applicant_name"),
        ]
        normalized_candidates = {
            self._normalize_name(name)
            for name in ocr_name_candidates
            if self._normalize_name(name)
        }
        customer_value = self._normalize_name(customer_name)
        application_value = self._normalize_name(application_name)

        if not normalized_candidates:
            return None

        valid_targets = {value for value in [customer_value, application_value] if value}
        if not valid_targets:
            return None

        if normalized_candidates.isdisjoint(valid_targets):
            return (
                "OCR-extracted identity name does not match customer profile "
                "or linked application identity."
            )
        return None

    def check_salary_pattern(
        self,
        *,
        ocr_data: dict[str, Any],
        bank_statement_data: dict[str, Any],
    ) -> str | None:
        """Compare salary slip amount with bank salary-credit averages."""
        salary_slip_amount = float(ocr_data.get("salary_amount") or 0)
        bank_average_credit = float(
            bank_statement_data.get("avg_salary_credit")
            or bank_statement_data.get("credited_salary")
            or (ocr_data.get("metadata", {}) or {}).get("bank_average_salary_credit")
            or 0
        )
        if salary_slip_amount <= 0 or bank_average_credit <= 0:
            return None

        mismatch_ratio = abs(salary_slip_amount - bank_average_credit) / salary_slip_amount
        if mismatch_ratio > 0.20:
            return (
                f"Salary slip amount and bank average salary credits differ by "
                f"{round(mismatch_ratio * 100, 2)}%."
            )
        return None

    def check_bank_statement_consistency(
        self,
        bank_statement_data: dict[str, Any],
    ) -> str | None:
        """Evaluate simple bank-statement salary consistency heuristics."""
        if not bank_statement_data:
            return None

        monthly_credits = bank_statement_data.get("monthly_salary_credits") or []
        if len(monthly_credits) >= 2:
            values = [float(value) for value in monthly_credits if value is not None]
            if values:
                average_value = sum(values) / len(values)
                if average_value > 0:
                    max_variation = max(abs(value - average_value) / average_value for value in values)
                    if max_variation > 0.35:
                        return "Bank statement salary credits are unusually inconsistent across months."

        metadata = bank_statement_data.get("metadata") or {}
        if metadata.get("statement_edit_flag") is True:
            return "Bank statement metadata indicates possible editing or export anomaly."
        return None

    def _normalize_name(self, value: str | None) -> str:
        """Normalize name for rough identity comparison."""
        return " ".join(str(value or "").lower().split())

    def _risk_level(self, score: int) -> str:
        """Map forensic score to LOW/MEDIUM/HIGH."""
        if score > 70:
            return "HIGH"
        if score >= 40:
            return "MEDIUM"
        return "LOW"


# ==========================================
# SECTION: Anomaly Scoring
# ==========================================
# Anomaly features are derived from the forensic flags returned here.


# ==========================================
# SECTION: Forensics
# ==========================================
# This is the main forensic analysis engine for document intelligence.


# ==========================================
# SECTION: Alerts
# ==========================================
# Alert thresholds are applied by alert_service.py after scoring.
