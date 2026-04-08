"""Dashboard KPI aggregation service using Pandas."""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

import pandas as pd

from app.models.application import Application
from app.models.lead import Lead


# ======================================
# SECTION: Core Service Logic
# ======================================
class DashboardKPIService:
    """Computes owner, branch, and agent KPI snapshots."""

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id

    def get_owner_kpis(self) -> dict:
        """Aggregate tenant-wide KPIs for owner dashboard."""
        lead_df = self._lead_dataframe()
        app_df = self._application_dataframe()

        total_leads = len(lead_df)
        total_apps = len(app_df)
        disbursed = int((lead_df["stage"] == "DISBURSED").sum()) if not lead_df.empty else 0
        lost = int((lead_df["stage"] == "LOST").sum()) if not lead_df.empty else 0
        pending_docs = int(lead_df["stage"].isin(["DOCS_PENDING", "DOCS_RECEIVED"]).sum()) if not lead_df.empty else 0

        conversion_rate = round((disbursed / total_leads) * 100, 2) if total_leads else 0.0
        commission_earned = round((lead_df.loc[lead_df["stage"] == "DISBURSED", "loan_amount"].fillna(0).sum()) * 0.005, 2) if not lead_df.empty else 0.0

        top_agents = self._top_agents(lead_df)
        branch_leaderboard = self._branch_leaderboard_placeholder(lead_df)

        return {
            "total_leads": int(total_leads),
            "applications": int(total_apps),
            "conversions": conversion_rate,
            "pending_docs": int(pending_docs),
            "commission_earned": commission_earned,
            "lost_leads": int(lost),
            "top_agents": top_agents,
            "branch_leaderboard": branch_leaderboard,
        }

    def get_branch_kpis(self, branch_name: str | None = None) -> dict:
        """Aggregate branch-level KPIs.

        Current models do not store explicit branch on leads/users,
        so this returns tenant-scoped proxy metrics with placeholder filter.
        """
        lead_df = self._lead_dataframe()
        if branch_name and not lead_df.empty and "assigned_agent" in lead_df.columns:
            branch_df = lead_df[lead_df["assigned_agent"].astype(str).str.contains(branch_name, case=False, na=False)]
        else:
            branch_df = lead_df

        total_leads = len(branch_df)
        disbursed = int((branch_df["stage"] == "DISBURSED").sum()) if not branch_df.empty else 0
        pending_docs = int(branch_df["stage"].isin(["DOCS_PENDING", "DOCS_RECEIVED"]).sum()) if not branch_df.empty else 0

        return {
            "total_leads": int(total_leads),
            "applications": int(total_leads),
            "conversions": round((disbursed / total_leads) * 100, 2) if total_leads else 0.0,
            "pending_docs": int(pending_docs),
            "commission_earned": round(branch_df["loan_amount"].fillna(0).sum() * 0.004, 2) if not branch_df.empty else 0.0,
            "lost_leads": int((branch_df["stage"] == "LOST").sum()) if not branch_df.empty else 0,
            "top_agents": self._top_agents(branch_df),
            "branch_leaderboard": self._branch_leaderboard_placeholder(branch_df),
        }

    def get_agent_kpis(self, agent_name: str) -> dict:
        """Aggregate agent-scoped KPIs by assigned_agent field."""
        lead_df = self._lead_dataframe()
        if lead_df.empty:
            filtered = lead_df
        else:
            filtered = lead_df[lead_df["assigned_agent"].fillna("") == agent_name]

        total_leads = len(filtered)
        disbursed = int((filtered["stage"] == "DISBURSED").sum()) if not filtered.empty else 0

        return {
            "total_leads": int(total_leads),
            "applications": int(total_leads),
            "conversions": round((disbursed / total_leads) * 100, 2) if total_leads else 0.0,
            "pending_docs": int(filtered["stage"].isin(["DOCS_PENDING", "DOCS_RECEIVED"]).sum()) if not filtered.empty else 0,
            "commission_earned": round(filtered["loan_amount"].fillna(0).sum() * 0.003, 2) if not filtered.empty else 0.0,
            "lost_leads": int((filtered["stage"] == "LOST").sum()) if not filtered.empty else 0,
            "top_agents": [{"agent": agent_name, "count": int(total_leads)}],
            "branch_leaderboard": self._branch_leaderboard_placeholder(filtered),
        }

    # ======================================
    # SECTION: Helper Functions
    # ======================================
    def _lead_dataframe(self) -> pd.DataFrame:
        """Load tenant leads into Pandas DataFrame."""
        leads = Lead.query.filter_by(tenant_id=self.tenant_id, is_deleted=False).all()
        rows = [
            {
                "id": lead.id,
                "stage": lead.stage,
                "loan_amount": float(lead.loan_amount) if lead.loan_amount is not None else 0.0,
                "assigned_agent": lead.assigned_agent,
                "source": lead.source,
            }
            for lead in leads
        ]
        return pd.DataFrame(rows)

    def _application_dataframe(self) -> pd.DataFrame:
        """Load tenant applications into DataFrame."""
        applications = Application.query.filter_by(tenant_id=self.tenant_id, is_deleted=False).all()
        rows = [
            {
                "id": app.id,
                "stage": app.current_stage,
                "loan_amount": float(app.loan_amount) if app.loan_amount is not None else 0.0,
            }
            for app in applications
        ]
        return pd.DataFrame(rows)

    def _top_agents(self, lead_df: pd.DataFrame) -> list[dict]:
        """Return top 5 agents by assigned lead count."""
        if lead_df.empty or "assigned_agent" not in lead_df.columns:
            return []

        grouped = (
            lead_df[lead_df["assigned_agent"].notna()]
            .groupby("assigned_agent")
            .size()
            .sort_values(ascending=False)
            .head(5)
        )
        return [{"agent": str(agent), "count": int(count)} for agent, count in grouped.items()]

    def _branch_leaderboard_placeholder(self, lead_df: pd.DataFrame) -> list[dict]:
        """Return placeholder branch leaderboard derived from source mix."""
        if lead_df.empty:
            return []

        grouped = lead_df.groupby("source").size().sort_values(ascending=False).head(5)
        return [{"branch": str(source), "count": int(count)} for source, count in grouped.items()]


# ======================================
# SECTION: Calculators
# ======================================
# N/A for this service. KPI computations are part of the core logic
# methods for owner/branch/agent snapshots.
