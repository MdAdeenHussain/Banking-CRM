"""Validation helpers for secure document upload pipeline."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import os
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.documents.models import ALLOWED_MIME_TYPES, ALLOWED_UPLOAD_EXTENSIONS


# ==========================================
# SECTION: Core Logic
# ==========================================
def sanitize_filename(filename: str) -> str:
    """Return filesystem-safe filename.

    This prevents path traversal and unsupported characters.
    """
    return secure_filename(filename or "document")


def resolve_extension(filename: str) -> str:
    """Extract lowercase extension without dot."""
    return Path(filename).suffix.lower().lstrip(".")


# ==========================================
# SECTION: Validation
# ==========================================
def validate_file_type(file_obj: FileStorage) -> tuple[bool, str]:
    """Validate extension + MIME against allow-list.

    Allowed: pdf, jpg, jpeg, png
    """
    filename = sanitize_filename(file_obj.filename or "")
    extension = resolve_extension(filename)
    mimetype = (file_obj.mimetype or "").lower()

    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        return False, "Unsupported file extension. Allowed: pdf, jpg, jpeg, png."

    if mimetype not in ALLOWED_MIME_TYPES:
        return False, "Unsupported MIME type. Allowed: application/pdf, image/jpeg, image/png."

    return True, "ok"


def validate_file_size(file_obj: FileStorage, max_bytes: int) -> tuple[bool, str, int]:
    """Validate upload size without loading entire file in memory."""
    file_obj.stream.seek(0, os.SEEK_END)
    size = int(file_obj.stream.tell())
    file_obj.stream.seek(0)

    if size <= 0:
        return False, "Uploaded file is empty.", size
    if size > max_bytes:
        return False, f"File exceeds max allowed size ({max_bytes} bytes).", size

    return True, "ok", size


# ==========================================
# SECTION: Fraud Checks
# ==========================================
# N/A in validators module. Fraud checks are implemented in fraud_engine.py
