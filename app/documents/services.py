"""Document module orchestration helpers.

This module wraps lower-level service functions to keep route handlers
small and beginner-friendly.
"""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.services.document_service import DocumentService


# ==========================================
# SECTION: Core Logic
# ==========================================
class DocumentModuleService:
    """Facade around DocumentService for module-level operations."""

    def __init__(self, tenant_id: int, actor_user_id: int | None = None) -> None:
        self.service = DocumentService(tenant_id=tenant_id, actor_user_id=actor_user_id)

    def list_documents_payload(self) -> list[dict[str, Any]]:
        """Return JSON-friendly list payload for API/UI responses."""
        records = self.service.list_documents()
        return [
            {
                "id": doc.id,
                "customer_id": doc.customer_id,
                "application_id": doc.application_id,
                "file_name": doc.file_name,
                "document_type": doc.document_type,
                "version": doc.version,
                "ocr_status": doc.ocr_status,
                "verification_status": doc.verification_status,
                "fraud_score": doc.fraud_score,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            }
            for doc in records
        ]


# ==========================================
# SECTION: Validation
# ==========================================
# Validation responsibilities are delegated to app.documents.validators
# through DocumentService.


# ==========================================
# SECTION: Fraud Checks
# ==========================================
# Fraud checks are delegated to app.documents.fraud_engine via
# DocumentService methods.
