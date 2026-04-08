"""Automation and orchestration API routes."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.automation_engine.campaign_attribution_service import CampaignAttributionService
from app.automation_engine.meta_tracking_service import MetaTrackingService
from app.automation_engine.scheduler_service import SchedulerService
from app.automation_engine.workflow_engine import WorkflowEngine


automation_bp = Blueprint("automation", __name__)


# ==========================================
# SECTION: Workflow Rules
# ==========================================
@automation_bp.post("/api/v1/automation/trigger")
@login_required
def trigger_automation_event():
    """Trigger an automation event manually."""
    payload = request.get_json(silent=True) or {}
    engine = WorkflowEngine(tenant_id=current_user.tenant_id, actor_user_id=current_user.id)
    result = engine.trigger_event(payload.get("event_name", ""), payload.get("payload", {}))
    return jsonify({"success": True, "data": result}), 200


# ==========================================
# SECTION: Communication
# ==========================================
@automation_bp.get("/api/v1/automation/callbacks/due")
@login_required
def due_callbacks_api():
    """Return callbacks due within the next 24 hours."""
    service = SchedulerService(tenant_id=current_user.tenant_id, actor_user_id=current_user.id)
    data = service.get_due_callbacks(within_hours=int(request.args.get("within_hours", 24)))
    return jsonify({"success": True, "data": data}), 200


# ==========================================
# SECTION: Scheduling
# ==========================================
@automation_bp.get("/api/v1/automation/campaign-roi")
@login_required
def campaign_roi_api():
    """Return campaign attribution ROI metrics."""
    service = CampaignAttributionService(tenant_id=current_user.tenant_id, actor_user_id=current_user.id)
    return jsonify({"success": True, "data": service.calculate_campaign_roi()}), 200


# ==========================================
# SECTION: Tracking
# ==========================================
@automation_bp.get("/api/v1/automation/meta/pixel")
def pixel_snippet_api():
    """Return Meta Pixel base snippet placeholder."""
    service = MetaTrackingService()
    return jsonify({"success": True, "data": {"snippet": service.inject_pixel_base()}}), 200
