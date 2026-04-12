"""
LoanAxis CRM — Input Validators

Validation helpers for mobile numbers, CIBIL scores, GSTIN, etc.
"""

import re
from typing import Optional


def validate_mobile(mobile: str) -> tuple[bool, Optional[str]]:
    """
    Validate an Indian mobile number.

    Accepted formats: 10 digits, optionally prefixed with +91 or 0.

    Returns:
        (is_valid, error_message)
    """
    if not mobile:
        return False, "Mobile number is required"

    # Strip whitespace and common prefixes
    cleaned = mobile.strip().replace(" ", "").replace("-", "")
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0"):
        cleaned = cleaned[1:]

    if not cleaned.isdigit():
        return False, "Mobile number must contain only digits"

    if len(cleaned) != 10:
        return False, "Mobile number must be 10 digits"

    if cleaned[0] not in "6789":
        return False, "Mobile number must start with 6, 7, 8, or 9"

    return True, None


def validate_cibil_score(score) -> tuple[bool, Optional[str]]:
    """
    Validate CIBIL score range (300-900).

    Returns:
        (is_valid, error_message)
    """
    if score is None:
        return True, None  # Optional field

    try:
        score = int(score)
    except (ValueError, TypeError):
        return False, "CIBIL score must be a number"

    if score < 300 or score > 900:
        return False, "CIBIL score must be between 300 and 900"

    return True, None


def validate_gstin(gstin: str) -> tuple[bool, Optional[str]]:
    """
    Validate an Indian GSTIN (Goods and Services Tax Identification Number).

    Format: 2-digit state code + 10-char PAN + 1 entity code + Z + 1 check digit.
    Example: 27ABCDE1234F1Z5

    Returns:
        (is_valid, error_message)
    """
    if not gstin:
        return True, None  # Optional field

    gstin = gstin.strip().upper()

    if len(gstin) != 15:
        return False, "GSTIN must be 15 characters"

    pattern = r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[A-Z]{1}\d{1}$"
    if not re.match(pattern, gstin):
        return False, "Invalid GSTIN format"

    # Validate state code (01-37)
    state_code = int(gstin[:2])
    if state_code < 1 or state_code > 37:
        return False, "Invalid state code in GSTIN"

    return True, None


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Basic email format validation.

    Returns:
        (is_valid, error_message)
    """
    if not email:
        return True, None  # Optional in some contexts

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email.strip()):
        return False, "Invalid email address format"

    return True, None


def validate_pincode(pincode: str) -> tuple[bool, Optional[str]]:
    """
    Validate an Indian postal pincode (6 digits).

    Returns:
        (is_valid, error_message)
    """
    if not pincode:
        return True, None

    cleaned = pincode.strip()
    if not cleaned.isdigit() or len(cleaned) != 6:
        return False, "Pincode must be 6 digits"

    if cleaned[0] == "0":
        return False, "Pincode cannot start with 0"

    return True, None


def sanitize_phone(phone: str) -> str:
    """Normalize a phone number to 10 digits."""
    if not phone:
        return ""
    cleaned = phone.strip().replace(" ", "").replace("-", "")
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0"):
        cleaned = cleaned[1:]
    return cleaned
