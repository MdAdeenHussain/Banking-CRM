"""Document Vault service layer.

Implements secure uploads, versioning, OCR trigger, fraud checks,
and verification workflow using deterministic rule-based logic.
"""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage

from app.documents.fraud_engine import DocumentFraudEngine
from app.documents.models import OCRStatus, VerificationStatus
from app.documents.ocr_engine import OCREngine
from app.documents.validators import (
    sanitize_filename,
    validate_file_size,
    validate_file_type as validate_upload_file_type,
)
from app.extensions import db
from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.document import Document


# ==========================================
# SECTION: Core Logic
# ==========================================
class DocumentService:
    """Core business service for document lifecycle operations."""

    def __init__(self, tenant_id: int, actor_user_id: int | None = None) -> None:
        self.tenant_id = tenant_id
        self.actor_user_id = actor_user_id

    def upload_document(
        self,
        file: FileStorage,
        customer_id: int,
        doc_type: str,
        application_id: int | None = None,
    ) -> Document:
        """Upload and persist document metadata safely.

        Steps:
        1) Validate tenant ownership for customer/application.
        2) Validate file type and size.
        3) Hash file for duplicate detection.
        4) Store file under private uploads path.
        5) Create DB record with versioning.
        6) Trigger OCR async task.
        """
        self._validate_customer_and_application(customer_id, application_id)

        is_type_ok, type_message = self.validate_file_type(file)
        if not is_type_ok:
            raise ValueError(type_message)

        max_size = int(current_app.config.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
        is_size_ok, size_message, size_bytes = validate_file_size(file, max_size)
        if not is_size_ok:
            raise ValueError(size_message)

        file_hash = self.generate_file_hash(file)
        if self.check_duplicate(file_hash, self.tenant_id):
            raise ValueError("Duplicate document detected using file hash.")

        storage_path, safe_name = self._persist_file(file, customer_id)
        version = self._resolve_next_version(customer_id, application_id, doc_type)

        # Versioning rule: old active versions for same slot become inactive.
        self._deactivate_current_version(customer_id, application_id, doc_type)

        document = Document(
            tenant_id=self.tenant_id,
            customer_id=customer_id,
            application_id=application_id,
            file_name=safe_name,
            file_path=storage_path,
            file_size=size_bytes,
            file_type=(file.mimetype or "").lower(),
            document_type=doc_type,
            uploaded_by=self.actor_user_id,
            ocr_status=OCRStatus.PENDING,
            ocr_data_json={},
            fraud_score=0,
            fraud_flags_json={},
            verification_status=VerificationStatus.PENDING,
            file_hash=file_hash,
            version=version,
        )
        db.session.add(document)
        db.session.flush()

        self._log(
            action="document_uploaded",
            entity_id=document.id,
            details=f"Uploaded doc_type={doc_type}, version={version}",
        )
        db.session.commit()

        self._trigger_ocr_task(document.id)
        return document

    def run_ocr_for_document(self, document_id: int) -> Document:
        """Run OCR synchronously and update document record."""
        document = self.get_document_or_fail(document_id)
        engine = OCREngine()

        document.ocr_status = OCRStatus.PROCESSING
        db.session.commit()

        try:
            ocr_data = engine.extract_text(document.file_path)
            document.ocr_data_json = ocr_data
            document.ocr_status = OCRStatus.COMPLETED
            document.updated_at = datetime.now(timezone.utc)
            db.session.commit()

            self._log(
                action="document_ocr_completed",
                entity_id=document.id,
                details="OCR extraction completed.",
            )
            db.session.commit()
        except Exception as exc:  # pragma: no cover - defensive safeguard
            document.ocr_status = OCRStatus.FAILED
            db.session.commit()
            raise RuntimeError(f"OCR pipeline failed: {exc}") from exc

        return document

    def run_fraud_check_for_document(self, document_id: int) -> Document:
        """Run deterministic fraud checks and store score/flags."""
        document = self.get_document_or_fail(document_id)
        engine = DocumentFraudEngine(tenant_id=self.tenant_id)

        result = engine.run_all_checks(
            document=document,
            ocr_data=document.ocr_data_json or {},
            bank_statement_data=None,
        )

        document.fraud_score = int(result["fraud_score"])
        document.fraud_flags_json = {
            "risk_level": result["risk_level"],
            "flags": result["flags"],
        }
        db.session.commit()

        self._log(
            action="document_fraud_checked",
            entity_id=document.id,
            details=f"Fraud score={document.fraud_score}",
        )
        db.session.commit()
        return document

    def verify_document(self, document_id: int, note: str | None = None) -> Document:
        """Mark document as verified and capture verifier metadata."""
        document = self.get_document_or_fail(document_id)
        document.verification_status = VerificationStatus.VERIFIED
        document.verified_by = self.actor_user_id
        document.verified_at = datetime.now(timezone.utc)

        if note:
            self.add_verification_note(document_id, note)

        self._log(
            action="document_verified",
            entity_id=document.id,
            details=note or "Document marked VERIFIED.",
        )
        db.session.commit()
        return document

    def reject_document(self, document_id: int, note: str | None = None) -> Document:
        """Mark document as rejected and capture reviewer details."""
        document = self.get_document_or_fail(document_id)
        document.verification_status = VerificationStatus.REJECTED
        document.verified_by = self.actor_user_id
        document.verified_at = datetime.now(timezone.utc)

        self._log(
            action="document_rejected",
            entity_id=document.id,
            details=note or "Document marked REJECTED.",
        )
        db.session.commit()
        return document

    def add_verification_note(self, document_id: int, note: str) -> None:
        """Persist verification note in audit timeline."""
        document = self.get_document_or_fail(document_id)
        if document.verification_status == VerificationStatus.PENDING:
            document.verification_status = VerificationStatus.UNDER_REVIEW
        self._log(
            action="document_verification_note",
            entity_id=document.id,
            details=note,
        )
        db.session.commit()

    def delete_document(self, document_id: int) -> None:
        """Soft-delete document and keep audit history."""
        document = self.get_document_or_fail(document_id)
        document.is_deleted = True
        document.is_active = False

        self._log(
            action="document_deleted",
            entity_id=document.id,
            details="Document soft-deleted.",
        )
        db.session.commit()

    def get_document_or_fail(self, document_id: int) -> Document:
        """Get tenant-scoped document, else raise ValueError."""
        document = Document.query.filter_by(
            id=document_id,
            tenant_id=self.tenant_id,
            is_deleted=False,
        ).first()
        if not document:
            raise ValueError("Document not found for current tenant.")
        return document

    def list_documents(self) -> list[Document]:
        """List active tenant documents for vault screens."""
        return (
            Document.query.filter_by(
                tenant_id=self.tenant_id,
                is_deleted=False,
            )
            .order_by(Document.created_at.desc())
            .all()
        )


# ==========================================
# SECTION: Validation
# ==========================================
    def validate_file_type(self, file: FileStorage) -> tuple[bool, str]:
        """Validate file type for secure upload."""
        return validate_upload_file_type(file)

    def generate_file_hash(self, file: FileStorage) -> str:
        """Generate SHA256 hash for duplicate detection."""
        hasher = hashlib.sha256()

        file.stream.seek(0)
        while True:
            chunk = file.stream.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
        file.stream.seek(0)

        return hasher.hexdigest()

    def check_duplicate(self, file_hash: str, tenant_id: int) -> bool:
        """Check whether same file hash already exists in tenant vault."""
        existing = Document.query.filter_by(
            tenant_id=tenant_id,
            file_hash=file_hash,
            is_deleted=False,
        ).first()
        return existing is not None


# ==========================================
# SECTION: Fraud Checks
# ==========================================
    def _trigger_ocr_task(self, document_id: int) -> None:
        """Trigger async OCR task with safe fallback."""
        try:
            from app.documents.tasks import process_document_ocr

            process_document_ocr.delay(document_id)
        except Exception:
            # If queue infrastructure is unavailable, keep upload successful.
            # Operator can trigger OCR manually via route endpoint.
            current_app.logger.warning(
                "OCR async trigger skipped for document_id=%s", document_id
            )

    def _validate_customer_and_application(self, customer_id: int, application_id: int | None) -> None:
        """Ensure linked entities belong to same tenant."""
        customer = Customer.query.filter_by(
            id=customer_id,
            tenant_id=self.tenant_id,
            is_deleted=False,
        ).first()
        if not customer:
            raise ValueError("Customer not found for current tenant.")

        if application_id is not None:
            application = Application.query.filter_by(
                id=application_id,
                tenant_id=self.tenant_id,
                customer_id=customer_id,
                is_deleted=False,
            ).first()
            if not application:
                raise ValueError("Application not found for customer in current tenant.")

    def _persist_file(self, file: FileStorage, customer_id: int) -> tuple[str, str]:
        """Write file to private uploads storage with secure naming."""
        safe_original = sanitize_filename(file.filename or "document")
        suffix = Path(safe_original).suffix.lower() or ".bin"
        safe_name = f"{uuid.uuid4().hex}{suffix}"

        upload_root = current_app.config.get("UPLOAD_FOLDER", "uploads")
        target_dir = Path(upload_root) / "documents" / str(self.tenant_id) / str(customer_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / safe_name
        file.save(str(target_path))

        # Stored as internal path only. No direct public URL exposure.
        return str(target_path), safe_name

    def _resolve_next_version(
        self,
        customer_id: int,
        application_id: int | None,
        doc_type: str,
    ) -> int:
        """Return next version number for same document slot."""
        latest = (
            Document.query.filter_by(
                tenant_id=self.tenant_id,
                customer_id=customer_id,
                application_id=application_id,
                document_type=doc_type,
                is_deleted=False,
            )
            .order_by(Document.version.desc(), Document.id.desc())
            .first()
        )
        return (latest.version + 1) if latest else 1

    def _deactivate_current_version(
        self,
        customer_id: int,
        application_id: int | None,
        doc_type: str,
    ) -> None:
        """Deactivate older active versions for same document slot."""
        docs = Document.query.filter_by(
            tenant_id=self.tenant_id,
            customer_id=customer_id,
            application_id=application_id,
            document_type=doc_type,
            is_deleted=False,
            is_active=True,
        ).all()
        for doc in docs:
            doc.is_active = False

    def _log(self, *, action: str, entity_id: int, details: str) -> None:
        """Write audit timeline event."""
        log = AuditLog(
            tenant_id=self.tenant_id,
            user_id=self.actor_user_id,
            action=action,
            entity="document",
            entity_id=str(entity_id),
            details=details,
        )
        db.session.add(log)
