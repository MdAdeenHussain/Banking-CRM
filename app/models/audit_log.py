from datetime import datetime

from flask import has_request_context, request
from flask_login import current_user
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.extensions import db
from app.models.base import BaseModel


AUDITED_TABLES = {
    "users",
    "leads",
    "commissions",
    "invoices",
    "tasks",
    "documents",
    "bank_applications",
    "client_financials",
    "bank_partners",
    "branches",
    "remarks",
}


class AuditLog(BaseModel):
    """Immutable audit trail record for data changes."""

    __tablename__ = "audit_logs"

    action = db.Column(
        db.Enum("CREATE", "UPDATE", "DELETE", name="audit_action_enum"),
        nullable=False,
    )
    table_name = db.Column(db.String(100), nullable=False, index=True)
    record_id = db.Column(db.String(36), nullable=False, index=True)
    changed_fields = db.Column(JSONB, nullable=True)
    old_values = db.Column(JSONB, nullable=True)
    new_values = db.Column(JSONB, nullable=True)
    performed_by = db.Column(db.String(36), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "action": self.action,
                "table_name": self.table_name,
                "record_id": self.record_id,
                "changed_fields": self.changed_fields,
                "old_values": self.old_values,
                "new_values": self.new_values,
                "performed_by": self.performed_by,
                "ip_address": self.ip_address,
            }
        )
        return base


def _get_current_user_id() -> str | None:
    try:
        if has_request_context() and current_user and current_user.is_authenticated:
            return str(current_user.id)
    except Exception:
        return None
    return None


def _get_request_info() -> tuple[str | None, str | None]:
    try:
        if has_request_context():
            return request.remote_addr, request.headers.get("User-Agent", "")[:500]
    except Exception:
        return None, None
    return None, None


def _serialize_value(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (int, float, bool)):
        return value
    return str(value)


def _get_model_changes(instance) -> tuple[dict, dict, list]:
    old_values = {}
    new_values = {}
    changed_fields = []

    for attr in db.inspect(instance).mapper.column_attrs:
        key = attr.key
        history = db.inspect(instance).attrs[key].history
        if history.has_changes():
            old_val = history.deleted[0] if history.deleted else None
            new_val = history.added[0] if history.added else getattr(instance, key)
            if "password" in key.lower() or "token" in key.lower() or "otp" in key.lower():
                old_val = "***REDACTED***"
                new_val = "***REDACTED***"
            old_values[key] = _serialize_value(old_val)
            new_values[key] = _serialize_value(new_val)
            changed_fields.append(key)

    return old_values, new_values, changed_fields


def _get_instance_values(instance) -> dict:
    values = {}
    for attr in db.inspect(instance).mapper.column_attrs:
        key = attr.key
        val = getattr(instance, key, None)
        if "password" in key.lower() or "token" in key.lower() or "otp" in key.lower():
            val = "***REDACTED***"
        values[key] = _serialize_value(val)
    return values


def register_audit_listeners():
    """Register automatic audit listeners."""

    @event.listens_for(Session, "after_flush")
    def after_flush(session, flush_context):
        user_id = _get_current_user_id()
        ip_address, user_agent = _get_request_info()
        audit_entries = []

        for instance in session.new:
            table_name = getattr(instance, "__tablename__", None)
            if table_name and table_name in AUDITED_TABLES:
                values = _get_instance_values(instance)
                audit_entries.append(
                    AuditLog(
                        action="CREATE",
                        table_name=table_name,
                        record_id=str(getattr(instance, "id", "")),
                        new_values=values,
                        performed_by=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                )

        for instance in session.dirty:
            table_name = getattr(instance, "__tablename__", None)
            if table_name and table_name in AUDITED_TABLES:
                old_vals, new_vals, changed = _get_model_changes(instance)
                if changed:
                    audit_entries.append(
                        AuditLog(
                            action="UPDATE",
                            table_name=table_name,
                            record_id=str(getattr(instance, "id", "")),
                            changed_fields=changed,
                            old_values=old_vals,
                            new_values=new_vals,
                            performed_by=user_id,
                            ip_address=ip_address,
                            user_agent=user_agent,
                        )
                    )

        for instance in session.deleted:
            table_name = getattr(instance, "__tablename__", None)
            if table_name and table_name in AUDITED_TABLES:
                values = _get_instance_values(instance)
                audit_entries.append(
                    AuditLog(
                        action="DELETE",
                        table_name=table_name,
                        record_id=str(getattr(instance, "id", "")),
                        old_values=values,
                        performed_by=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                )

        for entry in audit_entries:
            session.add(entry)
