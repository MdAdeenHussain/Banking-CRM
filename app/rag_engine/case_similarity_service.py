"""Case similarity helpers for loan, fraud, and rejection memory."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.rag_engine.retriever import KnowledgeRetriever


# ==========================================
# SECTION: Embeddings
# ==========================================
# Similarity search uses query embeddings through KnowledgeRetriever.


# ==========================================
# SECTION: Vector Search
# ==========================================
# Retrieval stays tenant-safe by requiring tenant_id in every public call.


# ==========================================
# SECTION: Retrieval Logic
# ==========================================
class CaseSimilarityService:
    """Find semantically similar historical cases for decision support."""

    def __init__(self) -> None:
        self.retriever = KnowledgeRetriever()

    def find_similar_loan_cases(
        self,
        query: str,
        *,
        tenant_id: int,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Find similar past loan/application cases."""
        return self.retriever.retrieve_relevant_context(
            query,
            tenant_id=tenant_id,
            top_k=top_k,
            namespaces=["historical_applications", "lender_rules", "call_transcripts"],
        )

    def find_similar_fraud_cases(
        self,
        query: str,
        *,
        tenant_id: int,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Find similar fraud cases and anomaly patterns."""
        return self.retriever.retrieve_relevant_context(
            query,
            tenant_id=tenant_id,
            top_k=top_k,
            namespaces=["fraud_cases", "compliance_notes"],
        )

    def find_similar_rejections(
        self,
        query: str,
        *,
        tenant_id: int,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Find similar rejection reasons and underwriting outcomes."""
        return self.retriever.retrieve_relevant_context(
            query,
            tenant_id=tenant_id,
            top_k=top_k,
            namespaces=["rejections", "lender_rules", "historical_applications"],
        )

    def find_similar_cases(
        self,
        query: str,
        *,
        tenant_id: int,
        case_type: str = "loan",
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Generic similarity entry point used by the API layer."""
        normalized_case_type = str(case_type or "loan").lower()
        if normalized_case_type == "fraud":
            return self.find_similar_fraud_cases(query, tenant_id=tenant_id, top_k=top_k)
        if normalized_case_type == "rejection":
            return self.find_similar_rejections(query, tenant_id=tenant_id, top_k=top_k)
        return self.find_similar_loan_cases(query, tenant_id=tenant_id, top_k=top_k)


# ==========================================
# SECTION: Context Builder
# ==========================================
# Similarity results are later converted into prompt context and UI cards.
