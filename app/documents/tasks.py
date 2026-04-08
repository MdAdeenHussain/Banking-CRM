"""Asynchronous document processing tasks (OCR + fraud checks)."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from celery.utils.log import get_task_logger

from app.models.document import Document
from app.services.document_service import DocumentService
from tasks.celery_app import celery_app


# ==========================================
# SECTION: Core Logic
# ==========================================
logger = get_task_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_document_ocr(self, document_id: int) -> dict:
    """Process OCR and fraud checks for a document.

    Workflow:
    1) Fetch document.
    2) Run OCR extraction.
    3) Store structured OCR data.
    4) Trigger rule-based fraud checks.
    """
    document = Document.query.filter_by(id=document_id, is_deleted=False).first()
    if document is None:
        return {
            "status": "not_found",
            "document_id": document_id,
        }

    service = DocumentService(tenant_id=document.tenant_id, actor_user_id=document.uploaded_by)

    try:
        processed = service.run_ocr_for_document(document_id=document_id)
        scored = service.run_fraud_check_for_document(document_id=document_id)
        logger.info(
            "Document OCR/fraud processed | doc=%s tenant=%s score=%s",
            document_id,
            document.tenant_id,
            scored.fraud_score,
        )
        return {
            "status": "completed",
            "document_id": document_id,
            "ocr_status": processed.ocr_status,
            "fraud_score": scored.fraud_score,
        }
    except Exception as exc:
        logger.exception("Document OCR task failed | doc=%s", document_id)
        raise self.retry(exc=exc, countdown=10)


# ==========================================
# SECTION: Validation
# ==========================================
# N/A for task module.


# ==========================================
# SECTION: Fraud Checks
# ==========================================
# Fraud checks are executed as part of process_document_ocr() using
# DocumentService.run_fraud_check_for_document.
