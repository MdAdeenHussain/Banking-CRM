"""Knowledge loading pipeline for vector memory.

This module converts existing platform data into searchable semantic
memory records for lender rules, rejections, fraud patterns, and more.
"""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.lead import Lead
from app.models.lender import Lender
from app.rag_engine.embedding_service import EmbeddingService


# ==========================================
# SECTION: Embeddings
# ==========================================
# Knowledge records are embedded before storage in the vector layer.


# ==========================================
# SECTION: Vector Search
# ==========================================
# VectorStore ingests the records produced by this loader.


# ==========================================
# SECTION: Retrieval Logic
# ==========================================
class KnowledgeLoader:
    """Loads tenant knowledge into vector-memory-friendly documents."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()

    def load_all_sources(self, tenant_id: int) -> list[dict[str, Any]]:
        """Load every supported Phase 8 knowledge source for one tenant."""
        records: list[dict[str, Any]] = []
        records.extend(self.load_lender_rules(tenant_id))
        records.extend(self.load_historical_applications(tenant_id))
        records.extend(self.load_rejection_logs(tenant_id))
        records.extend(self.load_fraud_logs(tenant_id))
        records.extend(self.load_call_summaries(tenant_id))
        records.extend(self.load_compliance_notes(tenant_id))
        records.extend(self.load_branch_reports(tenant_id))
        return records

    def load_lender_rules(self, tenant_id: int) -> list[dict[str, Any]]:
        """Load lender rule memory from lender benchmark records."""
        lenders = Lender.query.filter_by(tenant_id=tenant_id, is_deleted=False).all()
        documents = []
        for lender in lenders:
            text = (
                f"Lender rule for {lender.lender_name}. "
                f"Interest rate {float(lender.interest_rate or 0):.2f}. "
                f"Approval percentage {float(lender.approval_percentage or 0):.2f}. "
                f"Speed score {float(lender.speed_score or 0):.2f}. "
                f"Documentation ease {float(lender.ease_score or 0):.2f}."
            )
            documents.append(
                self._build_record(
                    record_id=f"lender-rule-{tenant_id}-{lender.id}",
                    tenant_id=tenant_id,
                    namespace="lender_rules",
                    text=text,
                    metadata={
                        "lender_id": lender.id,
                        "lender_name": lender.lender_name,
                        "interest_rate": float(lender.interest_rate or 0),
                    },
                )
            )
        return documents

    def load_historical_applications(self, tenant_id: int) -> list[dict[str, Any]]:
        """Load historical application outcomes for similarity search."""
        applications = Application.query.filter_by(tenant_id=tenant_id, is_deleted=False).all()
        documents = []
        for application in applications:
            customer_name = getattr(application.customer, "full_name", "customer")
            text = (
                f"Historical application for {customer_name}. "
                f"Loan type {application.loan_type}. "
                f"Amount {float(application.loan_amount or 0):.2f}. "
                f"Current stage {application.current_stage}. "
                f"Status {application.status}."
            )
            documents.append(
                self._build_record(
                    record_id=f"application-{tenant_id}-{application.id}",
                    tenant_id=tenant_id,
                    namespace="historical_applications",
                    text=text,
                    metadata={
                        "application_id": application.id,
                        "loan_type": application.loan_type,
                        "current_stage": application.current_stage,
                        "status": application.status,
                    },
                )
            )
        return documents

    def load_rejection_logs(self, tenant_id: int) -> list[dict[str, Any]]:
        """Load rejection reasoning from audit trails and applications."""
        applications = (
            Application.query.filter(
                Application.tenant_id == tenant_id,
                Application.is_deleted.is_(False),
                Application.current_stage.in_(["REJECTED"]),
            ).all()
        )
        audit_logs = (
            AuditLog.query.filter(
                AuditLog.tenant_id == tenant_id,
                AuditLog.is_deleted.is_(False),
                AuditLog.action.ilike("%reject%"),
            ).all()
        )

        records = []
        for application in applications:
            text = (
                f"Rejected application memory. Loan type {application.loan_type}. "
                f"Amount {float(application.loan_amount or 0):.2f}. "
                f"Stage {application.current_stage}. Status {application.status}."
            )
            records.append(
                self._build_record(
                    record_id=f"rejection-application-{tenant_id}-{application.id}",
                    tenant_id=tenant_id,
                    namespace="rejections",
                    text=text,
                    metadata={
                        "application_id": application.id,
                        "reason_source": "application_stage",
                    },
                )
            )

        for audit_log in audit_logs:
            text = (
                f"Rejection audit memory for entity {audit_log.entity}. "
                f"Action {audit_log.action}. Details {audit_log.details or 'no details'}."
            )
            records.append(
                self._build_record(
                    record_id=f"rejection-audit-{tenant_id}-{audit_log.id}",
                    tenant_id=tenant_id,
                    namespace="rejections",
                    text=text,
                    metadata={
                        "audit_log_id": audit_log.id,
                        "entity": audit_log.entity,
                        "action": audit_log.action,
                    },
                )
            )
        return records

    def load_fraud_logs(self, tenant_id: int) -> list[dict[str, Any]]:
        """Load fraud-related document memory for semantic matching."""
        documents = (
            Document.query.filter(
                Document.tenant_id == tenant_id,
                Document.is_deleted.is_(False),
                Document.fraud_score >= 40,
            ).all()
        )
        records = []
        for document in documents:
            flags = document.fraud_flags_json or []
            flag_text = ", ".join(str(flag) for flag in flags) if flags else "no explicit flags"
            text = (
                f"Fraud case for document type {document.document_type}. "
                f"Fraud score {document.fraud_score}. "
                f"Flags {flag_text}. "
                f"OCR status {document.ocr_status}. Verification status {document.verification_status}."
            )
            records.append(
                self._build_record(
                    record_id=f"fraud-case-{tenant_id}-{document.id}",
                    tenant_id=tenant_id,
                    namespace="fraud_cases",
                    text=text,
                    metadata={
                        "document_id": document.id,
                        "document_type": document.document_type,
                        "fraud_score": int(document.fraud_score or 0),
                    },
                )
            )
        return records

    def load_call_summaries(self, tenant_id: int) -> list[dict[str, Any]]:
        """Load call/transcript proxies from lead records."""
        leads = Lead.query.filter_by(tenant_id=tenant_id, is_deleted=False).all()
        records = []
        for lead in leads:
            text = (
                f"Customer interaction memory for {lead.customer_name}. "
                f"Lead stage {lead.stage}. Loan type {lead.loan_type or 'unknown'}. "
                f"Source {lead.source or 'unknown'}. "
                f"Assigned agent {lead.assigned_agent or 'unassigned'}. "
                f"Likely transcript summary: customer discussed {lead.loan_type or 'loan needs'} "
                f"with amount {float(lead.loan_amount or 0):.2f}."
            )
            records.append(
                self._build_record(
                    record_id=f"call-summary-{tenant_id}-{lead.id}",
                    tenant_id=tenant_id,
                    namespace="call_transcripts",
                    text=text,
                    metadata={
                        "lead_id": lead.id,
                        "customer_name": lead.customer_name,
                        "lead_stage": lead.stage,
                    },
                )
            )
        return records

    def load_compliance_notes(self, tenant_id: int) -> list[dict[str, Any]]:
        """Load compliance and audit notes from audit logs."""
        audit_logs = (
            AuditLog.query.filter(
                AuditLog.tenant_id == tenant_id,
                AuditLog.is_deleted.is_(False),
                AuditLog.entity.in_(["compliance", "audit", "document"]),
            ).all()
        )
        records = []
        for audit_log in audit_logs:
            text = (
                f"Compliance note memory. Action {audit_log.action}. "
                f"Entity {audit_log.entity}. Details {audit_log.details or 'no details'}."
            )
            records.append(
                self._build_record(
                    record_id=f"compliance-note-{tenant_id}-{audit_log.id}",
                    tenant_id=tenant_id,
                    namespace="compliance_notes",
                    text=text,
                    metadata={
                        "audit_log_id": audit_log.id,
                        "action": audit_log.action,
                    },
                )
            )
        return records

    def load_branch_reports(self, tenant_id: int) -> list[dict[str, Any]]:
        """Load branch-style narratives from audit summaries and lead trends."""
        leads = Lead.query.filter_by(tenant_id=tenant_id, is_deleted=False).limit(25).all()
        if not leads:
            return []

        stage_summary: dict[str, int] = {}
        for lead in leads:
            stage_summary[lead.stage] = stage_summary.get(lead.stage, 0) + 1

        summary_text = ", ".join(
            f"{stage}: {count}" for stage, count in sorted(stage_summary.items())
        )
        text = (
            "Branch report memory summarizing recent lead movement. "
            f"Recent stage mix includes {summary_text}."
        )
        return [
            self._build_record(
                record_id=f"branch-report-{tenant_id}",
                tenant_id=tenant_id,
                namespace="branch_reports",
                text=text,
                metadata={"summary_type": "stage_mix"},
            )
        ]

    def _build_record(
        self,
        *,
        record_id: str,
        tenant_id: int,
        namespace: str,
        text: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a vector-store-ready record with embedding attached."""
        return {
            "id": record_id,
            "tenant_id": tenant_id,
            "namespace": namespace,
            "text": text,
            "metadata": metadata,
            "embedding": self.embedding_service.embed_document(text),
        }


# ==========================================
# SECTION: Context Builder
# ==========================================
# PromptContextBuilder consumes these records after retrieval.
