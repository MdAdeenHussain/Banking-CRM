"""Explainable fraud reasoning service using LLM + memory."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.ai_hub.assistant_service import AssistantService


# ==========================================
# SECTION: Fraud Detection
# ==========================================
class FraudReasoningService:
    """Generate explainable fraud reasoning from scored signals."""

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id
        self.assistant = AssistantService()

    def generate_reasoning(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate compliance-friendly explanation for fraud risk."""
        rule_score = payload.get("rule_score", 0)
        anomaly_score = payload.get("anomaly_score", 0)
        device_score = payload.get("device_score", 0)
        identity_score = payload.get("identity_score", 0)
        forensic_score = payload.get("forensic_score", 0)
        reasons = payload.get("reasons", [])
        observations = payload.get("observations", [])

        result = self.assistant.generate_text(
            task_type="fraud_reasoning",
            prompt_key="fraud_reasoning",
            prompt_values={
                "rule_score": rule_score,
                "anomaly_score": anomaly_score,
                "device_score": device_score,
                "identity_score": identity_score,
                "forensic_score": forensic_score,
                "reasons": ", ".join(str(reason) for reason in reasons) or "No explicit fraud reasons supplied.",
                "observations": ", ".join(str(item) for item in observations) or "No supporting observations supplied.",
            },
            sensitive=True,
            tenant_id=self.tenant_id,
            memory_query=(
                f"fraud reasoning for rule score {rule_score}, anomaly score {anomaly_score}, "
                f"device score {device_score}, identity score {identity_score}, forensic score {forensic_score}, "
                f"observations {observations}"
            ),
            memory_namespaces=["fraud_cases", "compliance_notes", "rejections"],
        )
        return {
            "reason": result["content"],
            "provider": result["provider"],
            "model": result["model"],
            "generated_by": "llm_assistant",
            "memory_context": result["memory_context"],
            "retrieved_items": result["retrieved_items"],
        }


# ==========================================
# SECTION: Anomaly Scoring
# ==========================================
# This service explains scores produced elsewhere instead of training them.


# ==========================================
# SECTION: Forensics
# ==========================================
# Forensic observations are included in the reasoning prompt.


# ==========================================
# SECTION: Alerts
# ==========================================
# Human-readable fraud reasoning is suitable for notification messages.
