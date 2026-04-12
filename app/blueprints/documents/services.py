"""
LoanAxis CRM — Document Services
"""
from datetime import datetime, timezone
from app.extensions import db
from app.models.document import Document
from app.utils.file_utils import secure_upload


def handle_upload(file, lead_id, document_type, uploaded_by_id, custom_label=None, expiry_date=None):
    """Handle document upload with versioning."""
    file_info = secure_upload(file, lead_id, document_type)

    # Check for existing version of same doc type
    existing = Document.query.filter_by(
        lead_id=lead_id, document_type=document_type, is_deleted=False
    ).order_by(Document.version_number.desc()).first()

    version = (existing.version_number + 1) if existing else 1

    doc = Document(
        lead_id=lead_id,
        document_type=document_type,
        custom_label=custom_label,
        original_filename=file_info["original_filename"],
        stored_filename=file_info["stored_filename"],
        file_path=file_info["file_path"],
        mime_type=file_info["mime_type"],
        file_size_kb=file_info["file_size_kb"],
        version_number=version,
        uploaded_by=uploaded_by_id,
        uploaded_at=datetime.now(timezone.utc),
        expiry_date=expiry_date,
    )
    db.session.add(doc)
    db.session.commit()
    return doc


def get_document_by_token(token):
    """Get a document by its access token."""
    return Document.query.filter_by(access_token=token, is_deleted=False).first()
