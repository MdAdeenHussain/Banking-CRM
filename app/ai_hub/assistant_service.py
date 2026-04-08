"""Shared LLM assistant orchestration service."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.ai_hub.prompt_manager import PromptManager
from app.ai_hub.router import AIProviderRouter
from app.rag_engine.prompt_context_builder import PromptContextBuilder


# ==========================================
# SECTION: Provider Routing
# ==========================================
# Routing decisions are delegated to AIProviderRouter so task services can
# stay focused on business behavior rather than provider selection rules.


# ==========================================
# SECTION: Prompt Templates
# ==========================================
# Prompt keys are resolved through PromptManager.render().


# ==========================================
# SECTION: Assistant Logic
# ==========================================
class AssistantService:
    """Thin orchestration layer for all LLM-assisted business features."""

    def __init__(self) -> None:
        self.router = AIProviderRouter()
        self.context_builder = PromptContextBuilder()

    def generate_text(
        self,
        *,
        task_type: str,
        prompt_key: str,
        prompt_values: dict[str, Any],
        sensitive: bool = False,
        tenant_id: int | None = None,
        memory_query: str | None = None,
        memory_namespaces: list[str] | None = None,
    ) -> dict[str, Any]:
        """Render prompt and execute through provider router."""
        memory_payload = {
            "memory_context": "No relevant memory found.",
            "retrieved_items": [],
            "cards": [],
        }
        rendered_values = dict(prompt_values)

        if tenant_id and memory_query:
            memory_payload = self.context_builder.build_context(
                memory_query,
                tenant_id=tenant_id,
                top_k=5,
                namespaces=memory_namespaces,
            )

        rendered_values.setdefault("memory_context", memory_payload["memory_context"])
        prompt = PromptManager.render(prompt_key, **rendered_values)
        result = self.router.execute(
            task_type=task_type,
            prompt=prompt,
            sensitive=sensitive,
            context=rendered_values,
        )
        content = result.content
        if result.simulated:
            content = self._build_simulated_narrative(task_type, rendered_values)
        return {
            "content": content,
            "provider": result.provider,
            "model": result.model,
            "simulated": result.simulated,
            "memory_context": memory_payload["memory_context"],
            "retrieved_items": memory_payload["retrieved_items"],
            "memory_cards": memory_payload["cards"],
        }

    def explain_rejection(
        self,
        application_data: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate borrower-friendly rejection explanation."""
        memory_query = (
            f"Rejected {application_data.get('loan_type', 'loan')} application "
            f"due to {application_data.get('decision_reason', 'threshold mismatch')} "
            f"with FOIR {application_data.get('foir', 'N/A')} and credit score "
            f"{application_data.get('credit_score', 'N/A')}"
        )
        result = self.generate_text(
            task_type="rejection_explanation",
            prompt_key="rejection_explanation",
            prompt_values={
                "lender": application_data.get("lender", "Selected lender"),
                "foir": application_data.get("foir", "N/A"),
                "credit_score": application_data.get("credit_score", "N/A"),
                "decision_reason": application_data.get(
                    "decision_reason",
                    "Current profile does not meet lender thresholds.",
                ),
                "next_step": application_data.get(
                    "next_step",
                    "Improve financial profile or consider a secured option.",
                ),
            },
            sensitive=True,
            tenant_id=tenant_id,
            memory_query=memory_query,
            memory_namespaces=["rejections", "lender_rules", "historical_applications"],
        )
        return {
            "explanation": result["content"],
            "provider": result["provider"],
            "model": result["model"],
            "generated_by": "llm_assistant",
            "memory_context": result["memory_context"],
            "retrieved_items": result["retrieved_items"],
        }

    def _build_simulated_narrative(self, task_type: str, prompt_values: dict[str, Any]) -> str:
        """Return useful local placeholder narratives for Phase 7 flows."""
        if task_type == "call_summary":
            transcript = str(prompt_values.get("transcript", ""))
            narrative = (
                "Customer is exploring a loan requirement and expects quick guidance. "
                f"Conversation indicates follow-up planning is needed. Transcript length: {len(transcript.split())} words."
            )
            return self._append_memory_hint(narrative, prompt_values)

        if task_type == "next_action":
            narrative = (
                f"Recommended action is to {prompt_values.get('recommended_action', 'continue follow-up')}. "
                f"Current stage is {prompt_values.get('lead_stage', 'CONTACTED')} and the pending focus is "
                f"{prompt_values.get('pending_item', 'general qualification')}."
            )
            return self._append_memory_hint(narrative, prompt_values)

        if task_type == "message_draft":
            narrative = (
                f"Hello {prompt_values.get('customer_name', 'Customer')}, this is a quick follow-up regarding your "
                f"{prompt_values.get('loan_type', 'loan')}. Please share {prompt_values.get('pending_docs', 'the pending items')} "
                f"so we can move ahead. We will reconnect {prompt_values.get('next_follow_up', 'soon')}."
            )
            return self._append_memory_hint(narrative, prompt_values)

        if task_type == "rejection_explanation":
            narrative = (
                f"Based on the current FOIR of {prompt_values.get('foir', 'N/A')} and credit score of "
                f"{prompt_values.get('credit_score', 'N/A')}, the lender {prompt_values.get('lender', 'selected lender')} "
                f"could not approve the application. A practical next step is to {prompt_values.get('next_step', 'review the profile and reapply later')}."
            )
            return self._append_memory_hint(narrative, prompt_values)

        if task_type == "branch_report":
            narrative = (
                f"{prompt_values.get('branch_name', 'The branch')} recorded {prompt_values.get('lead_volume', 0)} leads and "
                f"{prompt_values.get('sanction_count', 0)} key outcomes, with conversion movement at "
                f"{prompt_values.get('conversion_change', '0%')}. Main focus should be to "
                f"{prompt_values.get('focus_area', 'improve operational discipline')}."
            )
            return self._append_memory_hint(narrative, prompt_values)

        if task_type == "fraud_reasoning":
            narrative = (
                f"Fraud assessment is elevated because rule score is {prompt_values.get('rule_score', 0)}, "
                f"anomaly score is {prompt_values.get('anomaly_score', 0)}, device score is "
                f"{prompt_values.get('device_score', 0)}, identity score is {prompt_values.get('identity_score', 0)}, "
                f"and forensic score is {prompt_values.get('forensic_score', 0)}. "
                f"Key reasons: {prompt_values.get('reasons', 'No explicit reasons supplied')}."
            )
            return self._append_memory_hint(narrative, prompt_values)

        return "LLM placeholder response generated successfully."

    def _append_memory_hint(self, narrative: str, prompt_values: dict[str, Any]) -> str:
        """Append a short memory hint when retrieved context is available."""
        memory_context = str(prompt_values.get("memory_context", "")).strip()
        if not memory_context or memory_context == "No relevant memory found.":
            return narrative

        first_line = memory_context.splitlines()[0]
        return f"{narrative} Retrieved memory suggests: {first_line}"
