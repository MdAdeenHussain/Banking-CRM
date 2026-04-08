"""Dashboard KPI aggregation service using Pandas."""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

import pandas as pd

from app.models.application import Application
from app.models.document import Document
from app.models.lead import Lead
from app.models.lender import Lender


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
        doc_df = self._document_dataframe()

        total_leads = len(lead_df)
        total_apps = len(app_df)
        disbursed = int((lead_df["stage"] == "DISBURSED").sum()) if not lead_df.empty else 0
        lost = int((lead_df["stage"] == "LOST").sum()) if not lead_df.empty else 0
        pending_docs = int(lead_df["stage"].isin(["DOCS_PENDING", "DOCS_RECEIVED"]).sum()) if not lead_df.empty else 0
        documents_uploaded = int(len(doc_df))
        documents_pending = int((doc_df["ocr_status"] == "PENDING").sum()) if not doc_df.empty else 0
        fraud_alerts = int((doc_df["fraud_score"] >= 40).sum()) if not doc_df.empty else 0
        verification_queue_count = int((doc_df["verification_status"].isin(["PENDING", "UNDER_REVIEW"])).sum()) if not doc_df.empty else 0
        ai_lead_score_distribution = self._ai_lead_score_distribution(lead_df)
        approval_probability = self._approval_probability_proxy(app_df)
        top_lender_matches = self._top_lender_matches()
        risk_segmentation = self._risk_segmentation(doc_df)

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
            "documents_uploaded": documents_uploaded,
            "documents_pending": documents_pending,
            "fraud_alerts": fraud_alerts,
            "verification_queue_count": verification_queue_count,
            "ai_lead_score_distribution": ai_lead_score_distribution,
            "approval_probability": approval_probability,
            "top_lender_matches": top_lender_matches,
            "risk_segmentation": risk_segmentation,
        }

    def get_branch_kpis(self, branch_name: str | None = None) -> dict:
        """Aggregate branch-level KPIs.

        Current models do not store explicit branch on leads/users,
        so this returns tenant-scoped proxy metrics with placeholder filter.
        """
        lead_df = self._lead_dataframe()
        doc_df = self._document_dataframe()
        if branch_name and not lead_df.empty and "assigned_agent" in lead_df.columns:
            branch_df = lead_df[lead_df["assigned_agent"].astype(str).str.contains(branch_name, case=False, na=False)]
        else:
            branch_df = lead_df

        total_leads = len(branch_df)
        disbursed = int((branch_df["stage"] == "DISBURSED").sum()) if not branch_df.empty else 0
        pending_docs = int(branch_df["stage"].isin(["DOCS_PENDING", "DOCS_RECEIVED"]).sum()) if not branch_df.empty else 0
        ai_lead_score_distribution = self._ai_lead_score_distribution(branch_df)
        approval_probability = self._approval_probability_proxy(self._application_dataframe())
        top_lender_matches = self._top_lender_matches()
        risk_segmentation = self._risk_segmentation(doc_df)

        return {
            "total_leads": int(total_leads),
            "applications": int(total_leads),
            "conversions": round((disbursed / total_leads) * 100, 2) if total_leads else 0.0,
            "pending_docs": int(pending_docs),
            "commission_earned": round(branch_df["loan_amount"].fillna(0).sum() * 0.004, 2) if not branch_df.empty else 0.0,
            "lost_leads": int((branch_df["stage"] == "LOST").sum()) if not branch_df.empty else 0,
            "top_agents": self._top_agents(branch_df),
            "branch_leaderboard": self._branch_leaderboard_placeholder(branch_df),
            "documents_uploaded": int(len(doc_df)),
            "documents_pending": int((doc_df["ocr_status"] == "PENDING").sum()) if not doc_df.empty else 0,
            "fraud_alerts": int((doc_df["fraud_score"] >= 40).sum()) if not doc_df.empty else 0,
            "verification_queue_count": int((doc_df["verification_status"].isin(["PENDING", "UNDER_REVIEW"])).sum()) if not doc_df.empty else 0,
            "ai_lead_score_distribution": ai_lead_score_distribution,
            "approval_probability": approval_probability,
            "top_lender_matches": top_lender_matches,
            "risk_segmentation": risk_segmentation,
        }

    def get_agent_kpis(self, agent_name: str) -> dict:
        """Aggregate agent-scoped KPIs by assigned_agent field."""
        lead_df = self._lead_dataframe()
        doc_df = self._document_dataframe()
        if lead_df.empty:
            filtered = lead_df
        else:
            filtered = lead_df[lead_df["assigned_agent"].fillna("") == agent_name]

        total_leads = len(filtered)
        disbursed = int((filtered["stage"] == "DISBURSED").sum()) if not filtered.empty else 0
        ai_lead_score_distribution = self._ai_lead_score_distribution(filtered)
        approval_probability = self._approval_probability_proxy(self._application_dataframe())
        top_lender_matches = self._top_lender_matches()
        risk_segmentation = self._risk_segmentation(doc_df)

        return {
            "total_leads": int(total_leads),
            "applications": int(total_leads),
            "conversions": round((disbursed / total_leads) * 100, 2) if total_leads else 0.0,
            "pending_docs": int(filtered["stage"].isin(["DOCS_PENDING", "DOCS_RECEIVED"]).sum()) if not filtered.empty else 0,
            "commission_earned": round(filtered["loan_amount"].fillna(0).sum() * 0.003, 2) if not filtered.empty else 0.0,
            "lost_leads": int((filtered["stage"] == "LOST").sum()) if not filtered.empty else 0,
            "top_agents": [{"agent": agent_name, "count": int(total_leads)}],
            "branch_leaderboard": self._branch_leaderboard_placeholder(filtered),
            "documents_uploaded": int(len(doc_df)),
            "documents_pending": int((doc_df["ocr_status"] == "PENDING").sum()) if not doc_df.empty else 0,
            "fraud_alerts": int((doc_df["fraud_score"] >= 40).sum()) if not doc_df.empty else 0,
            "verification_queue_count": int((doc_df["verification_status"].isin(["PENDING", "UNDER_REVIEW"])).sum()) if not doc_df.empty else 0,
            "ai_lead_score_distribution": ai_lead_score_distribution,
            "approval_probability": approval_probability,
            "top_lender_matches": top_lender_matches,
            "risk_segmentation": risk_segmentation,
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
                "ai_score": float(lead.ai_score_placeholder) if lead.ai_score_placeholder is not None else None,
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

    def _document_dataframe(self) -> pd.DataFrame:
        """Load tenant documents into DataFrame."""
        documents = Document.query.filter_by(tenant_id=self.tenant_id, is_deleted=False).all()
        rows = [
            {
                "id": doc.id,
                "ocr_status": doc.ocr_status,
                "fraud_score": int(doc.fraud_score or 0),
                "verification_status": doc.verification_status,
            }
            for doc in documents
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

    def _ai_lead_score_distribution(self, lead_df: pd.DataFrame) -> dict:
        """Compute low/medium/high buckets for AI lead scores."""
        if lead_df.empty or "ai_score" not in lead_df.columns:
            return {"low": 0, "medium": 0, "high": 0}

        scores = pd.to_numeric(lead_df["ai_score"], errors="coerce").fillna(0)
        return {
            "low": int((scores < 40).sum()),
            "medium": int(((scores >= 40) & (scores < 70)).sum()),
            "high": int((scores >= 70).sum()),
        }

    def _approval_probability_proxy(self, app_df: pd.DataFrame) -> float:
        """Compute approval-probability proxy from application stage mix."""
        if app_df.empty:
            return 0.0

        approved = int(app_df["stage"].isin(["SANCTIONED", "DISBURSED"]).sum())
        total = len(app_df)
        return round((approved / total) * 100, 2) if total else 0.0

    def _top_lender_matches(self) -> list[dict]:
        """Return top lender matches by approval and rate competitiveness."""
        lenders = Lender.query.filter_by(tenant_id=self.tenant_id, is_deleted=False).all()
        if not lenders:
            return []

        rows = []
        for lender in lenders:
            approval = float(lender.approval_percentage or 0)
            rate = float(lender.interest_rate or 15)
            score = (0.7 * approval) + (0.3 * max(0, 100 - (rate * 6)))
            rows.append({"bank": lender.lender_name, "score": round(score, 2)})

        return sorted(rows, key=lambda x: x["score"], reverse=True)[:3]

    def _risk_segmentation(self, doc_df: pd.DataFrame) -> dict:
        """Compute risk segmentation buckets from document fraud scores."""
        if doc_df.empty:
            return {"low": 0, "medium": 0, "high": 0}

        scores = pd.to_numeric(doc_df["fraud_score"], errors="coerce").fillna(0)
        return {
            "low": int((scores < 40).sum()),
            "medium": int(((scores >= 40) & (scores <= 70)).sum()),
            "high": int((scores > 70).sum()),
        }


# ======================================
# SECTION: Calculators
# ======================================
# N/A for this service. KPI computations are part of the core logic
# methods for owner/branch/agent snapshots.
