"""Embedding helpers for semantic retrieval.

The service prefers a local sentence-transformer model, but gracefully
falls back to deterministic hash embeddings when optional packages are
not installed yet. This keeps Phase 8 usable in lightweight setups.
"""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Iterable

import numpy as np
from flask import current_app, has_app_context


# ==========================================
# SECTION: Embeddings
# ==========================================
class EmbeddingService:
    """Create vector embeddings for text and document memory."""

    def __init__(self) -> None:
        self.embedding_model_name = self._get_config(
            "RAG_EMBEDDING_MODEL",
            "all-MiniLM-L6-v2",
        )
        self.vector_size = int(self._get_config("RAG_EMBEDDING_DIM", 384))

    def embed_text(self, text: str) -> list[float]:
        """Convert free-form text into an embedding vector.

        Preferred path:
        1. Local sentence-transformers model
        2. Placeholder cloud embedding fallback
        3. Deterministic hash embedding fallback
        """
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            return [0.0] * self.vector_size

        transformer_model = self._load_sentence_transformer()
        if transformer_model is not None:
            vector = transformer_model.encode(normalized_text)
            return self._normalize_vector(vector)

        if self._get_config("RAG_ENABLE_OPENAI_EMBEDDINGS", False):
            return self._fallback_cloud_embedding(normalized_text)

        return self._hash_embedding(normalized_text)

    def embed_document(self, document_text: str) -> list[float]:
        """Convert a document body into an embedding vector."""
        return self.embed_text(document_text)

    def embed_batch(self, texts: Iterable[str]) -> list[list[float]]:
        """Embed a batch of texts for vector-store ingestion."""
        return [self.embed_text(text) for text in texts]

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_sentence_transformer():
        """Load local sentence-transformer model when available."""
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            return None

        model_name = "all-MiniLM-L6-v2"
        if has_app_context():
            model_name = current_app.config.get("RAG_EMBEDDING_MODEL", model_name)

        try:
            return SentenceTransformer(model_name)
        except Exception:
            return None

    def _fallback_cloud_embedding(self, text: str) -> list[float]:
        """Placeholder cloud embedding fallback.

        This intentionally returns a deterministic local vector until a
        real provider client is added in a future phase.
        """
        return self._hash_embedding(f"cloud::{text}")

    def _hash_embedding(self, text: str) -> list[float]:
        """Create deterministic lightweight embeddings without extra libs."""
        vector = np.zeros(self.vector_size, dtype=float)
        tokens = self._normalize_text(text).split()

        if not tokens:
            return vector.tolist()

        for index, token in enumerate(tokens):
            digest = hashlib.sha256(f"{token}:{index}".encode("utf-8")).digest()
            for offset, byte in enumerate(digest):
                position = (index * len(digest) + offset) % self.vector_size
                vector[position] += (byte / 255.0) - 0.5

        return self._normalize_vector(vector)

    def _normalize_vector(self, vector: np.ndarray | list[float]) -> list[float]:
        """Normalize vectors for cosine-similarity search."""
        array = np.asarray(vector, dtype=float)
        norm = np.linalg.norm(array)
        if norm == 0:
            return array.tolist()
        return (array / norm).tolist()

    def _normalize_text(self, text: str) -> str:
        """Normalize user text before embedding."""
        return " ".join(str(text or "").strip().split())

    @staticmethod
    def _get_config(key: str, default):
        """Read configuration safely with or without app context."""
        if has_app_context():
            return current_app.config.get(key, default)
        return default


# ==========================================
# SECTION: Vector Search
# ==========================================
# Vector store integrations consume the normalized embeddings above.


# ==========================================
# SECTION: Retrieval Logic
# ==========================================
# Knowledge retrieval calls this service for both ingestion and queries.


# ==========================================
# SECTION: Context Builder
# ==========================================
# PromptContextBuilder uses retrieval outputs generated from these vectors.
