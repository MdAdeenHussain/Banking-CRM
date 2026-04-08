"""Workflow orchestration engine."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.automation_engine.campaign_attribution_service import CampaignAttributionService
from app.automation_engine.communication_service import CommunicationService
from app.automation_engine.meta_tracking_service import MetaTrackingService
from app.automation_engine.notification_rules import NotificationRulesEngine
from app.automation_engine.scheduler_service import SchedulerService
from app.extensions import db
from app.models.audit_log import AuditLog


# ==========================================
# SECTION: Workflow Rules
# ==========================================
class WorkflowEngine:
    """Central event dispatcher for automation workflows."""

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

    def __init__(self, tenant_id: int, actor_user_id: int | None = None) -> None:
        self.tenant_id = tenant_id
        self.actor_user_id = actor_user_id
        self.communication = CommunicationService(tenant_id=tenant_id)
        self.scheduler = SchedulerService(tenant_id=tenant_id, actor_user_id=actor_user_id)
        self.rules_engine = NotificationRulesEngine(tenant_id=tenant_id)
        self.meta_tracking = MetaTrackingService(tenant_id=tenant_id, actor_user_id=actor_user_id)
        self.campaign_attribution = CampaignAttributionService(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
        )

    def trigger_event(self, event_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch automation event and execute configured rules."""
        if event_name not in self.SUPPORTED_EVENTS:
            raise ValueError(f"Unsupported workflow event: {event_name}")

        self._log_event(event_name=event_name, payload=payload)
        actions = self.execute_rules(event_name, payload)

        if event_name == "lead_created":
            self.create_followup_sequence(payload)
            lead_id = payload.get("lead_id")
            if lead_id and payload.get("campaign_id"):
                self.campaign_attribution.map_lead_to_campaign(
                    lead_id=int(lead_id),
                    source=payload.get("source"),
                    medium=payload.get("medium"),
                    campaign=payload.get("campaign"),
                    adset=payload.get("adset"),
                    creative=payload.get("creative"),
                    campaign_id=payload.get("campaign_id"),
                    adset_id=payload.get("adset_id"),
                    ad_id=payload.get("ad_id"),
                    utm_source=payload.get("utm_source"),
                    utm_campaign=payload.get("utm_campaign"),
                )
                self.meta_tracking.track_lead_created(
                    int(lead_id),
                    campaign_id=payload.get("campaign_id"),
                    tenant_id=self.tenant_id,
                )

        if event_name == "application_submitted" and payload.get("application_id"):
            self.meta_tracking.track_application_submit(
                int(payload["application_id"]),
                tenant_id=self.tenant_id,
            )

        if event_name == "fraud_detected" and int(payload.get("fraud_score", 0) or 0) > 70:
            self.communication.send_push_notification(
                recipient=self.rules_engine._first_user_by_role("owner") or self.actor_user_id,
                template="REJECTION_MESSAGE",
                variables=payload,
            )

        return {
            "event_name": event_name,
            "actions_executed": len(actions),
            "actions": actions,
        }

    def execute_rules(self, event_name: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Evaluate automation rules and execute resulting actions."""
        actions = self.rules_engine.evaluate_rules(event_name, payload)
        executed_actions = []
        for action in actions:
            recipient = action.get("recipient")
            template = action.get("template", "DOCUMENT_REMINDER")
            variables = action.get("variables", payload)
            action_name = action.get("action")

            if recipient is None:
                continue

            if action_name in {"notify_customer", "notify_agent", "notify_manager", "notify_billing"}:
                notification = self.communication.send_whatsapp(
                    recipient=recipient,
                    template=template,
                    variables=variables,
                    retry_count=0,
                )
                executed_actions.append(
                    {
                        "action": action_name,
                        "notification_id": notification.id,
                        "channel": notification.channel,
                    }
                )
            elif action_name == "notify_compliance":
                notification = self.communication.send_email(
                    recipient=recipient,
                    template=template,
                    variables=variables,
                    retry_count=0,
                )
                executed_actions.append(
                    {
                        "action": action_name,
                        "notification_id": notification.id,
                        "channel": notification.channel,
                    }
                )

        return executed_actions

    def create_followup_sequence(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Create day 0/day 1/day 3/day 7 follow-up sequence."""
        results = []
        recipient = payload.get("customer_email") or payload.get("customer_mobile") or payload.get("assigned_agent") or self.actor_user_id

        intro = self.communication.send_whatsapp(
            recipient=recipient,
            template="DOCUMENT_REMINDER",
            variables=payload,
            retry_count=0,
        )
        results.append({"step": "day_0_intro", "notification_id": intro.id})

        results.append(self.schedule_day_1_reminder(payload))
        results.append(self.schedule_day_3_callback(payload))
        results.append(self.schedule_day_7_reengagement(payload))
        return results

    def schedule_day_1_reminder(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Schedule day 1 reminder."""
        scheduled_for = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        notification = self.communication.schedule_message(
            channel="whatsapp",
            recipient=payload.get("customer_email") or payload.get("customer_mobile") or self.actor_user_id,
            template="DOCUMENT_REMINDER",
            variables=payload,
            scheduled_for_iso=scheduled_for,
        )
        return {"step": "day_1_reminder", "notification_id": notification.id}

    def schedule_day_3_callback(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Schedule day 3 callback."""
        due_at = datetime.now(timezone.utc) + timedelta(days=3)
        callback = self.scheduler.schedule_callback(
            lead_id=payload.get("lead_id"),
            customer_name=payload.get("customer_name"),
            date=due_at.strftime("%Y-%m-%d"),
            time=due_at.strftime("%H:%M"),
            assigned_agent=payload.get("assigned_agent"),
            priority="high",
        )
        return {"step": "day_3_callback", "callback_id": callback["callback_id"]}

    def schedule_day_7_reengagement(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Schedule day 7 re-engagement message."""
        scheduled_for = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        notification = self.communication.schedule_message(
            channel="email",
            recipient=payload.get("customer_email") or self.actor_user_id,
            template="ELIGIBILITY_RESULT",
            variables=payload,
            scheduled_for_iso=scheduled_for,
        )
        return {"step": "day_7_reengagement", "notification_id": notification.id}

    def _log_event(self, *, event_name: str, payload: dict[str, Any]) -> None:
        """Persist orchestration event audit trail."""
        audit = AuditLog(
            tenant_id=self.tenant_id,
            user_id=self.actor_user_id,
            action=f"workflow_event_{event_name}",
            entity="workflow",
            entity_id=event_name,
            details=json.dumps(payload, ensure_ascii=True),
        )
        db.session.add(audit)
        db.session.commit()
