"""
app/common/models.py
Common models shared across modules.
"""

from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import Index
from app.extensions import db
from app.common.mixins import BaseTenantModel, utcnow
from uuid import uuid4


class Task(BaseTenantModel):
    """
    Background task tracker for Celery jobs.
    Tracks async task status, results, and errors for Phase 2+ (document processing, etc.).
    
    PHASE_2_HOOK: Used by Celery tasks for OCR, fraud detection, API calls to external services.
    """
    __tablename__ = "tasks"
    __table_args__ = (
        Index("idx_task_status", "status"),
        Index("idx_task_created", "created_at"),
    )

    # Override tenant_id with ForeignKey constraint
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Task Identification
    task_name = db.Column(
        db.String(255),
        nullable=False,
        comment="Celery task name (e.g. 'app.tasks.process_ocr')"
    )
    task_id = db.Column(
        db.String(255),
        nullable=True,
        unique=True,
        comment="Celery task ID"
    )
    
    # Task Status
    status = db.Column(
        db.String(50),
        default="PENDING",
        nullable=False,
        index=True,
        comment="PENDING, RUNNING, SUCCESS, FAILURE, RETRY"
    )
    
    # Result
    result = db.Column(
        JSON,
        nullable=True,
        comment="Task result/output (JSON-serialized)"
    )
    
    # Error Handling
    error_message = db.Column(
        db.Text,
        nullable=True,
        comment="Error message if task failed"
    )
    
    # Timing
    started_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="When task started"
    )
    completed_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="When task completed"
    )
    
    # Retry Info
    retry_count = db.Column(
        db.Integer,
        default=0,
        comment="Number of retries"
    )
    max_retries = db.Column(
        db.Integer,
        default=3,
        comment="Maximum allowed retries"
    )
    
    # Related Entity
    related_entity_type = db.Column(
        db.String(50),
        nullable=True,
        comment="Entity this task relates to (e.g. 'Document')"
    )
    related_entity_id = db.Column(
        db.String(36),
        nullable=True,
        comment="ID of related entity"
    )
    
    # Input Parameters
    input_data = db.Column(
        JSON,
        nullable=True,
        comment="Task input parameters"
    )

    def __repr__(self):
        return f"<Task {self.task_name} status={self.status}>"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "task_name": self.task_name,
            "task_id": self.task_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
        })
        return data
