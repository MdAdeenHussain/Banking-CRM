"""Campaign attribution and ROI service."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import json
from typing import Any

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.lead import Lead


# ==========================================
# SECTION: Workflow Rules
# ==========================================
# Attribution is recorded on lead events without adding new schema.


# ==========================================
# SECTION: Communication
# ==========================================
# Attribution data can be reused by communication and reporting services.


# ==========================================
# SECTION: Scheduling
# ==========================================
# Not applicable for attribution service.


# ==========================================
# SECTION: Tracking
# ==========================================
class CampaignAttributionService:
    """Track lead-to-campaign mapping and calculate ROI metrics."""

    def __init__(self, tenant_id: int, actor_user_id: int | None = None) -> None:
        self.tenant_id = tenant_id
        self.actor_user_id = actor_user_id

    def map_lead_to_campaign(
        self,
        *,
        lead_id: int,
        source: str | None = None,
        medium: str | None = None,
        campaign: str | None = None,
        adset: str | None = None,
        creative: str | None = None,
        campaign_id: str | None = None,
        adset_id: str | None = None,
        ad_id: str | None = None,
        utm_source: str | None = None,
        utm_campaign: str | None = None,
    ) -> dict[str, Any]:
        """Persist campaign attribution metadata for a lead."""
        payload = {
            "lead_id": lead_id,
            "source": source or utm_source or "unknown",
            "medium": medium or "paid",
            "campaign": campaign or utm_campaign or "unknown_campaign",
            "adset": adset or adset_id,
            "creative": creative or ad_id,
            "campaign_id": campaign_id,
            "adset_id": adset_id,
            "ad_id": ad_id,
            "utm_source": utm_source,
            "utm_campaign": utm_campaign,
        }
        log = AuditLog(
            tenant_id=self.tenant_id,
            user_id=self.actor_user_id,
            action="campaign_attribution_recorded",
            entity="lead",
            entity_id=str(lead_id),
            details=json.dumps(payload, ensure_ascii=True),
        )
        db.session.add(log)
        db.session.commit()
        return payload

    def get_lead_attribution(self, lead_id: int) -> dict[str, Any] | None:
        """Return latest attribution record for a lead."""
        log = (
            AuditLog.query.filter_by(
                tenant_id=self.tenant_id,
                action="campaign_attribution_recorded",
                entity="lead",
                entity_id=str(lead_id),
                is_deleted=False,
            )
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        if log is None:
            return None
        try:
            return json.loads(log.details or "{}")
        except json.JSONDecodeError:
            return None

    def calculate_campaign_roi(self) -> dict[str, Any]:
        """Calculate simple ROI metrics from campaign-attributed leads."""
        attributed_logs = AuditLog.query.filter_by(
            tenant_id=self.tenant_id,
            action="campaign_attribution_recorded",
            is_deleted=False,
        ).all()

        campaign_rows: dict[str, dict[str, Any]] = {}
        for log in attributed_logs:
            try:
                payload = json.loads(log.details or "{}")
            except json.JSONDecodeError:
                payload = {}
            campaign_name = payload.get("campaign") or payload.get("utm_campaign") or "unknown_campaign"
            row = campaign_rows.setdefault(
                campaign_name,
                {
                    "campaign": campaign_name,
                    "lead_count": 0,
                    "disbursed_count": 0,
                    "revenue": 0.0,
                    "estimated_spend": 0.0,
                },
            )
            row["lead_count"] += 1
            lead = Lead.query.filter_by(
                id=payload.get("lead_id"),
                tenant_id=self.tenant_id,
                is_deleted=False,
            ).first()
            if lead and lead.stage == "DISBURSED":
                row["disbursed_count"] += 1
                row["revenue"] += float(lead.loan_amount or 0) * 0.005
            row["estimated_spend"] += 250.0

        campaigns = []
        total_revenue = 0.0
        total_spend = 0.0
        for row in campaign_rows.values():
            revenue = float(row["revenue"])
            spend = float(row["estimated_spend"])
            roi = round(((revenue - spend) / spend) * 100, 2) if spend else 0.0
            conversion_rate = round((row["disbursed_count"] / row["lead_count"]) * 100, 2) if row["lead_count"] else 0.0
            campaigns.append(
                {
                    **row,
                    "roi_percent": roi,
                    "conversion_rate": conversion_rate,
                }
            )
            total_revenue += revenue
            total_spend += spend

        campaigns.sort(key=lambda item: item["roi_percent"], reverse=True)
        overall_roi = round(((total_revenue - total_spend) / total_spend) * 100, 2) if total_spend else 0.0
        return {
            "overall_roi": overall_roi,
            "campaigns": campaigns[:5],
        }

    def meta_conversion_funnel(self) -> dict[str, int]:
        """Return Meta event funnel counts from tracked event logs."""
        logs = AuditLog.query.filter_by(
            tenant_id=self.tenant_id,
            action="meta_event_tracked",
            is_deleted=False,
        ).all()
        counts = {
            "PageView": 0,
            "Lead": 0,
            "CompleteRegistration": 0,
            "SubmitApplication": 0,
            "PurchaseEquivalent": 0,
        }
        for log in logs:
            try:
                payload = json.loads(log.details or "{}")
            except json.JSONDecodeError:
                payload = {}
            event_name = payload.get("event_name")
            if event_name in counts:
                counts[event_name] += 1
        return counts
