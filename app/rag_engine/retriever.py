"""Semantic retrieval service for Phase 8 knowledge memory."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.rag_engine.embedding_service import EmbeddingService
from app.rag_engine.knowledge_loader import KnowledgeLoader
from app.rag_engine.vector_store import VectorStore


# ==========================================
# SECTION: Embeddings
# ==========================================
# Query embeddings are created through EmbeddingService before search.


# ==========================================
# SECTION: Vector Search
# ==========================================
class KnowledgeRetriever:
    """Retrieve relevant semantic memory for AI features and APIs."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.knowledge_loader = KnowledgeLoader()

    def retrieve_relevant_context(
        self,
        query: str,
        *,
        tenant_id: int,
        top_k: int = 5,
        namespaces: list[str] | None = None,
        auto_refresh: bool = True,
    ) -> list[dict[str, Any]]:
        """Perform semantic retrieval against tenant knowledge memory."""
        if auto_refresh and not self.vector_store.has_tenant_memory(tenant_id):
            self.refresh_tenant_knowledge(tenant_id)

        query_vector = self.embedding_service.embed_text(query)
        return self.vector_store.search(
            query_vector,
            top_k=top_k,
            tenant_id=tenant_id,
            namespaces=namespaces,
        )

    def refresh_tenant_knowledge(self, tenant_id: int) -> int:
        """Rebuild or append tenant memory from application database records."""
        documents = self.knowledge_loader.load_all_sources(tenant_id)
        return self.vector_store.add_documents(documents)

    def retrieve_text_only(
        self,
        query: str,
        *,
        tenant_id: int,
        top_k: int = 5,
        namespaces: list[str] | None = None,
    ) -> list[str]:
        """Return only the text fragments from retrieval results."""
        results = self.retrieve_relevant_context(
            query,
            tenant_id=tenant_id,
            top_k=top_k,
            namespaces=namespaces,
        )
        return [result.get("text", "") for result in results]


# ==========================================
# SECTION: Retrieval Logic
# ==========================================
# This class is the main entry point used by APIs and prompt builders.


# ==========================================
# SECTION: Context Builder
# ==========================================
# PromptContextBuilder formats retrieval outputs into human-readable context.
