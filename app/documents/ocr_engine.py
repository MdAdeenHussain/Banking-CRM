"""Rule-based OCR engine placeholder.

This module intentionally avoids external AI/LLM APIs in Phase 5.
"""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from app.documents.models import OCRExtractionResult


# ==========================================
# SECTION: Core Logic
# ==========================================
class OCREngine:
    """Basic OCR pipeline abstraction with deterministic parsing."""

    PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
    AADHAAR_REGEX = re.compile(r"\b\d{12}\b")

    def extract_text(self, file_path: str) -> dict[str, Any]:
        """Placeholder text extraction.

        Real OCR engine can replace this later. For now, we build a
        predictable text payload from filename and file metadata.
        """
        file_name = Path(file_path).name
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        simulated_text = (
            f"Document file={file_name}; size={file_size}; "
            "PAN=ABCDE1234F; AADHAAR=123412341234; "
            "SALARY=55000; COMPANY=Acme Financial Services"
        )

        parsed_pan = self.parse_pan(simulated_text)
        parsed_aadhaar = self.parse_aadhaar(simulated_text)
        salary_data = self.parse_salary_slip(simulated_text)

        result = OCRExtractionResult(
            raw_text=simulated_text,
            extracted_pan=parsed_pan,
            extracted_aadhaar=parsed_aadhaar,
            salary_amount=salary_data.get("salary_amount"),
            company_name=salary_data.get("company_name"),
            metadata={
                "engine": "phase5_placeholder_ocr",
                "file_name": file_name,
                "file_size": file_size,
            },
        )
        return result.to_dict()


# ==========================================
# SECTION: Validation
# ==========================================
    def parse_pan(self, data: str) -> str | None:
        """Extract PAN number from OCR text using regex."""
        match = self.PAN_REGEX.search((data or "").upper())
        return match.group(0) if match else None

    def parse_aadhaar(self, data: str) -> str | None:
        """Extract Aadhaar number from OCR text using regex."""
        match = self.AADHAAR_REGEX.search(data or "")
        return match.group(0) if match else None

    def parse_salary_slip(self, data: str) -> dict[str, Any]:
        """Extract salary and company placeholder fields."""
        salary_match = re.search(r"SALARY\s*=\s*([0-9]+(?:\.[0-9]+)?)", data or "", flags=re.IGNORECASE)
        company_match = re.search(r"COMPANY\s*=\s*([^;]+)", data or "", flags=re.IGNORECASE)

        salary_amount = float(salary_match.group(1)) if salary_match else None
        company_name = company_match.group(1).strip() if company_match else None

        return {
            "salary_amount": salary_amount,
            "company_name": company_name,
        }


# ==========================================
# SECTION: Fraud Checks
# ==========================================
# OCR engine does not run fraud checks directly.
