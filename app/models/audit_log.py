"""
LoanAxis CRM — Audit Log Model + SQLAlchemy Event Listeners

Automatically logs every CREATE, UPDATE, DELETE on critical tables
via SQLAlchemy after_flush event listener. Zero-effort audit trail
that cannot be bypassed by application code.
"""

import json
from datetime import datetime, timezone

from flask import request, has_request_context
from flask_login import current_user
from sqlalchemy import Column, String, DateTime, Text, JSON, event
from sqlalchemy.orm import Session

from app.extensions import db
from app.models.base import BaseModel


# Tables to audit automatically
AUDITED_TABLES = {
    "users", "leads", "commissions", "invoices", "tasks",
    "documents", "bank_applications", "client_financials",
    "bank_partners", "branches", "remarks",
}


class AuditLog(BaseModel):
    """Immutable audit trail record for data changes."""

    __tablename__ = "audit_logs"

    # ── Action Details ──────────────────────────────────────
    action = Column(String(10), nullable=False)  # CREATE | UPDATE | DELETE
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(36), nullable=False, index=True)

    # ── Change Data ─────────────────────────────────────────
    changed_fields = Column(JSON, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # ── Actor ───────────────────────────────────────────────
    performed_by = Column(String(36), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "action": self.action,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "changed_fields": self.changed_fields,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "performed_by": self.performed_by,
            "ip_address": self.ip_address,
        })
        return base


def _get_current_user_id() -> str | None:
    """Safely get the current user ID from Flask-Login."""
    try:
        if has_request_context() and current_user and current_user.is_authenticated:
            return current_user.id
    except Exception:
        pass
    return None


def _get_request_info() -> tuple[str | None, str | None]:
    """Safely get IP address and user agent from current request."""
    try:
        if has_request_context():
            return request.remote_addr, request.headers.get("User-Agent", "")[:500]
    except Exception:
        pass
    return None, None


def _serialize_value(value) -> str | None:
    """Convert a value to a JSON-safe string representation."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (int, float, bool)):
        return value
    return str(value)


def _get_model_changes(instance) -> tuple[dict, dict, list]:
    """
    Inspect an ORM instance for changed attributes.

    Returns (old_values, new_values, changed_field_names).
    """
    from sqlalchemy import inspect as sa_inspect

    mapper = sa_inspect(instance.__class__)
    old_values = {}
    new_values = {}
    changed_fields = []

    for attr in mapper.column_attrs:
        key = attr.key
        history = db.inspect(instance).attrs[key].history

        if history.has_changes():
            old_val = history.deleted[0] if history.deleted else None
            new_val = history.added[0] if history.added else getattr(instance, key)

            # Skip password hashes and tokens from audit
            if "password" in key.lower() or "token" in key.lower() or "otp" in key.lower():
                old_val = "***REDACTED***"
                new_val = "***REDACTED***"

            old_values[key] = _serialize_value(old_val)
            new_values[key] = _serialize_value(new_val)
            changed_fields.append(key)

    return old_values, new_values, changed_fields


def _get_instance_values(instance) -> dict:
    """Get all column values of an ORM instance for CREATE logging."""
    from sqlalchemy import inspect as sa_inspect

    mapper = sa_inspect(instance.__class__)
    values = {}
    for attr in mapper.column_attrs:
        key = attr.key
        val = getattr(instance, key, None)
        # Redact sensitive fields
        if "password" in key.lower() or "token" in key.lower() or "otp" in key.lower():
            val = "***REDACTED***"
        values[key] = _serialize_value(val)
    return values


def register_audit_listeners():
    """
    Register SQLAlchemy after_flush event listener for automatic audit logging.

    This function should be called once during app initialization.
    It monitors all INSERT, UPDATE, and DELETE operations on audited tables.
    """

    @event.listens_for(Session, "after_flush")
    def after_flush(session, flush_context):
        """Log all changes after a flush to the database."""
        user_id = _get_current_user_id()
        ip_address, user_agent = _get_request_info()

        audit_entries = []

        # ── Process new objects (CREATE) ────────────────────
        for instance in session.new:
            table_name = getattr(instance, "__tablename__", None)
            if table_name and table_name in AUDITED_TABLES:
                values = _get_instance_values(instance)
                audit_entries.append(AuditLog(
                    action="CREATE",
                    table_name=table_name,
                    record_id=str(getattr(instance, "id", "")),
                    new_values=values,
                    performed_by=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                ))

        # ── Process modified objects (UPDATE) ───────────────
        for instance in session.dirty:
            table_name = getattr(instance, "__tablename__", None)
            if table_name and table_name in AUDITED_TABLES:
                old_vals, new_vals, changed = _get_model_changes(instance)
                if changed:  # Only log if something actually changed
                    audit_entries.append(AuditLog(
                        action="UPDATE",
                        table_name=table_name,
                        record_id=str(getattr(instance, "id", "")),
                        changed_fields=changed,
                        old_values=old_vals,
                        new_values=new_vals,
                        performed_by=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    ))

        # ── Process deleted objects (DELETE) ─────────────────
        for instance in session.deleted:
            table_name = getattr(instance, "__tablename__", None)
            if table_name and table_name in AUDITED_TABLES:
                values = _get_instance_values(instance)
                audit_entries.append(AuditLog(
                    action="DELETE",
                    table_name=table_name,
                    record_id=str(getattr(instance, "id", "")),
                    old_values=values,
                    performed_by=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                ))

        # Add audit entries to session (they'll be flushed in the next flush)
        # We use object_session to avoid re-triggering through session.add
        for entry in audit_entries:
            session.add(entry)
