"""Fraud alert workflow service."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.notification import Notification
from app.models.user import User


# ==========================================
# SECTION: Fraud Detection
# ==========================================
class FraudAlertService:
    """Generate and list fraud alerts for operational users."""

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id

    def trigger_alerts(
        self,
        *,
        risk_score: int,
        risk_level: str,
        entity_label: str,
        message: str,
    ) -> list[Notification]:
        """Create alerts when fraud score crosses the escalation threshold."""
        if int(risk_score) <= 70:
            return []

        recipients = User.query.filter(
            User.tenant_id == self.tenant_id,
            User.is_deleted.is_(False),
            User.role.in_(["branch", "owner", "platform", "compliance"]),
        ).all()

        notifications = []
        for user in recipients:
            notification = Notification(
                tenant_id=self.tenant_id,
                user_id=user.id,
                title=f"Fraud Alert: {entity_label}",
                message=f"[{risk_level}] Score {risk_score}. {message}",
                channel="in_app",
                status="QUEUED",
            )
            db.session.add(notification)
            notifications.append(notification)

        db.session.commit()
        return notifications

    def list_alerts(self, *, user_id: int | None = None, limit: int = 25) -> list[Notification]:
        """List fraud alerts for a tenant or a specific user."""
        query = Notification.query.filter(
            Notification.tenant_id == self.tenant_id,
            Notification.is_deleted.is_(False),
            Notification.title.ilike("Fraud Alert:%"),
        )
        if user_id is not None:
            query = query.filter(Notification.user_id == user_id)
        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    def serialize_alerts(self, alerts: list[Notification]) -> list[dict[str, Any]]:
        """Return JSON-safe alert payloads."""
        return [
            {
                "id": alert.id,
                "title": alert.title,
                "message": alert.message,
                "channel": alert.channel,
                "status": alert.status,
                "is_read": alert.is_read,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            }
            for alert in alerts
        ]


# ==========================================
# SECTION: Anomaly Scoring
# ==========================================
# Alerts are downstream of the final anomaly/risk score.


# ==========================================
# SECTION: Forensics
# ==========================================
# Alert messages may include forensic findings generated elsewhere.


# ==========================================
# SECTION: Alerts
# ==========================================
# This is the operational escalation workflow for high fraud risk.
