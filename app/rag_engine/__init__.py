"""RAG engine package exports.

This package contains the retrieval, vector memory, and prompt context
helpers used by Phase 8 semantic search features.
"""

# ==========================================
# SECTION: Embeddings
# ==========================================
# Package-level exports keep imports predictable for the rest of the app.

# ==========================================
# SECTION: Vector Search
# ==========================================
# The concrete vector database implementation lives in vector_store.py.

# ==========================================
# SECTION: Retrieval Logic
# ==========================================
from app.rag_engine.case_similarity_service import CaseSimilarityService
from app.rag_engine.embedding_service import EmbeddingService
from app.rag_engine.knowledge_loader import KnowledgeLoader
from app.rag_engine.prompt_context_builder import PromptContextBuilder
from app.rag_engine.retriever import KnowledgeRetriever
from app.rag_engine.vector_store import VectorStore


# ==========================================
# SECTION: Context Builder
# ==========================================
__all__ = [
    "EmbeddingService",
    "VectorStore",
    "KnowledgeLoader",
    "KnowledgeRetriever",
    "PromptContextBuilder",
    "CaseSimilarityService",
]
