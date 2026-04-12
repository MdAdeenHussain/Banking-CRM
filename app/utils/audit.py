"""
LoanAxis CRM — Audit Utility

Manual audit logging helper for cases where SQLAlchemy event listeners
don't capture actions (e.g., bulk operations, external API calls).
"""

from flask import request, has_request_context
from flask_login import current_user

from app.extensions import db
from app.models.audit_log import AuditLog


def log_action(
    action: str,
    table_name: str,
    record_id: str,
    changed_fields: list[str] = None,
    old_values: dict = None,
    new_values: dict = None,
    user_id: str = None,
) -> AuditLog:
    """
    Manually log an audit action.

    Use this for operations not captured by the automatic SQLAlchemy
    event listener (e.g., bulk updates, external integrations).

    Args:
        action: "CREATE", "UPDATE", or "DELETE"
        table_name: The database table affected
        record_id: ID of the affected record
        changed_fields: List of field names that changed (for UPDATE)
        old_values: Previous values (for UPDATE/DELETE)
        new_values: New values (for CREATE/UPDATE)
        user_id: Override the current user ID

    Returns:
        The created AuditLog instance
    """
    # Get actor info
    actor_id = user_id
    ip_address = None
    user_agent = None

    if not actor_id:
        try:
            if current_user and current_user.is_authenticated:
                actor_id = current_user.id
        except Exception:
            pass

    if has_request_context():
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent", "")[:500]

    entry = AuditLog(
        action=action,
        table_name=table_name,
        record_id=str(record_id),
        changed_fields=changed_fields,
        old_values=old_values,
        new_values=new_values,
        performed_by=actor_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.session.add(entry)
    # Don't commit — let the caller's transaction handle it
    return entry
