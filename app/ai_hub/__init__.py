"""AI hub package exports for Phase 7 LLM architecture."""

# ==========================================
# SECTION: Imports
# ==========================================
from app.ai_hub.routes import ai_hub_bp


# ==========================================
# SECTION: Provider Routing
# ==========================================
# The provider router lives in app.ai_hub.router and is used by the
# service layer rather than imported here to keep package imports light.


# ==========================================
# SECTION: Prompt Templates
# ==========================================
# Shared prompt templates are stored in app.ai_hub.prompt_manager.


# ==========================================
# SECTION: Assistant Logic
# ==========================================
# Assistant orchestration is handled by app.ai_hub.assistant_service.

__all__ = ["ai_hub_bp"]
