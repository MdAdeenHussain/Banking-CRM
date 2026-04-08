"""Notification and periodic summary tasks."""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

from celery.utils.log import get_task_logger

from app.models.tenant import Tenant
from app.services.dashboard_kpi_service import DashboardKPIService
from tasks.celery_app import celery_app


# ======================================
# SECTION: Core Service Logic
# ======================================
logger = get_task_logger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def nightly_kpi_summary(self) -> dict:
    """Generate nightly KPI summaries for all active tenants."""
    summaries = []

    tenants = Tenant.query.filter_by(is_deleted=False, is_active=True).all()
    for tenant in tenants:
        service = DashboardKPIService(tenant_id=tenant.id)
        summaries.append(
            {
                "tenant_id": tenant.id,
                "owner_kpis": service.get_owner_kpis(),
            }
        )

    logger.info("Nightly KPI summary generated for %s tenants", len(summaries))
    return {
        "status": "completed",
        "tenant_count": len(summaries),
        "summaries": summaries,
    }


# ======================================
# SECTION: Helper Functions
# ======================================
# N/A for this module.


# ======================================
# SECTION: Calculators
# ======================================
# N/A for this module.
