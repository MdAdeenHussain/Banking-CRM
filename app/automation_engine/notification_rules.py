"""Notification and SLA rules engine."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.automation_engine.scheduler_service import SchedulerService
from app.models.document import Document
from app.models.lead import Lead
from app.models.user import User


# ==========================================
# SECTION: Workflow Rules
# ==========================================
class NotificationRulesEngine:
    """Evaluate automation and SLA escalation rules."""

    SUPPORTED_EVENTS = {
        "lead_created",
        "stage_changed",
        "doc_uploaded",
        "eligibility_checked",
        "application_submitted",
        "fraud_detected",
        "payment_failed",
        "callback_due",
    }

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id

    def evaluate_rules(self, event_name: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Return actions that should be executed for an event."""
        if event_name not in self.SUPPORTED_EVENTS:
            return []

        actions: list[dict[str, Any]] = []
        fraud_score = int(payload.get("fraud_score", 0) or 0)
        no_followup_48h = bool(payload.get("no_followup_48h", False))
        lead_stuck_3d = bool(payload.get("lead_stuck_3d", False))

        if fraud_score > 70 or event_name == "fraud_detected":
            actions.append(
                {
                    "action": "notify_compliance",
                    "recipient": self._first_user_by_role("owner") or self._first_user_by_role("branch"),
                    "template": "REJECTION_MESSAGE",
                    "variables": payload,
                }
            )

        if no_followup_48h:
            actions.append(
                {
                    "action": "notify_manager",
                    "recipient": self._first_user_by_role("branch"),
                    "template": "CALLBACK_REMINDER",
                    "variables": payload,
                }
            )

        if lead_stuck_3d:
            actions.append(
                {
                    "action": "notify_agent",
                    "recipient": payload.get("assigned_agent") or self._first_user_by_role("agent"),
                    "template": "DOCUMENT_REMINDER",
                    "variables": payload,
                }
            )

        if event_name == "application_submitted":
            actions.append(
                {
                    "action": "notify_customer",
                    "recipient": payload.get("customer_email") or payload.get("customer_mobile") or self._first_user_by_role("agent"),
                    "template": "BANK_SUBMISSION",
                    "variables": payload,
                }
            )

        if event_name == "payment_failed":
            actions.append(
                {
                    "action": "notify_billing",
                    "recipient": self._first_user_by_role("owner"),
                    "template": "PAYMENT_ALERT",
                    "variables": payload,
                }
            )

        return actions

    def evaluate_sla_breaches(self) -> dict[str, Any]:
        """Compute SLA breach counts and escalation paths."""
        now = datetime.now(timezone.utc)

        first_contact_cutoff = now - timedelta(minutes=15)
        lead_breaches = Lead.query.filter(
            Lead.tenant_id == self.tenant_id,
            Lead.is_deleted.is_(False),
            Lead.created_at <= first_contact_cutoff,
            Lead.stage.in_(["NEW", "NEW_LEAD"]),
        ).count()

        doc_review_cutoff = now - timedelta(hours=4)
        doc_breaches = Document.query.filter(
            Document.tenant_id == self.tenant_id,
            Document.is_deleted.is_(False),
            Document.created_at <= doc_review_cutoff,
            Document.verification_status.in_(["PENDING", "UNDER_REVIEW"]),
        ).count()

        callback_breaches = sum(
            1
            for callback in SchedulerService(tenant_id=self.tenant_id).get_due_callbacks(within_hours=24)
            if float(callback.get("hours_until_due", 0)) <= 0
        )

        return {
            "lead_first_contact_breaches": int(lead_breaches),
            "doc_review_breaches": int(doc_breaches),
            "callback_due_breaches": int(callback_breaches),
            "total_breaches": int(lead_breaches + doc_breaches + callback_breaches),
            "escalation_path": ["agent", "manager", "owner"],
        }

    def _first_user_by_role(self, role: str) -> int | None:
        """Resolve first active tenant user id for role."""
        user = User.query.filter_by(
            tenant_id=self.tenant_id,
            role=role,
            is_deleted=False,
            is_active=True,
        ).order_by(User.id.asc()).first()
        return user.id if user else None
