"""Next best action engine using rules plus LLM narration."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.ai_hub.assistant_service import AssistantService


# ==========================================
# SECTION: Provider Routing
# ==========================================
# Next-best-action advice may contain customer context, so services can
# mark it sensitive when lead payloads include PII.


# ==========================================
# SECTION: Prompt Templates
# ==========================================
# Prompt text comes from PromptManager via AssistantService.


# ==========================================
# SECTION: Assistant Logic
# ==========================================
class NextActionService:
    """Combines business rules with LLM-style narrative advice."""

    def __init__(self) -> None:
        self.assistant = AssistantService()

    def recommend(
        self,
        lead_data: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate next best action for agent workflow."""
        docs_uploaded = bool(lead_data.get("docs_uploaded", False))
        stale_days = int(lead_data.get("stale_days", 0) or 0)
        credit_score = int(lead_data.get("credit_score", 0) or 0)
        pending_item = str(lead_data.get("pending_item", "general follow-up"))
        lead_stage = str(lead_data.get("lead_stage", "CONTACTED"))

        if docs_uploaded:
            rule_action = "submit profile to matching lenders"
        elif stale_days > 3:
            rule_action = "priority callback to revive the lead"
        elif credit_score and credit_score < 650:
            rule_action = "discuss secured loan or co-applicant option"
        else:
            rule_action = "continue qualification and collect required documents"

        narrative = self.assistant.generate_text(
            task_type="next_action",
            prompt_key="next_action",
            prompt_values={
                "lead_stage": lead_stage,
                "docs_uploaded": docs_uploaded,
                "stale_days": stale_days,
                "credit_score": credit_score,
                "pending_item": pending_item,
                "recommended_action": rule_action,
            },
            sensitive=bool(lead_data.get("customer_name") or lead_data.get("mobile")),
            tenant_id=tenant_id,
            memory_query=(
                f"Lead stage {lead_stage}, docs uploaded {docs_uploaded}, stale days {stale_days}, "
                f"credit score {credit_score}, pending item {pending_item}"
            ),
            memory_namespaces=["historical_applications", "call_transcripts", "lender_rules"],
        )

        return {
            "recommended_action": rule_action,
            "advice": narrative["content"],
            "provider": narrative["provider"],
            "model": narrative["model"],
            "generated_by": "llm_assistant",
            "memory_context": narrative["memory_context"],
            "retrieved_items": narrative["retrieved_items"],
        }
