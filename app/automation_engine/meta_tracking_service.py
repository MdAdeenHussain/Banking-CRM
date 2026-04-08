"""Meta Pixel and webhook support service."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import json
from typing import Any

from flask import current_app

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.tenant import Tenant


# ==========================================
# SECTION: Workflow Rules
# ==========================================
# Meta events and webhook payloads are normalized here.


# ==========================================
# SECTION: Communication
# ==========================================
# Pixel snippets are returned as JS/HTML placeholders for templates.


# ==========================================
# SECTION: Scheduling
# ==========================================
# Not applicable for pixel tracking service.


# ==========================================
# SECTION: Tracking
# ==========================================
class MetaTrackingService:
    """Handle Meta pixel snippet generation and event tracking."""

    DEFAULT_PIXEL_ID = "META_PIXEL_PLACEHOLDER"

    def __init__(self, tenant_id: int | None = None, actor_user_id: int | None = None) -> None:
        self.tenant_id = tenant_id
        self.actor_user_id = actor_user_id

    def inject_pixel_base(self, pixel_id: str | None = None) -> str:
        """Return placeholder Meta Pixel base snippet."""
        pixel = pixel_id or self.DEFAULT_PIXEL_ID
        return (
            "<script>\n"
            "  // Meta Pixel placeholder snippet\n"
            f"  window.fbq = window.fbq || function(){{console.log('Meta Pixel', arguments);}};\n"
            f"  fbq('init', '{pixel}');\n"
            "  fbq('track', 'PageView');\n"
            "</script>"
        )

    def track_page_view(self, page_name: str, *, tenant_id: int | None = None) -> dict[str, Any]:
        """Track Meta PageView event."""
        return self._track_event("PageView", {"page_name": page_name}, tenant_id=tenant_id)

    def track_lead_created(self, lead_id: int, *, campaign_id: str | None = None, tenant_id: int | None = None) -> dict[str, Any]:
        """Track Meta Lead event."""
        return self._track_event("Lead", {"lead_id": lead_id, "campaign_id": campaign_id}, tenant_id=tenant_id)

    def track_application_submit(
        self,
        application_id: int,
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Track Meta SubmitApplication event."""
        return self._track_event("SubmitApplication", {"application_id": application_id}, tenant_id=tenant_id)

    def track_conversion(self, lead_id: int, *, tenant_id: int | None = None) -> dict[str, Any]:
        """Track Meta PurchaseEquivalent conversion event."""
        return self._track_event("PurchaseEquivalent", {"lead_id": lead_id}, tenant_id=tenant_id)

    def verify_token(self, supplied_token: str) -> bool:
        """Verify webhook token against config placeholder."""
        expected_token = current_app.config.get("META_WEBHOOK_TOKEN", "")
        return not expected_token or expected_token == supplied_token

    def receive_meta_lead(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normalize Meta lead webhook payload into internal structure."""
        lead_data = payload.get("lead") or payload.get("lead_data") or payload
        normalized = {
            "tenant": self.resolve_tenant(payload),
            "customer_name": lead_data.get("full_name") or lead_data.get("name") or "Meta Lead",
            "mobile": lead_data.get("phone") or lead_data.get("mobile") or "",
            "email": lead_data.get("email"),
            "loan_type": lead_data.get("loan_type") or "unknown",
            "loan_amount": lead_data.get("loan_amount"),
            "branch_id": lead_data.get("branch_id"),
            "pan": lead_data.get("pan"),
            "campaign_id": lead_data.get("campaign_id") or payload.get("campaign_id"),
            "adset_id": lead_data.get("adset_id") or payload.get("adset_id"),
            "ad_id": lead_data.get("ad_id") or payload.get("ad_id"),
            "utm_source": lead_data.get("utm_source") or payload.get("utm_source") or "meta",
            "utm_campaign": lead_data.get("utm_campaign") or payload.get("utm_campaign"),
            "source": "meta_ads",
        }
        return normalized

    def resolve_tenant(self, payload: dict[str, Any]) -> Tenant | None:
        """Resolve tenant from payload using id or slug."""
        tenant_id = payload.get("tenant_id")
        tenant_slug = payload.get("tenant_slug")
        if tenant_id:
            return Tenant.query.filter_by(id=tenant_id, is_deleted=False, is_active=True).first()
        if tenant_slug:
            return Tenant.query.filter_by(slug=tenant_slug, is_deleted=False, is_active=True).first()
        return None

    def _track_event(
        self,
        event_name: str,
        payload: dict[str, Any],
        *,
        tenant_id: int | None = None,
    ) -> dict[str, Any]:
        """Persist Meta tracking event to audit logs."""
        active_tenant_id = tenant_id or self.tenant_id
        event_payload = {"event_name": event_name, **payload}
        if active_tenant_id:
            log = AuditLog(
                tenant_id=active_tenant_id,
                user_id=self.actor_user_id,
                action="meta_event_tracked",
                entity="meta",
                entity_id=event_name,
                details=json.dumps(event_payload, ensure_ascii=True),
            )
            db.session.add(log)
            db.session.commit()
        return event_payload
