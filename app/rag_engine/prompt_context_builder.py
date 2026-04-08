"""Prompt context formatter for memory-aware assistant prompts."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.rag_engine.retriever import KnowledgeRetriever


# ==========================================
# SECTION: Embeddings
# ==========================================
# This module does not embed directly; it consumes retrieval outputs.


# ==========================================
# SECTION: Vector Search
# ==========================================
# Retrieval is delegated to KnowledgeRetriever before formatting.


# ==========================================
# SECTION: Retrieval Logic
# ==========================================
class PromptContextBuilder:
    """Build readable prompt context from semantically retrieved memory."""

    def __init__(self) -> None:
        self.retriever = KnowledgeRetriever()

    def build_context(
        self,
        query: str,
        *,
        tenant_id: int,
        top_k: int = 5,
        namespaces: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build memory context text plus structured retrieval metadata."""
        results = self.retriever.retrieve_relevant_context(
            query,
            tenant_id=tenant_id,
            top_k=top_k,
            namespaces=namespaces,
        )
        context_lines = []
        cards = []

        for index, item in enumerate(results, start=1):
            line = (
                f"{index}. [{item.get('namespace', 'memory')}] "
                f"{item.get('text', '')} "
                f"(score={item.get('score', 0)})"
            )
            context_lines.append(line.strip())
            cards.append(
                {
                    "title": item.get("namespace", "memory").replace("_", " ").title(),
                    "summary": item.get("text", ""),
                    "score": item.get("score", 0),
                    "metadata": item.get("metadata", {}),
                }
            )

        memory_context = "\n".join(context_lines) if context_lines else "No relevant memory found."
        return {
            "memory_context": memory_context,
            "retrieved_items": results,
            "cards": cards,
        }


# ==========================================
# SECTION: Context Builder
# ==========================================
# This is the final formatting layer before memory is injected into prompts.
