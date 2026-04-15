from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.extensions import db
from app.models.base import BaseModel


TASK_TYPES = [
    "Customer Follow-up",
    "Document Collection",
    "Bank Follow-up",
    "Payout Follow-up",
    "EMI Reminder",
    "Disbursal Confirmation",
    "Internal Meeting",
    "Other",
]

TASK_PRIORITIES = ["Low", "Medium", "High", "Urgent"]
TASK_STATUSES = ["Pending", "In Progress", "Done", "Overdue"]


class Task(BaseModel):
    """A task or reminder, optionally linked to a lead."""

    __tablename__ = "tasks"

    task_type = db.Column(
        db.Enum(*TASK_TYPES, name="task_type_enum"),
        nullable=False,
        default="Other",
    )
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=True)
    lead_id = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("leads.id"),
        nullable=True,
    )
    assigned_to = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_by = db.Column(
        PGUUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=False,
    )
    due_date = db.Column(db.Date, nullable=False)
    due_time = db.Column(db.Time, nullable=True)
    priority = db.Column(
        db.Enum(*TASK_PRIORITIES, name="task_priority_enum"),
        nullable=False,
        default="Medium",
    )
    status = db.Column(
        db.Enum(*TASK_STATUSES, name="task_status_enum"),
        nullable=False,
        default="Pending",
    )
    reminder_sent = db.Column(db.Boolean, default=False, nullable=False)
    reminder_sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completion_note = db.Column(db.Text, nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    assignee = db.relationship("User", foreign_keys=[assigned_to], backref="tasks_assigned")
    creator = db.relationship("User", foreign_keys=[created_by])
    lead = db.relationship("Lead", backref="tasks")

    @property
    def is_overdue(self) -> bool:
        if self.status == "Done":
            return False
        today = datetime.now(timezone.utc).date()
        return self.due_date < today

    @property
    def priority_color(self) -> str:
        colors = {
            "Low": "gray",
            "Medium": "blue",
            "High": "amber",
            "Urgent": "red",
        }
        return colors.get(self.priority, "gray")

    def mark_complete(self, note: str = None) -> None:
        self.status = "Done"
        self.completed_at = datetime.now(timezone.utc)
        if note:
            self.completion_note = note

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "task_type": self.task_type,
                "title": self.title,
                "description": self.description,
                "lead_id": str(self.lead_id) if self.lead_id else None,
                "assigned_to": str(self.assigned_to),
                "due_date": self.due_date.isoformat() if self.due_date else None,
                "due_time": self.due_time.isoformat() if self.due_time else None,
                "priority": self.priority,
                "status": self.status,
                "is_overdue": self.is_overdue,
                "priority_color": self.priority_color,
            }
        )
        return base
