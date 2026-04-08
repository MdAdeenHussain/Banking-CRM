"""Meta webhook route controllers.

Handles Meta Lead Ads webhook ingestion and transforms payloads into
tenant-scoped lead records.
"""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.automation_engine.meta_tracking_service import MetaTrackingService
from app.models.tenant import Tenant
from app.services.lead_workflow_service import LeadWorkflowService


# ======================================
# SECTION: Core Service Logic
# ======================================
meta_webhook_bp = Blueprint("meta_webhook", __name__)


@meta_webhook_bp.post("/api/v1/meta/webhook")
def receive_meta_lead():
    """Receive Meta lead payload and create a CRM lead.

    Flow:
    1) Verify token placeholder.
    2) Resolve tenant context from payload.
    3) Normalize lead fields.
    4) Create lead with source=meta_ads.
    5) Auto-assign agent via round-robin.
    """
    payload = request.get_json(silent=True) or {}
    meta_service = MetaTrackingService()

    supplied_token = request.headers.get("X-Meta-Token", "")
    if not meta_service.verify_token(supplied_token):
        return jsonify({"status": "error", "message": "Invalid webhook token."}), 401

    normalized = meta_service.receive_meta_lead(payload)
    tenant = normalized.get("tenant")
    if tenant is None:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Tenant context not provided or invalid.",
                }
            ),
            400,
        )

    service = LeadWorkflowService(tenant_id=tenant.id)
    lead_payload = {
        "customer_name": normalized.get("customer_name"),
        "mobile": normalized.get("mobile"),
        "email": normalized.get("email"),
        "loan_type": normalized.get("loan_type"),
        "loan_amount": normalized.get("loan_amount"),
        "source": "meta_ads",
        "medium": "paid_social",
        "stage": "NEW_LEAD",
        "auto_assign": True,
        "branch_id": normalized.get("branch_id"),
        "pan": normalized.get("pan"),
        "campaign": normalized.get("utm_campaign"),
        "campaign_id": normalized.get("campaign_id"),
        "adset_id": normalized.get("adset_id"),
        "ad_id": normalized.get("ad_id"),
        "utm_source": normalized.get("utm_source"),
        "utm_campaign": normalized.get("utm_campaign"),
    }

    try:
        lead = service.create_lead(lead_payload)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 409

    return (
        jsonify(
            {
                "status": "success",
                "message": "Meta lead ingested successfully.",
                "data": {
                    "lead_id": lead.id,
                    "tenant_id": tenant.id,
                    "source": lead.source,
                    "assigned_agent": lead.assigned_agent,
                    "stage": lead.stage,
                },
            }
        ),
        201,
    )


# ======================================
# SECTION: Helper Functions
# ======================================
def _resolve_tenant(payload: dict) -> Tenant | None:
    """Resolve tenant from webhook payload using tenant_id or tenant_slug."""
    return MetaTrackingService().resolve_tenant(payload)


# ======================================
# SECTION: Calculators
# ======================================
# N/A for route module.
