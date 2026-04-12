"""
LoanAxis CRM — File Utilities

Secure file upload handling, MIME validation, and token-based serving.
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from flask import current_app
from werkzeug.utils import secure_filename


def validate_mime_type(mime_type: str) -> bool:
    """Check if a MIME type is in the allowed list."""
    allowed = current_app.config.get("ALLOWED_MIME_TYPES", set())
    return mime_type in allowed


def validate_extension(filename: str) -> bool:
    """Check if a file extension is allowed."""
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", set())
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed


def secure_upload(
    file,
    lead_id: str,
    document_type: str,
    upload_folder: str = None,
) -> dict:
    """
    Securely handle a file upload.

    Creates a unique filename, validates the file, saves it to the
    upload directory organized by lead ID, and returns file metadata.

    Args:
        file: Werkzeug FileStorage object from the form
        lead_id: ID of the lead this document belongs to
        document_type: Type of document (e.g., "Aadhaar", "PAN")
        upload_folder: Override upload folder path

    Returns:
        Dict with: stored_filename, file_path, mime_type, file_size_kb

    Raises:
        ValueError: If file validation fails
    """
    if not file or not file.filename:
        raise ValueError("No file provided")

    original_name = secure_filename(file.filename)
    if not original_name:
        raise ValueError("Invalid filename")

    # Validate extension
    if not validate_extension(original_name):
        allowed = ", ".join(current_app.config.get("ALLOWED_EXTENSIONS", set()))
        raise ValueError(f"File type not allowed. Accepted: {allowed}")

    # Validate MIME type
    if file.content_type and not validate_mime_type(file.content_type):
        raise ValueError(f"MIME type '{file.content_type}' is not allowed")

    # Generate unique stored filename
    ext = original_name.rsplit(".", 1)[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    stored_filename = f"{document_type}_{timestamp}_{unique_id}.{ext}"

    # Build path: uploads/<lead_id>/
    base_folder = upload_folder or current_app.config.get("UPLOAD_FOLDER", "uploads")
    lead_folder = os.path.join(base_folder, lead_id)
    os.makedirs(lead_folder, exist_ok=True)

    file_path = os.path.join(lead_folder, stored_filename)

    # Save the file
    file.save(file_path)

    # Get file size
    file_size_kb = round(os.path.getsize(file_path) / 1024, 2)

    # Check size limit
    max_size_bytes = current_app.config.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)
    if os.path.getsize(file_path) > max_size_bytes:
        os.remove(file_path)
        max_mb = max_size_bytes / (1024 * 1024)
        raise ValueError(f"File exceeds maximum size of {max_mb}MB")

    return {
        "original_filename": original_name,
        "stored_filename": stored_filename,
        "file_path": file_path,
        "mime_type": file.content_type,
        "file_size_kb": file_size_kb,
    }


def get_file_path(lead_id: str, stored_filename: str) -> Optional[str]:
    """
    Get the full filesystem path for a stored document.

    Returns None if the file doesn't exist.
    """
    base_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    file_path = os.path.join(base_folder, lead_id, stored_filename)

    if os.path.exists(file_path):
        return file_path
    return None


def delete_file(file_path: str) -> bool:
    """
    Safely delete a file from the filesystem.

    Returns True if deletion succeeded, False otherwise.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except OSError:
        pass
    return False
