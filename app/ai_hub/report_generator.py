"""Narrative report generation service for management dashboards."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from typing import Any

from app.ai_hub.assistant_service import AssistantService


# ==========================================
# SECTION: Provider Routing
# ==========================================
# Non-sensitive branch/owner narratives may use cloud fallback when
# allowed, while PII-heavy summaries stay local.


# ==========================================
# SECTION: Prompt Templates
# ==========================================
# Branch report prompt rendering is delegated to PromptManager.


# ==========================================
# SECTION: Assistant Logic
# ==========================================
class ReportGenerator:
    """Generates narrative reports for branch managers and owners."""

    def __init__(self) -> None:
        self.assistant = AssistantService()

    def generate_branch_report(
        self,
        report_data: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate branch manager narrative report."""
        return self._generate(report_data, tenant_id=tenant_id)

    def generate_owner_report(
        self,
        report_data: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate owner dashboard narrative report."""
        return self._generate(report_data, tenant_id=tenant_id)

    def generate_daily_performance_summary(
        self,
        report_data: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate concise daily performance summary."""
        return self._generate(report_data, tenant_id=tenant_id)

    def generate_weekly_business_summary(
        self,
        report_data: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate weekly business summary narrative."""
        return self._generate(report_data, tenant_id=tenant_id)

    def _generate(
        self,
        report_data: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Internal narrative generator shared across report types."""
        result = self.assistant.generate_text(
            task_type="branch_report",
            prompt_key="branch_report",
            prompt_values={
                "branch_name": report_data.get("branch_name", "Main Branch"),
                "conversion_change": report_data.get("conversion_change", "0%"),
                "lead_volume": report_data.get("lead_volume", 0),
                "sanction_count": report_data.get("sanction_count", 0),
                "fraud_alerts": report_data.get("fraud_alerts", 0),
                "focus_area": report_data.get("focus_area", "improve follow-up quality"),
            },
            sensitive=False,
            tenant_id=tenant_id,
            memory_query=(
                f"Branch report for {report_data.get('branch_name', 'branch')} with lead volume "
                f"{report_data.get('lead_volume', 0)} and fraud alerts {report_data.get('fraud_alerts', 0)}"
            ),
            memory_namespaces=["branch_reports", "historical_applications", "fraud_cases", "rejections"],
        )
        return {
            "report": result["content"],
            "provider": result["provider"],
            "model": result["model"],
            "generated_by": "llm_assistant",
            "memory_context": result["memory_context"],
            "retrieved_items": result["retrieved_items"],
        }
