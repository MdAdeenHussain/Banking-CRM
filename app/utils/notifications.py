"""
LoanAxis CRM — Notification Helper

Centralized notification creation utility used across all modules.
"""

from app.extensions import db
from app.models.notification import Notification


def create_notification(
    user_id: str,
    title: str,
    body: str = None,
    notification_type: str = "info",
    related_model: str = None,
    related_id: str = None,
) -> Notification:
    """
    Create an in-app notification for a user.

    Args:
        user_id: The recipient user's ID
        title: Notification title (shown in bell dropdown)
        body: Optional notification body text
        notification_type: One of the NOTIFICATION_TYPES constants
        related_model: Model name for deep-linking (e.g., "lead", "task")
        related_id: ID of the related record for deep-linking

    Returns:
        The created Notification instance
    """
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        related_model=related_model,
        related_id=related_id,
    )
    db.session.add(notification)
    return notification


def notify_lead_assigned(lead, assigned_user_id: str) -> None:
    """Notify a user that a lead has been assigned to them."""
    create_notification(
        user_id=assigned_user_id,
        title=f"New lead assigned: {lead.customer_name}",
        body=f"Lead #{lead.lead_number} ({lead.loan_type} - ₹{lead.loan_amount_applied:,.0f}) has been assigned to you.",
        notification_type="lead_assigned",
        related_model="lead",
        related_id=lead.id,
    )


def notify_lead_status_changed(lead, from_stage: str, to_stage: str, user_ids: list[str]) -> None:
    """Notify relevant users about a lead status change."""
    for uid in user_ids:
        create_notification(
            user_id=uid,
            title=f"Lead status updated: {lead.customer_name}",
            body=f"Lead #{lead.lead_number} moved from {from_stage} → {to_stage}.",
            notification_type="lead_status_changed",
            related_model="lead",
            related_id=lead.id,
        )


def notify_task_due(task, user_id: str) -> None:
    """Notify a user about a due task."""
    create_notification(
        user_id=user_id,
        title=f"Task due today: {task.title}",
        body=f"Task '{task.title}' is due today. Priority: {task.priority}.",
        notification_type="task_due_today",
        related_model="task",
        related_id=task.id,
    )


def notify_document_uploaded(lead, uploaded_by_name: str, user_ids: list[str]) -> None:
    """Notify relevant users about a document upload."""
    for uid in user_ids:
        create_notification(
            user_id=uid,
            title=f"Document uploaded for {lead.customer_name}",
            body=f"{uploaded_by_name} uploaded a document for lead #{lead.lead_number}.",
            notification_type="document_uploaded",
            related_model="lead",
            related_id=lead.id,
        )


def notify_payout_received(commission, user_ids: list[str]) -> None:
    """Notify users about a payout received."""
    for uid in user_ids:
        create_notification(
            user_id=uid,
            title="Commission payout received",
            body=f"₹{commission.net_after_tds:,.2f} commission payout has been received.",
            notification_type="payout_received",
            related_model="commission",
            related_id=commission.id,
        )
