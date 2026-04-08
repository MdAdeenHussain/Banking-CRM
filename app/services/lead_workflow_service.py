"""Lead workflow engine.

Phase 4 adds business workflow logic for lead lifecycle management
while keeping AI/ML logic out of scope.
"""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from flask import current_app
from flask_login import current_user

from app.extensions import db, redis_client
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.lead import Lead
from app.models.user import User


# ======================================
# SECTION: Core Service Logic
# ======================================
# In-memory fallback counter when Redis is unavailable.
_ROUND_ROBIN_COUNTER: dict[str, int] = defaultdict(int)


class LeadWorkflowService:
    """Business workflow engine for lead lifecycle operations.

    The service is tenant-scoped to prevent cross-tenant data access.
    """

    # Lifecycle requested in Phase 4.
    ALLOWED_WORKFLOW_STAGES = {
        "NEW_LEAD",
        "CONTACTED",
        "INTERESTED",
        "DOCS_PENDING",
        "DOCS_RECEIVED",
        "ELIGIBILITY_CHECKED",
        "BANK_MATCHED",
        "APPLICATION_FILED",
        "UNDER_REVIEW",
        "SANCTIONED",
        "DISBURSED",
        "LOST",
    }

    def __init__(self, tenant_id: int, actor_user_id: int | None = None) -> None:
        """Initialize service with tenant scope and optional actor context."""
        self.tenant_id = tenant_id
        self.actor_user_id = actor_user_id

    def create_lead(self, data: dict[str, Any]) -> Lead:
        """Create lead record with duplicate checks and default stage.

        Steps:
        1) Validate duplicates by mobile/PAN (PAN checks customer records).
        2) Assign explicit or default source.
        3) Set workflow default stage.
        4) Optionally auto-assign an agent.
        5) Write audit timeline.
        """
        mobile = str(data.get("mobile", "")).strip()
        pan = str(data.get("pan", "")).strip() or None

        is_duplicate = self.duplicate_check(mobile=mobile, pan=pan)
        if is_duplicate:
            raise ValueError("Potential duplicate lead detected for this tenant.")

        source = data.get("source") or "manual"
        default_stage = data.get("stage") or "NEW_LEAD"
        if default_stage not in self.ALLOWED_WORKFLOW_STAGES:
            default_stage = "NEW_LEAD"

        lead = Lead(
            tenant_id=self.tenant_id,
            customer_name=data.get("customer_name", "Unknown Lead"),
            mobile=mobile,
            email=data.get("email"),
            loan_type=data.get("loan_type"),
            loan_amount=data.get("loan_amount"),
            source=source,
            stage=default_stage,
            assigned_agent=data.get("assigned_agent"),
            ai_score_placeholder=data.get("ai_score_placeholder"),
        )

        db.session.add(lead)
        db.session.flush()

        # Optional auto assignment: branch_id can be provided by webhook/source flow.
        if not lead.assigned_agent and data.get("auto_assign"):
            agent = self.round_robin_assign(branch_id=data.get("branch_id"))
            if agent:
                lead.assigned_agent = agent.name

        self._log_timeline(
            entity="lead",
            entity_id=lead.id,
            action="lead_created",
            details=f"Lead created with stage={lead.stage}, source={source}",
        )

        db.session.commit()

        # Update dashboard metrics cache placeholder.
        self._update_dashboard_counters()
        return lead

    def update_stage(self, lead_id: int, new_stage: str) -> Lead:
        """Move lead stage, record timeline, and refresh dashboard counters."""
        if new_stage not in self.ALLOWED_WORKFLOW_STAGES:
            raise ValueError(f"Invalid lead stage: {new_stage}")

        lead = self._get_lead_or_fail(lead_id)
        old_stage = lead.stage
        lead.stage = new_stage
        lead.updated_at = datetime.now(timezone.utc)

        self._log_timeline(
            entity="lead",
            entity_id=lead.id,
            action="lead_stage_updated",
            details=f"Stage changed {old_stage} -> {new_stage}",
        )

        db.session.commit()
        self._update_dashboard_counters()
        return lead

    def assign_agent(self, lead_id: int, agent_id: int) -> Lead:
        """Assign lead to an agent in the same tenant."""
        lead = self._get_lead_or_fail(lead_id)

        agent = User.query.filter_by(
            id=agent_id,
            tenant_id=self.tenant_id,
            is_deleted=False,
            is_active=True,
        ).first()
        if not agent:
            raise ValueError("Agent not found for current tenant.")

        lead.assigned_agent = agent.name
        self._log_timeline(
            entity="lead",
            entity_id=lead.id,
            action="lead_assigned",
            details=f"Assigned to agent_id={agent.id}, name={agent.name}",
        )

        db.session.commit()
        self._update_dashboard_counters()
        return lead

    def add_note(self, lead_id: int, note: str) -> None:
        """Add interaction note by writing into audit timeline."""
        lead = self._get_lead_or_fail(lead_id)
        self._log_timeline(
            entity="lead",
            entity_id=lead.id,
            action="lead_note_added",
            details=note,
        )
        db.session.commit()

    def duplicate_check(self, mobile: str, pan: str | None) -> bool:
        """Duplicate detection using mobile and optional PAN.

        - Mobile duplicates are checked in lead records for same tenant.
        - PAN duplicates are checked in customer records for same tenant.
        """
        mobile = (mobile or "").strip()
        if not mobile:
            return False

        lead_exists = Lead.query.filter_by(
            tenant_id=self.tenant_id,
            mobile=mobile,
            is_deleted=False,
        ).first()

        if lead_exists:
            return True

        if pan:
            customer_exists = Customer.query.filter_by(
                tenant_id=self.tenant_id,
                pan=pan,
                is_deleted=False,
            ).first()
            if customer_exists:
                return True

        return False

    def round_robin_assign(self, branch_id: int | None) -> User | None:
        """Round-robin agent assignment with branch fallback.

        Current model does not store `branch_id` on users, so branch logic
        is implemented as placeholder while preserving function contract.

        Logic:
        1) Rotate through active tenant agents.
        2) Use Redis counter when available.
        3) Fallback to branch manager role if no agent exists.
        """
        agents = (
            User.query.filter_by(
                tenant_id=self.tenant_id,
                role="agent",
                is_deleted=False,
                is_active=True,
            )
            .order_by(User.id.asc())
            .all()
        )

        if agents:
            key = f"lead_rr:{self.tenant_id}:{branch_id or 'default'}"
            index = self._next_round_robin_index(key, len(agents))
            return agents[index]

        # Fallback to branch manager per requirement.
        manager = (
            User.query.filter_by(
                tenant_id=self.tenant_id,
                role="branch",
                is_deleted=False,
                is_active=True,
            )
            .order_by(User.id.asc())
            .first()
        )
        return manager

    # ======================================
    # SECTION: Helper Functions
    # ======================================
    def _get_lead_or_fail(self, lead_id: int) -> Lead:
        """Fetch tenant-scoped lead or raise error."""
        lead = Lead.query.filter_by(
            id=lead_id,
            tenant_id=self.tenant_id,
            is_deleted=False,
        ).first()
        if not lead:
            raise ValueError("Lead not found for current tenant.")
        return lead

    def _log_timeline(self, *, entity: str, entity_id: int, action: str, details: str) -> None:
        """Write timeline events into audit log."""
        log = AuditLog(
            tenant_id=self.tenant_id,
            user_id=self.actor_user_id,
            action=action,
            entity=entity,
            entity_id=str(entity_id),
            details=details,
        )
        db.session.add(log)

    def _next_round_robin_index(self, key: str, size: int) -> int:
        """Get next index from Redis or in-memory fallback."""
        if size <= 0:
            return 0

        if redis_client is not None:
            try:
                counter = redis_client.incr(key)
                return int(counter - 1) % size
            except Exception:  # pragma: no cover - safe fallback path
                pass

        _ROUND_ROBIN_COUNTER[key] += 1
        return (_ROUND_ROBIN_COUNTER[key] - 1) % size

    def _update_dashboard_counters(self) -> None:
        """Placeholder to refresh KPI cache after workflow mutations."""
        try:
            if redis_client is not None:
                redis_client.setex(
                    f"kpi_refresh_hint:{self.tenant_id}",
                    120,
                    datetime.now(timezone.utc).isoformat(),
                )
        except Exception:
            # Keep workflow resilient even if cache infrastructure is down.
            current_app.logger.debug("KPI cache hint update skipped.")


# ======================================
# SECTION: Helper Functions
# ======================================
def round_robin_assign(branch_id: int | None) -> User | None:
    """Module-level round-robin helper using logged-in tenant context.

    This keeps the externally requested function signature simple while
    enforcing tenant-safe assignment under the current user session.
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    actor_user_id = getattr(current_user, "id", None)
    if not tenant_id:
        raise ValueError("Tenant context is required for round-robin assignment.")

    service = LeadWorkflowService(tenant_id=tenant_id, actor_user_id=actor_user_id)
    return service.round_robin_assign(branch_id=branch_id)


# ======================================
# SECTION: Calculators
# ======================================
# N/A for this workflow module.
