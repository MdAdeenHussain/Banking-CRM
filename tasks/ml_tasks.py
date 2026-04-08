"""Celery tasks for periodic classical ML retraining."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from celery.utils.log import get_task_logger

from app.ai_ml.training_pipeline import (
    train_eligibility_model,
    train_lead_model,
    train_lender_model,
)
from app.models.tenant import Tenant
from tasks.celery_app import celery_app


logger = get_task_logger(__name__)


# ==========================================
# SECTION: Training Logic
# ==========================================
@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def weekly_model_retraining(self) -> dict:
    """Weekly scheduled retraining for all active tenants.

    Retrains:
    - lead scoring
    - eligibility
    - lender ranking
    """
    summaries: list[dict] = []

    tenants = Tenant.query.filter_by(is_deleted=False, is_active=True).all()
    for tenant in tenants:
        lead_result = train_lead_model(tenant.id)
        eligibility_result = train_eligibility_model(tenant.id)
        lender_result = train_lender_model(tenant.id)

        summaries.append(
            {
                "tenant_id": tenant.id,
                "lead": lead_result,
                "eligibility": eligibility_result,
                "lender": lender_result,
            }
        )

    logger.info("Weekly retraining completed for %s tenants", len(summaries))
    return {
        "status": "completed",
        "tenant_count": len(summaries),
        "summaries": summaries,
    }


# ==========================================
# SECTION: Prediction Logic
# ==========================================
# Prediction serving is handled via app.ai_ml.inference_service.


# ==========================================
# SECTION: Serialization
# ==========================================
# Each training pipeline handles model artifact serialization + registry writes.
