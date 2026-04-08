"""Automation service for communication and reminders.

Provider integrations are placeholders for now; logic is structured for
future adapter-based SMS/email/WhatsApp providers.
"""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

from datetime import datetime, timezone

from app.extensions import db
from app.models.notification import Notification


# ======================================
# SECTION: Core Service Logic
# ======================================
class AutomationService:
    """Dispatches communication placeholders and scheduling metadata."""

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id

    def send_email(self, user_id: int, subject: str, body: str) -> Notification:
        """Create email notification placeholder record."""
        return self._create_notification(
            user_id=user_id,
            title=subject,
            message=body,
            channel="email",
            status="QUEUED",
        )

    def send_sms(self, user_id: int, message: str) -> Notification:
        """Create SMS notification placeholder record."""
        return self._create_notification(
            user_id=user_id,
            title="SMS Alert",
            message=message,
            channel="sms",
            status="QUEUED",
        )

    def schedule_followup(self, user_id: int, message: str, due_at_iso: str) -> Notification:
        """Schedule follow-up reminder placeholder.

        For Phase 4 we persist metadata as text; Celery scheduler hookup
        can read these records later.
        """
        payload = f"Follow-up at {due_at_iso}: {message}"
        return self._create_notification(
            user_id=user_id,
            title="Follow-up Reminder",
            message=payload,
            channel="followup",
            status="SCHEDULED",
        )

    def send_assignment_alert(self, user_id: int, lead_name: str) -> Notification:
        """Notify assignee that a new lead has been assigned."""
        return self._create_notification(
            user_id=user_id,
            title="New Lead Assigned",
            message=f"You have been assigned lead: {lead_name}",
            channel="assignment",
            status="QUEUED",
        )

    # ======================================
    # SECTION: Helper Functions
    # ======================================
    def _create_notification(
        self,
        *,
        user_id: int,
        title: str,
        message: str,
        channel: str,
        status: str,
    ) -> Notification:
        """Persist notification event with tenant safety."""
        notification = Notification(
            tenant_id=self.tenant_id,
            user_id=user_id,
            title=title,
            message=message,
            channel=channel,
            status=status,
            sent_at=datetime.now(timezone.utc) if status == "SENT" else None,
        )
        db.session.add(notification)
        db.session.commit()
        return notification


# ======================================
# SECTION: Calculators
# ======================================
# N/A for this service.
