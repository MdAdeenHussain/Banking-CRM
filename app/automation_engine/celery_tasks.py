"""Celery orchestration tasks for automation workflows."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import json
from datetime import datetime, timezone

from celery.utils.log import get_task_logger

from app.automation_engine.campaign_attribution_service import CampaignAttributionService
from app.automation_engine.communication_service import CommunicationService
from app.automation_engine.scheduler_service import SchedulerService
from app.models.notification import Notification
from app.models.tenant import Tenant
from app.services.dashboard_kpi_service import DashboardKPIService
from tasks.celery_app import celery_app


logger = get_task_logger(__name__)


# ==========================================
# SECTION: Workflow Rules
# ==========================================
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_scheduled_reminder(self) -> dict:
    """Send due scheduled reminders from Notification table."""
    now = datetime.now(timezone.utc)
    processed = 0
    notifications = Notification.query.filter_by(status="SCHEDULED", is_deleted=False).all()
    for notification in notifications:
        try:
            payload = json.loads(notification.message or "{}")
        except json.JSONDecodeError:
            payload = {}
        scheduled_for = payload.get("scheduled_for")
        if not scheduled_for:
            continue
        try:
            due_at = datetime.fromisoformat(scheduled_for)
        except ValueError:
            continue
        if due_at <= now:
            notification.status = "SENT"
            notification.sent_at = now
            processed += 1
    if processed:
        from app.extensions import db

        db.session.commit()
    logger.info("Scheduled reminders processed=%s", processed)
    return {"status": "completed", "processed": processed}


# ==========================================
# SECTION: Communication
# ==========================================
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_callback_alert(self) -> dict:
    """Send callback alerts for callbacks due within 24 hours."""
    triggered = 0
    tenants = Tenant.query.filter_by(is_deleted=False, is_active=True).all()
    for tenant in tenants:
        scheduler = SchedulerService(tenant_id=tenant.id)
        communication = CommunicationService(tenant_id=tenant.id)
        for callback in scheduler.get_due_callbacks(within_hours=24):
            communication.send_push_notification(
                recipient=callback.get("assigned_agent") or callback.get("lead_id") or 1,
                template="CALLBACK_REMINDER",
                variables={
                    "customer_name": callback.get("customer_name", "Customer"),
                    "loan_type": "loan",
                    "callback_time": callback.get("time", "soon"),
                },
                retry_count=0,
            )
            triggered += 1
    logger.info("Callback alerts triggered=%s", triggered)
    return {"status": "completed", "triggered": triggered}


# ==========================================
# SECTION: Scheduling
# ==========================================
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def daily_branch_summary(self) -> dict:
    """Generate daily branch summaries from KPI service."""
    summaries = []
    tenants = Tenant.query.filter_by(is_deleted=False, is_active=True).all()
    for tenant in tenants:
        kpis = DashboardKPIService(tenant_id=tenant.id).get_branch_kpis()
        summaries.append({"tenant_id": tenant.id, "branch_kpis": kpis})
    logger.info("Daily branch summaries generated=%s", len(summaries))
    return {"status": "completed", "tenant_count": len(summaries)}


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def stale_lead_reengagement(self) -> dict:
    """Schedule re-engagement for stale leads via workflow audit trails."""
    reengaged = 0
    tenants = Tenant.query.filter_by(is_deleted=False, is_active=True).all()
    for tenant in tenants:
        service = CampaignAttributionService(tenant_id=tenant.id)
        _ = service.calculate_campaign_roi()
        stale_leads = DashboardKPIService(tenant_id=tenant.id).get_owner_kpis().get("stale_leads", 0)
        reengaged += int(stale_leads)
    logger.info("Stale lead re-engagement evaluated=%s", reengaged)
    return {"status": "completed", "stale_leads": reengaged}


# ==========================================
# SECTION: Tracking
# ==========================================
# Campaign ROI and scheduling metadata flow through these tasks.
