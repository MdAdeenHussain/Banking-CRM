"""
LoanAxis CRM — Task Model

Manages tasks and reminders for lead follow-ups, document collection,
bank follow-ups, and internal coordination.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Date, Time
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


TASK_TYPES = [
    "Customer Follow-up", "Document Collection", "Bank Follow-up",
    "Payout Follow-up", "EMI Reminder", "Disbursal Confirmation",
    "Internal Meeting", "Other",
]

TASK_PRIORITIES = ["Low", "Medium", "High", "Urgent"]

TASK_STATUSES = ["Pending", "In Progress", "Done", "Overdue"]


class Task(BaseModel):
    """A task or reminder, optionally linked to a lead."""

    __tablename__ = "tasks"

    # ── Task Details ────────────────────────────────────────
    task_type = Column(String(30), nullable=False, default="Other")
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)

    # ── Linked Lead (optional) ──────────────────────────────
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=True)

    # ── Assignment ──────────────────────────────────────────
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)

    # ── Scheduling ──────────────────────────────────────────
    due_date = Column(Date, nullable=False)
    due_time = Column(Time, nullable=True)

    # ── Priority & Status ───────────────────────────────────
    priority = Column(String(10), nullable=False, default="Medium")
    status = Column(String(15), nullable=False, default="Pending")

    # ── Reminder ────────────────────────────────────────────
    reminder_sent = Column(Boolean, default=False, nullable=False)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)

    # ── Completion ──────────────────────────────────────────
    completion_note = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ───────────────────────────────────────
    assignee = relationship("User", foreign_keys=[assigned_to], backref="tasks_assigned")
    creator = relationship("User", foreign_keys=[created_by])
    lead = relationship("Lead", backref="tasks")

    @property
    def is_overdue(self) -> bool:
        """Check if the task is past its due date and not completed."""
        if self.status == "Done":
            return False
        today = datetime.now(timezone.utc).date()
        return self.due_date < today

    @property
    def priority_color(self) -> str:
        """Return color for priority display."""
        colors = {
            "Low": "gray",
            "Medium": "blue",
            "High": "amber",
            "Urgent": "red",
        }
        return colors.get(self.priority, "gray")

    def mark_complete(self, note: str = None) -> None:
        """Mark the task as completed."""
        self.status = "Done"
        self.completed_at = datetime.now(timezone.utc)
        if note:
            self.completion_note = note

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "task_type": self.task_type,
            "title": self.title,
            "description": self.description,
            "lead_id": self.lead_id,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "due_time": self.due_time.isoformat() if self.due_time else None,
            "priority": self.priority,
            "status": self.status,
            "is_overdue": self.is_overdue,
            "priority_color": self.priority_color,
        })
        return base
