"""Message drafting engine for WhatsApp, email, and SMS."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.ai_hub.assistant_service import AssistantService


# ==========================================
# SECTION: Provider Routing
# ==========================================
# Generic drafts can use cloud fallback, but PII-containing payloads are
# still routed locally by AIProviderRouter.


# ==========================================
# SECTION: Prompt Templates
# ==========================================
# Draft prompts are sourced from PromptManager via AssistantService.


# ==========================================
# SECTION: Assistant Logic
# ==========================================
class MessageDraftService:
    """Creates professional customer-facing communication drafts."""

    def __init__(self) -> None:
        self.assistant = AssistantService()

    def draft_whatsapp(
        self,
        payload: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Draft a WhatsApp follow-up message."""
        return self._draft("whatsapp_draft", payload, tenant_id=tenant_id)

    def draft_email(
        self,
        payload: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Draft a professional follow-up email."""
        return self._draft("email_draft", payload, tenant_id=tenant_id)

    def draft_sms(
        self,
        payload: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Draft a short SMS reminder."""
        return self._draft("sms_draft", payload, tenant_id=tenant_id)

    def _draft(
        self,
        prompt_key: str,
        payload: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Internal message drafting helper."""
        result = self.assistant.generate_text(
            task_type="message_draft",
            prompt_key=prompt_key,
            prompt_values={
                "customer_name": payload.get("customer_name", "Customer"),
                "loan_type": payload.get("loan_type", "loan"),
                "pending_docs": payload.get("pending_docs", "no pending documents"),
                "next_follow_up": payload.get("next_follow_up", "tomorrow"),
            },
            sensitive=bool(
                payload.get("customer_name")
                or payload.get("mobile")
                or payload.get("email")
            ),
            tenant_id=tenant_id,
            memory_query=(
                f"Customer {payload.get('customer_name', 'customer')} for {payload.get('loan_type', 'loan')} "
                f"pending {payload.get('pending_docs', 'documents')} follow-up {payload.get('next_follow_up', 'soon')}"
            ),
            memory_namespaces=["call_transcripts", "historical_applications"],
        )
        return {
            "draft": result["content"],
            "provider": result["provider"],
            "model": result["model"],
            "generated_by": "llm_assistant",
            "memory_context": result["memory_context"],
            "retrieved_items": result["retrieved_items"],
        }
