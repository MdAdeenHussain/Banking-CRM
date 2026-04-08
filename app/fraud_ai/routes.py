"""Fraud AI API routes."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.fraud_ai.alert_service import FraudAlertService
from app.fraud_ai.device_fingerprint_service import DeviceFingerprintService
from app.fraud_ai.forensic_engine import ForensicEngine
from app.fraud_ai.fraud_reasoning_service import FraudReasoningService
from app.fraud_ai.risk_scoring_service import FraudRiskScoringService
from app.automation_engine.workflow_engine import WorkflowEngine
from app.models.document import Document


fraud_ai_bp = Blueprint("fraud_ai", __name__)


# ==========================================
# SECTION: Fraud Detection
# ==========================================
@fraud_ai_bp.post("/api/v1/fraud/check")
@login_required
def fraud_check_api():
    """Run full fraud scoring workflow for a document-linked case."""
    payload = request.get_json(silent=True) or {}
    service = FraudRiskScoringService(
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
    )
    assessment = service.evaluate_case(
        document_id=int(payload.get("document_id")),
        device_payload=payload.get("device_payload"),
        identifiers=payload.get("identifiers"),
        bank_statement_data=payload.get("bank_statement_data"),
    )

    reasoning = FraudReasoningService(current_user.tenant_id).generate_reasoning(
        {
            "rule_score": assessment["components"]["rule_score"],
            "anomaly_score": assessment["components"]["anomaly_score"],
            "device_score": assessment["components"]["device_score"],
            "identity_score": assessment["components"]["identity_score"],
            "forensic_score": assessment["components"]["forensic_score"],
            "reasons": assessment["identity_result"].get("reasons", [])
            + assessment["device_result"].get("multiple_identity_result", {}).get("reasons", [])
            + list(assessment["forensic_result"].get("flags", {}).values()),
            "observations": [
                f"risk_level={assessment['risk_level']}",
                f"document_id={assessment['document_id']}",
            ],
        }
    )

    alerts = FraudAlertService(current_user.tenant_id).trigger_alerts(
        risk_score=assessment["risk_score"],
        risk_level=assessment["risk_level"],
        entity_label=f"Document #{assessment['document_id']}",
        message=reasoning["reason"],
    )
    WorkflowEngine(
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
    ).trigger_event(
        "fraud_detected",
        {
            "fraud_score": assessment["risk_score"],
            "customer_name": getattr(Document.query.get(assessment["document_id"]).customer, "full_name", "Customer"),
            "loan_type": getattr(getattr(Document.query.get(assessment["document_id"]), "application", None), "loan_type", "loan"),
            "reasons": assessment["identity_result"].get("reasons", [])
            + assessment["device_result"].get("multiple_identity_result", {}).get("reasons", [])
            + list(assessment["forensic_result"].get("flags", {}).values()),
        },
    )

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    **assessment,
                    "reasoning": reasoning,
                    "alerts_created": len(alerts),
                },
            }
        ),
        200,
    )


# ==========================================
# SECTION: Anomaly Scoring
# ==========================================
@fraud_ai_bp.post("/api/v1/fraud/analyze-document")
@login_required
def analyze_document_api():
    """Run forensic analysis for one document."""
    payload = request.get_json(silent=True) or {}
    document = Document.query.filter_by(
        id=int(payload.get("document_id")),
        tenant_id=current_user.tenant_id,
        is_deleted=False,
    ).first_or_404()
    service = ForensicEngine(tenant_id=current_user.tenant_id)
    result = service.analyze_document(
        document,
        bank_statement_data=payload.get("bank_statement_data"),
        application_name=payload.get("application_name"),
    )
    return jsonify({"success": True, "data": result}), 200


@fraud_ai_bp.post("/api/v1/fraud/device-check")
@login_required
def device_check_api():
    """Run device fingerprint risk analysis."""
    payload = request.get_json(silent=True) or {}
    service = DeviceFingerprintService(
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
    )
    result = service.analyze_device(payload, persist=True)
    return jsonify({"success": True, "data": result}), 200


# ==========================================
# SECTION: Forensics
# ==========================================
@fraud_ai_bp.post("/api/v1/fraud/reasoning")
@login_required
def fraud_reasoning_api():
    """Generate explainable fraud reasoning."""
    payload = request.get_json(silent=True) or {}
    service = FraudReasoningService(tenant_id=current_user.tenant_id)
    result = service.generate_reasoning(payload)
    return jsonify({"success": True, "data": result}), 200


# ==========================================
# SECTION: Alerts
# ==========================================
@fraud_ai_bp.get("/api/v1/fraud/alerts")
@login_required
def fraud_alerts_api():
    """Return fraud alerts for current tenant/user."""
    service = FraudAlertService(tenant_id=current_user.tenant_id)
    user_id = None if current_user.role in {"owner", "platform", "branch"} else current_user.id
    alerts = service.list_alerts(user_id=user_id)
    return jsonify({"success": True, "data": service.serialize_alerts(alerts)}), 200
