"""Vector store abstraction for RAG memory.

The default implementation keeps a local JSON-backed memory index and
can optionally use FAISS or Chroma when those libraries are installed.
"""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from flask import current_app, has_app_context


# ==========================================
# SECTION: Embeddings
# ==========================================
# Embeddings are supplied by EmbeddingService and stored with metadata.


# ==========================================
# SECTION: Vector Search
# ==========================================
class VectorStore:
    """Small vector store abstraction with optional FAISS/Chroma support."""

    def __init__(self) -> None:
        self.backend = self._get_config("RAG_VECTOR_BACKEND", "faiss").lower()
        self.index_name = self._get_config("RAG_INDEX_NAME", "crm_knowledge")
        self.store_dir = Path(self._get_config("RAG_STORE_DIR", "rag_store"))
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.store_dir / f"{self.index_name}.json"
        self._memory_cache: list[dict[str, Any]] | None = None

    def create_index(self) -> None:
        """Create local index container if it does not exist yet."""
        if self.backend == "chroma":
            self._get_chroma_collection()
            return
        if self.backend == "faiss":
            self._get_faiss_components()
        if not self.index_file.exists():
            self.index_file.write_text("[]", encoding="utf-8")

    def add_documents(self, documents: list[dict[str, Any]]) -> int:
        """Add or replace vectorized documents in the store."""
        if not documents:
            return 0

        self.create_index()

        if self.backend == "chroma":
            return self._add_documents_chroma(documents)

        existing = self._load_records()
        existing_map = {record["id"]: record for record in existing}
        for document in documents:
            existing_map[document["id"]] = document
        merged = list(existing_map.values())
        self._save_records(merged)
        if self.backend == "faiss":
            self._persist_faiss_index(merged)
        return len(documents)

    def search(
        self,
        query_vector: list[float],
        *,
        top_k: int = 5,
        tenant_id: int | None = None,
        namespaces: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search the vector memory for semantically similar records."""
        self.create_index()
        if self.backend == "chroma":
            return self._search_chroma(
                query_vector,
                top_k=top_k,
                tenant_id=tenant_id,
                namespaces=namespaces,
            )
        if self.backend == "faiss":
            return self._search_faiss(
                query_vector,
                top_k=top_k,
                tenant_id=tenant_id,
                namespaces=namespaces,
            )
        return self._search_local(
            query_vector,
            top_k=top_k,
            tenant_id=tenant_id,
            namespaces=namespaces,
        )

    def delete_vectors(
        self,
        *,
        tenant_id: int | None = None,
        namespace: str | None = None,
        record_ids: list[str] | None = None,
    ) -> int:
        """Delete vectors by tenant, namespace, or explicit record ids."""
        records = self._load_records()
        before_count = len(records)
        record_id_set = set(record_ids or [])

        filtered = []
        for record in records:
            matches_tenant = tenant_id is None or record.get("tenant_id") == tenant_id
            matches_namespace = namespace is None or record.get("namespace") == namespace
            matches_record_id = not record_id_set or record.get("id") in record_id_set

            should_remove = matches_tenant and matches_namespace and matches_record_id
            if not should_remove:
                filtered.append(record)

        self._save_records(filtered)
        if self.backend == "faiss":
            self._persist_faiss_index(filtered)
        return before_count - len(filtered)

    def count(self, *, tenant_id: int | None = None) -> int:
        """Return the number of vectors currently stored."""
        records = self._load_records()
        if tenant_id is None:
            return len(records)
        return sum(1 for record in records if record.get("tenant_id") == tenant_id)

    def has_tenant_memory(self, tenant_id: int) -> bool:
        """Check whether a tenant already has indexed memory."""
        return self.count(tenant_id=tenant_id) > 0

    def _search_local(
        self,
        query_vector: list[float],
        *,
        top_k: int,
        tenant_id: int | None,
        namespaces: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Fallback cosine-similarity search without external vector DB."""
        records = self._filter_records(
            self._load_records(),
            tenant_id=tenant_id,
            namespaces=namespaces,
        )
        if not records:
            return []

        query = np.asarray(query_vector, dtype=float)
        results = []
        for record in records:
            vector = np.asarray(record.get("embedding", []), dtype=float)
            if not len(vector):
                continue
            score = float(np.dot(query, vector))
            results.append(
                {
                    "id": record.get("id"),
                    "text": record.get("text"),
                    "metadata": record.get("metadata", {}),
                    "namespace": record.get("namespace"),
                    "tenant_id": record.get("tenant_id"),
                    "score": round(score, 4),
                }
            )

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]

    def _search_faiss(
        self,
        query_vector: list[float],
        *,
        top_k: int,
        tenant_id: int | None,
        namespaces: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Search with FAISS when installed, otherwise fall back locally."""
        faiss_bundle = self._get_faiss_components()
        if faiss_bundle is None:
            return self._search_local(
                query_vector,
                top_k=top_k,
                tenant_id=tenant_id,
                namespaces=namespaces,
            )

        faiss, index = faiss_bundle
        records = self._load_records()
        filtered = self._filter_records(records, tenant_id=tenant_id, namespaces=namespaces)
        if not filtered:
            return []

        matrix = np.asarray([record["embedding"] for record in filtered], dtype="float32")
        if matrix.size == 0:
            return []

        local_index = faiss.IndexFlatIP(matrix.shape[1])
        local_index.add(matrix)
        scores, positions = local_index.search(
            np.asarray([query_vector], dtype="float32"),
            min(top_k, len(filtered)),
        )

        results = []
        for score, position in zip(scores[0], positions[0]):
            if position < 0:
                continue
            record = filtered[int(position)]
            results.append(
                {
                    "id": record.get("id"),
                    "text": record.get("text"),
                    "metadata": record.get("metadata", {}),
                    "namespace": record.get("namespace"),
                    "tenant_id": record.get("tenant_id"),
                    "score": round(float(score), 4),
                }
            )
        return results

    def _search_chroma(
        self,
        query_vector: list[float],
        *,
        top_k: int,
        tenant_id: int | None,
        namespaces: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Search with Chroma when installed, otherwise fall back locally."""
        collection = self._get_chroma_collection()
        if collection is None:
            return self._search_local(
                query_vector,
                top_k=top_k,
                tenant_id=tenant_id,
                namespaces=namespaces,
            )

        where_clause: dict[str, Any] | None = None
        if tenant_id is not None:
            where_clause = {"tenant_id": tenant_id}

        result = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_clause,
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        items = []
        for record_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            namespace = (metadata or {}).get("namespace")
            if namespaces and namespace not in namespaces:
                continue
            score = round(1 - float(distance), 4)
            items.append(
                {
                    "id": record_id,
                    "text": text,
                    "metadata": metadata or {},
                    "namespace": namespace,
                    "tenant_id": (metadata or {}).get("tenant_id"),
                    "score": score,
                }
            )
        return items

    def _add_documents_chroma(self, documents: list[dict[str, Any]]) -> int:
        """Persist records into Chroma when available."""
        collection = self._get_chroma_collection()
        if collection is None:
            existing = self._load_records()
            existing_map = {record["id"]: record for record in existing}
            for document in documents:
                existing_map[document["id"]] = document
            self._save_records(list(existing_map.values()))
            return len(documents)

        collection.upsert(
            ids=[document["id"] for document in documents],
            embeddings=[document["embedding"] for document in documents],
            documents=[document["text"] for document in documents],
            metadatas=[
                {
                    **document.get("metadata", {}),
                    "namespace": document.get("namespace"),
                    "tenant_id": document.get("tenant_id"),
                }
                for document in documents
            ],
        )
        existing = self._load_records()
        existing_map = {record["id"]: record for record in existing}
        for document in documents:
            existing_map[document["id"]] = document
        self._save_records(list(existing_map.values()))
        return len(documents)

    def _persist_faiss_index(self, records: list[dict[str, Any]]) -> None:
        """Persist a simple FAISS index file when the package is installed."""
        faiss_bundle = self._get_faiss_components()
        if faiss_bundle is None or not records:
            return

        faiss, _ = faiss_bundle
        matrix = np.asarray([record["embedding"] for record in records], dtype="float32")
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        faiss.write_index(index, str(self.store_dir / f"{self.index_name}.faiss"))

    def _get_faiss_components(self):
        """Load FAISS lazily so the app still works without it."""
        try:
            import faiss  # type: ignore
        except Exception:
            return None

        index_path = self.store_dir / f"{self.index_name}.faiss"
        if index_path.exists():
            try:
                index = faiss.read_index(str(index_path))
            except Exception:
                index = None
        else:
            index = None
        return faiss, index

    def _get_chroma_collection(self):
        """Load Chroma collection lazily when chromadb is installed."""
        try:
            import chromadb  # type: ignore
        except Exception:
            return None

        client = chromadb.PersistentClient(path=str(self.store_dir / "chroma"))
        return client.get_or_create_collection(name=self.index_name)

    def _filter_records(
        self,
        records: list[dict[str, Any]],
        *,
        tenant_id: int | None,
        namespaces: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Apply tenant and namespace filtering to stored records."""
        filtered = []
        for record in records:
            if tenant_id is not None and record.get("tenant_id") != tenant_id:
                continue
            if namespaces and record.get("namespace") not in namespaces:
                continue
            filtered.append(record)
        return filtered

    def _load_records(self) -> list[dict[str, Any]]:
        """Load persisted records from local JSON storage."""
        if self._memory_cache is not None:
            return list(self._memory_cache)

        if not self.index_file.exists():
            self._memory_cache = []
            return []

        try:
            records = json.loads(self.index_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            records = []

        self._memory_cache = list(records)
        return list(records)

    def _save_records(self, records: list[dict[str, Any]]) -> None:
        """Persist local record metadata to disk."""
        self._memory_cache = list(records)
        self.index_file.write_text(
            json.dumps(records, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _get_config(key: str, default):
        """Read configuration safely inside or outside app context."""
        if has_app_context():
            return current_app.config.get(key, default)
        return default


# ==========================================
# SECTION: Retrieval Logic
# ==========================================
# Search results are returned as plain dictionaries so downstream AI
# services can format them into prompts or UI payloads.


# ==========================================
# SECTION: Context Builder
# ==========================================
# PromptContextBuilder uses VectorStore search outputs to compose memory.
