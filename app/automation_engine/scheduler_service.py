"""Callback and reminder scheduling service."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.extensions import db
from app.models.audit_log import AuditLog


# ==========================================
# SECTION: Workflow Rules
# ==========================================
# Scheduler events are stored in AuditLog to avoid schema churn.


# ==========================================
# SECTION: Communication
# ==========================================
# Communication tasks consume due callbacks from this service.


# ==========================================
# SECTION: Scheduling
# ==========================================
class SchedulerService:
    """Manage callback scheduling, rescheduling, and completion."""

    def __init__(self, tenant_id: int, actor_user_id: int | None = None) -> None:
        self.tenant_id = tenant_id
        self.actor_user_id = actor_user_id

    def schedule_callback(
        self,
        *,
        lead_id: int | None = None,
        customer_name: str | None = None,
        date: str,
        time: str,
        assigned_agent: str | None,
        priority: str = "medium",
    ) -> dict[str, Any]:
        """Schedule a callback and store metadata in audit logs."""
        callback_id = f"callback-{uuid.uuid4().hex}"
        due_at = self._build_due_at(date, time)
        payload = {
            "callback_id": callback_id,
            "lead_id": lead_id,
            "customer_name": customer_name,
            "date": date,
            "time": time,
            "due_at": due_at.isoformat(),
            "assigned_agent": assigned_agent,
            "priority": priority,
            "status": "scheduled",
        }
        self._write_callback_log(
            action="callback_scheduled",
            callback_id=callback_id,
            payload=payload,
        )
        db.session.commit()
        return payload

    def reschedule_callback(
        self,
        callback_id: str,
        *,
        date: str,
        time: str,
        assigned_agent: str | None = None,
        priority: str | None = None,
    ) -> dict[str, Any]:
        """Reschedule an existing callback."""
        current = self._latest_callback_state(callback_id)
        if current is None:
            raise ValueError("Callback not found for current tenant.")

        current["date"] = date
        current["time"] = time
        current["due_at"] = self._build_due_at(date, time).isoformat()
        current["assigned_agent"] = assigned_agent or current.get("assigned_agent")
        if priority:
            current["priority"] = priority
        current["status"] = "rescheduled"

        self._write_callback_log(
            action="callback_rescheduled",
            callback_id=callback_id,
            payload=current,
        )
        db.session.commit()
        return current

    def mark_callback_completed(self, callback_id: str) -> dict[str, Any]:
        """Mark callback as completed."""
        current = self._latest_callback_state(callback_id)
        if current is None:
            raise ValueError("Callback not found for current tenant.")

        current["status"] = "completed"
        current["completed_at"] = datetime.now(timezone.utc).isoformat()
        self._write_callback_log(
            action="callback_completed",
            callback_id=callback_id,
            payload=current,
        )
        db.session.commit()
        return current

    def get_due_callbacks(self, *, within_hours: int = 24) -> list[dict[str, Any]]:
        """Return callbacks due within the requested horizon."""
        now = datetime.now(timezone.utc)
        due_callbacks = []
        for callback in self._all_callback_states():
            if callback.get("status") == "completed":
                continue
            due_at = self._parse_iso(callback.get("due_at"))
            if due_at is None:
                continue
            hours_until_due = (due_at - now).total_seconds() / 3600
            if hours_until_due <= within_hours:
                callback["hours_until_due"] = round(hours_until_due, 2)
                due_callbacks.append(callback)
        due_callbacks.sort(key=lambda item: item.get("due_at", ""))
        return due_callbacks

    def _all_callback_states(self) -> list[dict[str, Any]]:
        """Build latest callback state for each callback id."""
        logs = AuditLog.query.filter(
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.entity == "callback",
            AuditLog.is_deleted.is_(False),
        ).order_by(AuditLog.created_at.asc()).all()
        latest_by_callback: dict[str, dict[str, Any]] = {}
        for log in logs:
            payload = self._parse_details(log.details)
            callback_id = payload.get("callback_id") or log.entity_id
            if callback_id:
                latest_by_callback[callback_id] = payload
        return list(latest_by_callback.values())

    def _latest_callback_state(self, callback_id: str) -> dict[str, Any] | None:
        """Fetch latest callback state."""
        for callback in self._all_callback_states():
            if callback.get("callback_id") == callback_id:
                return callback
        return None

    def _write_callback_log(self, *, action: str, callback_id: str, payload: dict[str, Any]) -> None:
        """Persist callback lifecycle event to audit log."""
        log = AuditLog(
            tenant_id=self.tenant_id,
            user_id=self.actor_user_id,
            action=action,
            entity="callback",
            entity_id=callback_id,
            details=json.dumps(payload, ensure_ascii=True),
        )
        db.session.add(log)

    def _build_due_at(self, date: str, time: str) -> datetime:
        """Build timezone-aware due datetime from simple date/time strings."""
        date_part = (date or "").strip()
        time_part = (time or "").strip() or "00:00"
        combined = f"{date_part} {time_part}"
        try:
            naive = datetime.strptime(combined, "%Y-%m-%d %H:%M")
        except ValueError:
            naive = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        return naive.replace(tzinfo=timezone.utc)

    def _parse_iso(self, value: str | None) -> datetime | None:
        """Parse ISO date safely."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _parse_details(self, details: str | None) -> dict[str, Any]:
        """Parse callback payload JSON safely."""
        try:
            return json.loads(details or "{}")
        except json.JSONDecodeError:
            return {}


# ==========================================
# SECTION: Tracking
# ==========================================
# Callback lifecycle is auditable through callback_* audit actions.
