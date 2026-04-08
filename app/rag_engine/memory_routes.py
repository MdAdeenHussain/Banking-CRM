"""RAG memory APIs for semantic search and context retrieval."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.rag_engine.case_similarity_service import CaseSimilarityService
from app.rag_engine.prompt_context_builder import PromptContextBuilder
from app.rag_engine.retriever import KnowledgeRetriever


rag_memory_bp = Blueprint("rag_memory", __name__)


# ==========================================
# SECTION: Embeddings
# ==========================================
# Routes use service classes so vector generation stays out of controllers.


# ==========================================
# SECTION: Vector Search
# ==========================================
@rag_memory_bp.post("/api/v1/rag/search")
@login_required
def rag_search_api():
    """Run semantic search across tenant vector memory."""
    payload = request.get_json(silent=True) or {}
    retriever = KnowledgeRetriever()
    query = str(payload.get("query", "")).strip()
    namespaces = payload.get("namespaces")
    top_k = int(payload.get("top_k", 5) or 5)
    results = retriever.retrieve_relevant_context(
        query,
        tenant_id=current_user.tenant_id,
        top_k=top_k,
        namespaces=namespaces,
    )
    return jsonify({"success": True, "data": results}), 200


@rag_memory_bp.post("/api/v1/rag/similar-cases")
@login_required
def similar_cases_api():
    """Return semantically similar historical cases."""
    payload = request.get_json(silent=True) or {}
    service = CaseSimilarityService()
    query = str(payload.get("query", "")).strip()
    case_type = str(payload.get("case_type", "loan")).strip()
    top_k = int(payload.get("top_k", 5) or 5)
    results = service.find_similar_cases(
        query,
        tenant_id=current_user.tenant_id,
        case_type=case_type,
        top_k=top_k,
    )
    return jsonify({"success": True, "data": results}), 200


@rag_memory_bp.post("/api/v1/rag/context")
@login_required
def rag_context_api():
    """Return prompt-ready memory context for a user query."""
    payload = request.get_json(silent=True) or {}
    builder = PromptContextBuilder()
    query = str(payload.get("query", "")).strip()
    namespaces = payload.get("namespaces")
    top_k = int(payload.get("top_k", 5) or 5)
    result = builder.build_context(
        query,
        tenant_id=current_user.tenant_id,
        top_k=top_k,
        namespaces=namespaces,
    )
    return jsonify({"success": True, "data": result}), 200


# ==========================================
# SECTION: Retrieval Logic
# ==========================================
# Controllers return JSON only; formatting for prompts happens in services.


# ==========================================
# SECTION: Context Builder
# ==========================================
# Context responses are designed for direct reuse by the assistant layer.
