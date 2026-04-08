"""Application workflow engine.

Handles lifecycle transitions for loan applications with audit timeline
entries and tenant-safe data access.
"""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import current_app

from app.extensions import db
from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.document import Document


# ======================================
# SECTION: Core Service Logic
# ======================================
class ApplicationWorkflowService:
    """Business workflow service for application lifecycle."""

    ALLOWED_STAGES = {
        "INITIATED",
        "DOCS_PENDING",
        "DOCS_VERIFIED",
        "ELIGIBILITY_CHECKED",
        "BANK_MATCHED",
        "SUBMITTED",
        "UNDER_REVIEW",
        "SANCTIONED",
        "DISBURSED",
        "REJECTED",
    }

    def __init__(self, tenant_id: int, actor_user_id: int | None = None) -> None:
        self.tenant_id = tenant_id
        self.actor_user_id = actor_user_id

    def create_application(self, data: dict[str, Any]) -> Application:
        """Create a new application at INITIATED stage."""
        application = Application(
            tenant_id=self.tenant_id,
            customer_id=data["customer_id"],
            loan_type=data.get("loan_type", "unknown"),
            loan_amount=data.get("loan_amount", 0),
            status=data.get("status", "active"),
            current_stage="INITIATED",
        )
        db.session.add(application)
        db.session.flush()

        self._log_timeline(
            application_id=application.id,
            action="application_created",
            details="Application initialized.",
        )

        db.session.commit()
        return application

    def attach_customer(self, application_id: int, customer_id: int) -> Application:
        """Attach or replace customer on application."""
        application = self._get_application_or_fail(application_id)

        customer = Customer.query.filter_by(
            id=customer_id,
            tenant_id=self.tenant_id,
            is_deleted=False,
        ).first()
        if not customer:
            raise ValueError("Customer not found for tenant.")

        application.customer_id = customer.id
        self._log_timeline(
            application_id=application.id,
            action="application_customer_attached",
            details=f"Customer attached: {customer.id}",
        )
        db.session.commit()
        return application

    def attach_documents(self, application_id: int, document_ids: list[int]) -> int:
        """Validate documents and move stage to DOCS_VERIFIED when possible."""
        application = self._get_application_or_fail(application_id)

        documents = (
            Document.query.filter(
                Document.id.in_(document_ids),
                Document.tenant_id == self.tenant_id,
                Document.customer_id == application.customer_id,
                Document.is_deleted.is_(False),
            )
            .all()
        )

        attached_count = len(documents)
        for document in documents:
            # Link document to application so application workflow can surface
            # all supporting files in one timeline.
            document.application_id = application.id

        new_stage = "DOCS_VERIFIED" if attached_count > 0 else "DOCS_PENDING"
        application.current_stage = new_stage
        application.updated_at = datetime.now(timezone.utc)

        self._log_timeline(
            application_id=application.id,
            action="application_documents_attached",
            details=f"Attached documents={attached_count}, stage={new_stage}",
        )
        db.session.commit()
        return attached_count

    def submit_to_bank(self, application_id: int, lender_name: str) -> Application:
        """Submit application to bank and move to SUBMITTED stage."""
        application = self._get_application_or_fail(application_id)
        application.current_stage = "SUBMITTED"
        application.status = "submitted"

        self._log_timeline(
            application_id=application.id,
            action="application_submitted_to_bank",
            details=f"Submitted to lender={lender_name}",
        )
        db.session.commit()
        self._trigger_workflow_event(
            "application_submitted",
            {
                "application_id": application.id,
                "customer_name": getattr(application.customer, "full_name", "Customer"),
                "customer_email": getattr(application.customer, "email", None),
                "customer_mobile": getattr(application.customer, "mobile", None),
                "loan_type": application.loan_type,
                "lender_name": lender_name,
            },
        )
        return application

    def approve(self, application_id: int, remarks: str | None = None) -> Application:
        """Mark application as sanctioned."""
        application = self._get_application_or_fail(application_id)
        application.current_stage = "SANCTIONED"
        application.status = "approved"

        self._log_timeline(
            application_id=application.id,
            action="application_approved",
            details=remarks or "Application sanctioned.",
        )
        db.session.commit()
        return application

    def reject(self, application_id: int, reason: str) -> Application:
        """Mark application as rejected with reason."""
        application = self._get_application_or_fail(application_id)
        application.current_stage = "REJECTED"
        application.status = "rejected"

        self._log_timeline(
            application_id=application.id,
            action="application_rejected",
            details=reason,
        )
        db.session.commit()
        return application

    def update_stage(self, application_id: int, stage: str) -> Application:
        """Generic stage transition helper."""
        if stage not in self.ALLOWED_STAGES:
            raise ValueError(f"Invalid application stage: {stage}")

        application = self._get_application_or_fail(application_id)
        old_stage = application.current_stage
        application.current_stage = stage

        self._log_timeline(
            application_id=application.id,
            action="application_stage_updated",
            details=f"Stage changed {old_stage} -> {stage}",
        )
        db.session.commit()
        return application

    # ======================================
    # SECTION: Helper Functions
    # ======================================
    def _get_application_or_fail(self, application_id: int) -> Application:
        """Fetch application by tenant scope."""
        application = Application.query.filter_by(
            id=application_id,
            tenant_id=self.tenant_id,
            is_deleted=False,
        ).first()
        if not application:
            raise ValueError("Application not found for current tenant.")
        return application

    def _log_timeline(self, *, application_id: int, action: str, details: str) -> None:
        """Store application timeline in audit log."""
        audit = AuditLog(
            tenant_id=self.tenant_id,
            user_id=self.actor_user_id,
            action=action,
            entity="application",
            entity_id=str(application_id),
            details=details,
        )
        db.session.add(audit)

    def _trigger_workflow_event(self, event_name: str, payload: dict[str, Any]) -> None:
        """Trigger Phase 10 workflow automation safely."""
        try:
            from app.automation_engine.workflow_engine import WorkflowEngine

            WorkflowEngine(
                tenant_id=self.tenant_id,
                actor_user_id=self.actor_user_id,
            ).trigger_event(event_name, payload)
        except Exception:
            current_app.logger.debug("Automation workflow event skipped: %s", event_name)


# ======================================
# SECTION: Calculators
# ======================================
# N/A for this workflow module.
