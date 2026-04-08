"""AI assistant API routes for Phase 7 LLM features."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.ai_hub.assistant_service import AssistantService
from app.ai_hub.call_summary_service import CallSummaryService
from app.ai_hub.message_draft_service import MessageDraftService
from app.ai_hub.next_action_service import NextActionService
from app.ai_hub.report_generator import ReportGenerator


ai_hub_bp = Blueprint("ai_hub", __name__)


# ==========================================
# SECTION: Provider Routing
# ==========================================
# Each route delegates provider choice to the ai_hub service layer.


# ==========================================
# SECTION: Prompt Templates
# ==========================================
# Routes send structured payloads into service methods, which render the
# appropriate prompt templates internally.


# ==========================================
# SECTION: Assistant Logic
# ==========================================
@ai_hub_bp.post("/api/v1/ai/call-summary")
@login_required
def call_summary_api():
    """Return structured call summary output."""
    payload = request.get_json(silent=True) or {}
    service = CallSummaryService()
    data = service.summarize_call(payload.get("transcript", ""), tenant_id=current_user.tenant_id)
    return jsonify({"success": True, "data": data}), 200


@ai_hub_bp.post("/api/v1/ai/next-action")
@login_required
def next_action_api():
    """Return next-best-action recommendation."""
    payload = request.get_json(silent=True) or {}
    service = NextActionService()
    data = service.recommend(payload, tenant_id=current_user.tenant_id)
    return jsonify({"success": True, "data": data}), 200


@ai_hub_bp.post("/api/v1/ai/message-draft")
@login_required
def message_draft_api():
    """Return drafted WhatsApp/email/SMS message."""
    payload = request.get_json(silent=True) or {}
    service = MessageDraftService()
    channel = str(payload.get("channel", "whatsapp")).lower()

    if channel == "email":
        data = service.draft_email(payload, tenant_id=current_user.tenant_id)
    elif channel == "sms":
        data = service.draft_sms(payload, tenant_id=current_user.tenant_id)
    else:
        data = service.draft_whatsapp(payload, tenant_id=current_user.tenant_id)

    return jsonify({"success": True, "data": data}), 200


@ai_hub_bp.post("/api/v1/ai/rejection-explanation")
@login_required
def rejection_explanation_api():
    """Return borrower-friendly rejection explanation."""
    payload = request.get_json(silent=True) or {}
    service = AssistantService()
    data = service.explain_rejection(payload, tenant_id=current_user.tenant_id)
    return jsonify({"success": True, "data": data}), 200


@ai_hub_bp.post("/api/v1/ai/branch-report")
@login_required
def branch_report_api():
    """Return branch narrative report."""
    payload = request.get_json(silent=True) or {}
    service = ReportGenerator()
    payload.setdefault("requested_by_tenant", current_user.tenant_id)
    data = service.generate_branch_report(payload, tenant_id=current_user.tenant_id)
    return jsonify({"success": True, "data": data}), 200
