"""Billing service layer."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.billing import Billing


# =====================================
# SECTION: Service Definition
# =====================================
class BillingService:
    """Tenant billing and plan operations."""

    @staticmethod
    def get_current_plan(tenant_id: int) -> Billing | None:
        """Fetch active billing record for tenant."""
        return Billing.query.filter_by(tenant_id=tenant_id, is_deleted=False).first()

    @staticmethod
    def upsert_plan(tenant_id: int, payload: dict) -> Billing:
        """Create or update tenant billing info."""
        billing = Billing.query.filter_by(tenant_id=tenant_id, is_deleted=False).first()

        if not billing:
            billing = Billing(
                tenant_id=tenant_id,
                plan_name=payload.get("plan_name", "starter"),
                monthly_amount=payload.get("monthly_amount", 0),
                status=payload.get("status", "active"),
                renewal_date=payload.get("renewal_date"),
            )
            db.session.add(billing)
        else:
            billing.plan_name = payload.get("plan_name", billing.plan_name)
            billing.monthly_amount = payload.get("monthly_amount", billing.monthly_amount)
            billing.status = payload.get("status", billing.status)
            billing.renewal_date = payload.get("renewal_date", billing.renewal_date)

        db.session.commit()
        return billing

    # Future AI placeholder:
    # - usage forecast to billing advisor bridge
