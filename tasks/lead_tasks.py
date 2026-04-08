"""Lead-related background tasks."""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

from celery.utils.log import get_task_logger

from app.services.dashboard_kpi_service import DashboardKPIService
from tasks.celery_app import celery_app


# ======================================
# SECTION: Core Service Logic
# ======================================
logger = get_task_logger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_followup_reminder(self, tenant_id: int, user_id: int, lead_id: int) -> dict:
    """Send follow-up reminder placeholder.

    In future phases this will call SMS/WhatsApp providers.
    """
    logger.info("Follow-up reminder queued | tenant=%s user=%s lead=%s", tenant_id, user_id, lead_id)
    return {
        "status": "queued",
        "tenant_id": tenant_id,
        "user_id": user_id,
        "lead_id": lead_id,
    }


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def update_dashboard_metrics(self, tenant_id: int) -> dict:
    """Recompute and return owner KPI snapshot for tenant."""
    service = DashboardKPIService(tenant_id=tenant_id)
    owner_kpis = service.get_owner_kpis()
    logger.info("Dashboard metrics refreshed | tenant=%s", tenant_id)
    return {
        "status": "updated",
        "tenant_id": tenant_id,
        "owner_kpis": owner_kpis,
    }


# ======================================
# SECTION: Helper Functions
# ======================================
# N/A for this module.


# ======================================
# SECTION: Calculators
# ======================================
# N/A for this module.
