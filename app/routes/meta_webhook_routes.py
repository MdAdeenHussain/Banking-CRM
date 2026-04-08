"""Meta webhook route controllers.

Handles Meta Lead Ads webhook ingestion and transforms payloads into
tenant-scoped lead records.
"""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

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

    # Token verification placeholder.
    # In production, validate signature/token from Meta callback headers.
    expected_token = current_app.config.get("META_WEBHOOK_TOKEN", "")
    supplied_token = request.headers.get("X-Meta-Token", "")
    if expected_token and supplied_token != expected_token:
        return jsonify({"status": "error", "message": "Invalid webhook token."}), 401

    tenant = _resolve_tenant(payload)
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

    # Try Meta-like payload first, then generic fallback.
    lead_data = payload.get("lead") or payload.get("lead_data") or payload

    service = LeadWorkflowService(tenant_id=tenant.id)
    normalized = {
        "customer_name": lead_data.get("full_name") or lead_data.get("name") or "Meta Lead",
        "mobile": lead_data.get("phone") or lead_data.get("mobile") or "",
        "email": lead_data.get("email"),
        "loan_type": lead_data.get("loan_type") or "unknown",
        "loan_amount": lead_data.get("loan_amount"),
        "source": "meta_ads",
        "stage": "NEW_LEAD",
        "auto_assign": True,
        "branch_id": lead_data.get("branch_id"),
        "pan": lead_data.get("pan"),
    }

    try:
        lead = service.create_lead(normalized)
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
    tenant_id = payload.get("tenant_id")
    tenant_slug = payload.get("tenant_slug")

    if tenant_id:
        return Tenant.query.filter_by(id=tenant_id, is_deleted=False, is_active=True).first()

    if tenant_slug:
        return Tenant.query.filter_by(slug=tenant_slug, is_deleted=False, is_active=True).first()

    return None


# ======================================
# SECTION: Calculators
# ======================================
# N/A for route module.
