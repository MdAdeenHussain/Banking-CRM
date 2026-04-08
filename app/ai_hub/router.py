"""Provider router for local-first and cloud-fallback LLM orchestration."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from flask import current_app

from app.ai_hub.providers import (
    ClaudeProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
    ProviderResult,
)


class AIProviderRouter:
    """Routes LLM tasks to local or cloud providers based on sensitivity."""

    SENSITIVE_TASKS = {
        "call_summary",
        "rejection_explanation",
        "compliance_note",
        "fraud_report",
        "audit_log_summary",
    }

    SENSITIVE_FIELDS = {
        "pan",
        "aadhaar",
        "salary_slip",
        "bank_statement",
        "pii",
        "customer_name",
        "mobile",
        "email",
    }

    def __init__(self) -> None:
        self.max_retries = int(current_app.config.get("AI_PROVIDER_RETRIES", 2))

    # ==========================================
    # SECTION: Provider Routing
    # ==========================================
    def route_request(self, task_type: str, sensitive: bool = False) -> list[object]:
        """Route request to correct provider chain.

        Sensitive tasks -> local only.
        General tasks -> local first, then cloud fallback.
        """
        is_sensitive = sensitive or task_type in self.SENSITIVE_TASKS
        local_chain = self._local_chain()

        if is_sensitive:
            return local_chain

        if not current_app.config.get("AI_ALLOW_CLOUD", True):
            return local_chain

        return local_chain + self._cloud_chain()

    def execute(
        self,
        *,
        task_type: str,
        prompt: str,
        sensitive: bool = False,
        context: dict[str, Any] | None = None,
    ) -> ProviderResult:
        """Execute provider chain with retry logic and fallback order."""
        inferred_sensitive = sensitive or self._payload_is_sensitive(context or {})
        providers = self.route_request(task_type=task_type, sensitive=inferred_sensitive)
        last_error: Exception | None = None

        for provider in providers:
            for _attempt in range(self.max_retries):
                try:
                    return provider.generate_response(prompt)
                except Exception as exc:  # pragma: no cover - defensive fallback logic
                    last_error = exc

        raise RuntimeError(f"All AI providers failed for task={task_type}: {last_error}")

    def _payload_is_sensitive(self, context: dict[str, Any]) -> bool:
        """Detect obvious PII or regulated banking fields in payload."""
        payload_keys = {str(key).lower() for key in context.keys()}
        return not self.SENSITIVE_FIELDS.isdisjoint(payload_keys)

    def _local_chain(self) -> list[object]:
        """Build local-first provider list using Ollama-hosted models."""
        primary_model = current_app.config.get("AI_LOCAL_PRIMARY_MODEL", "llama3.1")
        secondary_model = current_app.config.get("AI_LOCAL_SECONDARY_MODEL", "mistral")
        endpoint = current_app.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
        return [
            OllamaProvider(model_name=primary_model, endpoint=endpoint),
            OllamaProvider(model_name=secondary_model, endpoint=endpoint),
        ]

    def _cloud_chain(self) -> list[object]:
        """Build cloud fallback chain: OpenAI -> Claude -> Gemini."""
        return [
            OpenAIProvider(
                model_name=current_app.config.get("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                api_key=current_app.config.get("OPENAI_API_KEY", ""),
                endpoint=current_app.config.get("OPENAI_BASE_URL", ""),
            ),
            ClaudeProvider(
                model_name=current_app.config.get("CLAUDE_MODEL_NAME", "claude-3-5-sonnet"),
                api_key=current_app.config.get("CLAUDE_API_KEY", ""),
                endpoint=current_app.config.get("CLAUDE_BASE_URL", ""),
            ),
            GeminiProvider(
                model_name=current_app.config.get("GEMINI_MODEL_NAME", "gemini-1.5-pro"),
                api_key=current_app.config.get("GEMINI_API_KEY", ""),
                endpoint=current_app.config.get("GEMINI_BASE_URL", ""),
            ),
        ]


# ==========================================
# SECTION: Prompt Templates
# ==========================================
# Prompts are rendered before router execution so routing logic stays
# focused on privacy, fallback, and provider selection.


# ==========================================
# SECTION: Assistant Logic
# ==========================================
# Services call router.execute(...) to keep local/cloud fallback behavior
# consistent across all assistant features.
