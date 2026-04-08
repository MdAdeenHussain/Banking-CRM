"""Communication service for automation workflows."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.extensions import db
from app.models.notification import Notification
from app.models.user import User


# ==========================================
# SECTION: Workflow Rules
# ==========================================
DOCUMENT_REMINDER = (
    "Hello {{customer_name}}, please upload the pending documents for your "
    "{{loan_type}} application so we can proceed."
)
CALLBACK_REMINDER = (
    "Hello {{customer_name}}, this is a reminder for your callback at "
    "{{callback_time}} regarding your {{loan_type}} request."
)
ELIGIBILITY_RESULT = (
    "Hello {{customer_name}}, your preliminary eligibility for {{loan_type}} "
    "has been updated. Please contact your agent for the next step."
)
BANK_SUBMISSION = (
    "Hello {{customer_name}}, your {{loan_type}} application has been submitted "
    "to the bank. We will keep you updated on the progress."
)
REJECTION_MESSAGE = (
    "Hello {{customer_name}}, your {{loan_type}} application could not be "
    "processed right now. Please speak with our team for alternate options."
)
PAYMENT_ALERT = (
    "Hello {{customer_name}}, we could not process your recent payment. "
    "Please update billing details to avoid service interruption."
)


# ==========================================
# SECTION: Communication
# ==========================================
class CommunicationService:
    """Dispatch communication placeholders through a unified API."""

    TEMPLATES = {
        "DOCUMENT_REMINDER": DOCUMENT_REMINDER,
        "CALLBACK_REMINDER": CALLBACK_REMINDER,
        "ELIGIBILITY_RESULT": ELIGIBILITY_RESULT,
        "BANK_SUBMISSION": BANK_SUBMISSION,
        "REJECTION_MESSAGE": REJECTION_MESSAGE,
        "PAYMENT_ALERT": PAYMENT_ALERT,
    }

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id

    def send_email(
        self,
        *,
        recipient: Any,
        template: str,
        variables: dict[str, Any],
        retry_count: int = 0,
    ) -> Notification:
        """Send email placeholder via SMTP-ready notification record."""
        return self._send(
            channel="email",
            provider="smtp",
            recipient=recipient,
            template=template,
            variables=variables,
            retry_count=retry_count,
        )

    def send_sms(
        self,
        *,
        recipient: Any,
        template: str,
        variables: dict[str, Any],
        retry_count: int = 0,
    ) -> Notification:
        """Send SMS placeholder via Twilio/MSG91-ready notification record."""
        return self._send(
            channel="sms",
            provider="twilio_or_msg91",
            recipient=recipient,
            template=template,
            variables=variables,
            retry_count=retry_count,
        )

    def send_whatsapp(
        self,
        *,
        recipient: Any,
        template: str,
        variables: dict[str, Any],
        retry_count: int = 0,
    ) -> Notification:
        """Send WhatsApp placeholder via WhatsApp Business API-ready record."""
        return self._send(
            channel="whatsapp",
            provider="whatsapp_business_api",
            recipient=recipient,
            template=template,
            variables=variables,
            retry_count=retry_count,
        )

    def send_push_notification(
        self,
        *,
        recipient: Any,
        template: str,
        variables: dict[str, Any],
        retry_count: int = 0,
    ) -> Notification:
        """Send in-app/push placeholder notification."""
        return self._send(
            channel="push",
            provider="push_gateway_placeholder",
            recipient=recipient,
            template=template,
            variables=variables,
            retry_count=retry_count,
        )

    def schedule_message(
        self,
        *,
        channel: str,
        recipient: Any,
        template: str,
        variables: dict[str, Any],
        scheduled_for_iso: str,
        retry_count: int = 0,
    ) -> Notification:
        """Create a scheduled outbound message record."""
        user_id = self._resolve_user_id(recipient)
        rendered_message = self.render_template(template, variables)
        payload = {
            "provider": "scheduled_placeholder",
            "recipient": self._recipient_label(recipient),
            "template": template,
            "variables": variables,
            "rendered_message": rendered_message,
            "scheduled_for": scheduled_for_iso,
            "retry_count": retry_count,
        }
        notification = Notification(
            tenant_id=self.tenant_id,
            user_id=user_id,
            title=f"{channel.upper()} Scheduled: {template.replace('_', ' ').title()}",
            message=json.dumps(payload, ensure_ascii=True),
            channel=channel,
            status="SCHEDULED",
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    def render_template(self, template_name: str, variables: dict[str, Any]) -> str:
        """Render template using simple placeholder replacement."""
        template = self.TEMPLATES.get(template_name, template_name)
        rendered = template
        for key, value in (variables or {}).items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return rendered

    def _send(
        self,
        *,
        channel: str,
        provider: str,
        recipient: Any,
        template: str,
        variables: dict[str, Any],
        retry_count: int,
    ) -> Notification:
        """Create immediate notification placeholder with rendered content."""
        user_id = self._resolve_user_id(recipient)
        rendered_message = self.render_template(template, variables)
        payload = {
            "provider": provider,
            "recipient": self._recipient_label(recipient),
            "template": template,
            "variables": variables,
            "rendered_message": rendered_message,
            "retry_count": retry_count,
        }
        notification = Notification(
            tenant_id=self.tenant_id,
            user_id=user_id,
            title=template.replace("_", " ").title(),
            message=json.dumps(payload, ensure_ascii=True),
            channel=channel,
            status="SENT",
            sent_at=datetime.now(timezone.utc),
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    def _resolve_user_id(self, recipient: Any) -> int:
        """Resolve notification user_id from recipient payload."""
        if isinstance(recipient, int):
            user = User.query.filter_by(
                id=recipient,
                tenant_id=self.tenant_id,
                is_deleted=False,
            ).first()
            if user:
                return user.id

        if isinstance(recipient, dict):
            for key in ["user_id", "id"]:
                value = recipient.get(key)
                if value:
                    return self._resolve_user_id(int(value))

            email = str(recipient.get("email", "")).strip().lower()
            if email:
                user = User.query.filter(
                    User.tenant_id == self.tenant_id,
                    User.email.ilike(email),
                    User.is_deleted.is_(False),
                ).first()
                if user:
                    return user.id

            phone = str(recipient.get("phone", "") or recipient.get("mobile", "")).strip()
            if phone:
                user = User.query.filter_by(
                    tenant_id=self.tenant_id,
                    phone=phone,
                    is_deleted=False,
                ).first()
                if user:
                    return user.id

        if isinstance(recipient, str):
            value = recipient.strip()
            user = User.query.filter(
                User.tenant_id == self.tenant_id,
                ((User.email.ilike(value)) | (User.phone == value) | (User.name.ilike(value))),
                User.is_deleted.is_(False),
            ).first()
            if user:
                return user.id

        fallback_user = User.query.filter_by(
            tenant_id=self.tenant_id,
            is_deleted=False,
        ).order_by(User.id.asc()).first()
        if fallback_user is None:
            raise ValueError("No valid user found to associate notification with.")
        return fallback_user.id

    def _recipient_label(self, recipient: Any) -> str:
        """Return human-readable recipient label for payload metadata."""
        if isinstance(recipient, dict):
            return str(
                recipient.get("email")
                or recipient.get("phone")
                or recipient.get("mobile")
                or recipient.get("user_id")
                or "unknown"
            )
        return str(recipient)


# ==========================================
# SECTION: Scheduling
# ==========================================
# Scheduled message support is implemented through Notification records.


# ==========================================
# SECTION: Tracking
# ==========================================
# Communication payloads include template/provider metadata for auditing.
