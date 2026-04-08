"""API routes for classical ML inference services."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required


# ==========================================
# SECTION: Training Logic
# ==========================================
# Training is triggered through Celery and pipeline modules, not directly
# through these inference API routes.


# ==========================================
# SECTION: Prediction Logic
# ==========================================
ai_ml_bp = Blueprint("ai_ml", __name__)


@ai_ml_bp.post("/api/v1/ai/lead-score")
@login_required
def lead_score_api():
    """Inference endpoint for lead conversion scoring."""
    from app.ai_ml.inference_service import InferenceService

    payload = request.get_json(silent=True) or {}
    service = InferenceService(tenant_id=current_user.tenant_id)

    data = service.predict_lead_score(payload)
    return jsonify({"success": True, "data": data}), 200


@ai_ml_bp.post("/api/v1/ai/eligibility")
@login_required
def eligibility_api():
    """Inference endpoint for approval probability predictions."""
    from app.ai_ml.inference_service import InferenceService

    payload = request.get_json(silent=True) or {}
    service = InferenceService(tenant_id=current_user.tenant_id)

    data = service.predict_eligibility(payload)
    return jsonify({"success": True, "data": data}), 200


@ai_ml_bp.post("/api/v1/ai/lender-rank")
@login_required
def lender_rank_api():
    """Inference endpoint for lender ranking recommendations."""
    from app.ai_ml.inference_service import InferenceService

    payload = request.get_json(silent=True) or {}
    service = InferenceService(tenant_id=current_user.tenant_id)

    data = service.recommend_lenders(payload)
    return jsonify({"success": True, "data": data}), 200


# ==========================================
# SECTION: Serialization
# ==========================================
# Serialization occurs in model classes and registry service, not routes.
