"""Provider clients for local and cloud LLM backends."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProviderResult:
    """Normalized provider response payload."""

    provider: str
    content: str
    model: str
    simulated: bool = True


class BaseProvider:
    """Shared provider helper with safe placeholder generation."""

    provider_name = "base"

    def __init__(self, *, model_name: str = "", api_key: str = "", endpoint: str = "") -> None:
        self.model_name = model_name
        self.api_key = api_key
        self.endpoint = endpoint

    def generate_response(self, prompt: str) -> ProviderResult:
        """Generate a placeholder response with safe wrappers."""
        try:
            content = self._simulate_response(prompt)
            return ProviderResult(
                provider=self.provider_name,
                content=content,
                model=self.model_name or self.provider_name,
                simulated=True,
            )
        except Exception as exc:  # pragma: no cover - defensive provider wrapper
            raise RuntimeError(f"{self.provider_name} provider failed: {exc}") from exc

    def _simulate_response(self, prompt: str) -> str:
        """Fallback response when real provider integration is absent."""
        snippet = " ".join(str(prompt).split())[:280]
        return f"[{self.provider_name}:{self.model_name or 'default'}] {snippet}"


# ==========================================
# SECTION: Provider Routing
# ==========================================
class OllamaProvider(BaseProvider):
    """Local provider wrapper for Ollama-hosted models such as Llama/Mistral."""

    provider_name = "ollama"


class OpenAIProvider(BaseProvider):
    """Cloud provider wrapper for OpenAI."""

    provider_name = "openai"


class ClaudeProvider(BaseProvider):
    """Cloud provider wrapper for Claude."""

    provider_name = "claude"


class GeminiProvider(BaseProvider):
    """Cloud provider wrapper for Gemini."""

    provider_name = "gemini"


# ==========================================
# SECTION: Prompt Templates
# ==========================================
# Providers receive already-rendered prompt text from PromptManager.


# ==========================================
# SECTION: Assistant Logic
# ==========================================
# Real HTTP transport can be added later without changing the services
# that depend on these provider classes.
