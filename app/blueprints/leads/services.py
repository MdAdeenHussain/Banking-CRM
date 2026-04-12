"""
LoanAxis CRM — Lead Services

Business logic for lead CRUD, pipeline management, and timeline.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple

from flask import current_app
from flask_login import current_user
from sqlalchemy import or_, and_

from app.extensions import db
from app.models.lead import Lead, LeadStatusHistory, PIPELINE_STAGES
from app.models.remark import Remark
from app.models.user import User
from app.utils.duplicate_check import check_duplicate_lead
from app.utils.notifications import notify_lead_assigned, notify_lead_status_changed


def create_lead(data: dict, created_by_user: User) -> Tuple[Lead, Optional[str]]:
    """
    Create a new lead.

    Handles duplicate detection and auto high-value flagging.

    Returns:
        (lead, warning_message) — warning is set if duplicate was overridden
    """
    warning = None

    # Check for duplicates
    if not data.get("override_duplicate"):
        existing = check_duplicate_lead(
            data["mobile_primary"], data["loan_type"]
        )
        if existing:
            return None, f"Duplicate detected: Lead #{existing.lead_number} ({existing.customer_name})"

    # Create the lead
    lead = Lead(
        customer_name=data["customer_name"],
        mobile_primary=data["mobile_primary"],
        mobile_alternate=data.get("mobile_alternate"),
        email=data.get("email"),
        city=data.get("city"),
        state=data.get("state"),
        pincode=data.get("pincode"),
        occupation=data.get("occupation"),
        employer_name=data.get("employer_name"),
        monthly_income=data.get("monthly_income"),
        annual_income=data.get("annual_income"),
        cibil_score=data.get("cibil_score"),
        loan_type=data["loan_type"],
        loan_amount_applied=data.get("loan_amount_applied"),
        bank_preferred=data.get("bank_preferred"),
        lead_source=data.get("lead_source"),
        priority_tag=data.get("priority_tag", "Warm"),
        assigned_executive_id=data.get("assigned_executive_id") or created_by_user.id,
        assigned_admin_id=data.get("assigned_admin_id"),
        branch_id=data.get("branch_id") or created_by_user.branch_id,
        created_by=created_by_user.id,
        pipeline_stage="New Lead",
        stage_updated_at=datetime.now(timezone.utc),
    )

    # Handle duplicate override
    if data.get("override_duplicate"):
        existing = check_duplicate_lead(data["mobile_primary"], data["loan_type"])
        if existing:
            lead.is_duplicate = True
            lead.duplicate_of_lead_id = existing.id
            warning = "Lead created with duplicate override."

    # Auto high-value detection
    threshold = current_app.config.get("HIGH_VALUE_THRESHOLD", 5000000)
    if lead.loan_amount_applied and lead.loan_amount_applied >= threshold:
        lead.is_high_value = True

    db.session.add(lead)

    # Create initial status history
    history = LeadStatusHistory(
        lead_id=lead.id,
        from_stage=None,
        to_stage="New Lead",
        changed_by=created_by_user.id,
        note="Lead created",
    )
    db.session.add(history)

    db.session.commit()

    # Notify assigned executive (if different from creator)
    if lead.assigned_executive_id and lead.assigned_executive_id != created_by_user.id:
        notify_lead_assigned(lead, lead.assigned_executive_id)
        db.session.commit()

    return lead, warning


def update_lead(lead_id: str, data: dict) -> Lead:
    """Update an existing lead's details."""
    lead = Lead.query.get_or_404(lead_id)

    for key, value in data.items():
        if hasattr(lead, key) and key not in ("id", "lead_number", "created_at", "created_by"):
            setattr(lead, key, value)

    # Re-check high value
    threshold = current_app.config.get("HIGH_VALUE_THRESHOLD", 5000000)
    if lead.loan_amount_applied and lead.loan_amount_applied >= threshold:
        lead.is_high_value = True
    else:
        lead.is_high_value = False

    db.session.commit()
    return lead


def update_stage(lead_id: str, new_stage: str, user: User, note: str = None) -> Lead:
    """
    Update a lead's pipeline stage.

    Creates a status history record and notifies relevant users.
    """
    lead = Lead.query.get_or_404(lead_id)
    old_stage = lead.pipeline_stage

    if old_stage == new_stage:
        return lead

    # Validate stage transition
    if new_stage not in PIPELINE_STAGES:
        raise ValueError(f"Invalid pipeline stage: {new_stage}")

    lead.pipeline_stage = new_stage
    lead.stage_updated_at = datetime.now(timezone.utc)

    # Record history
    history = LeadStatusHistory(
        lead_id=lead.id,
        from_stage=old_stage,
        to_stage=new_stage,
        changed_by=user.id,
        note=note,
    )
    db.session.add(history)
    db.session.commit()

    # Notify relevant users
    notify_user_ids = set()
    if lead.assigned_executive_id and lead.assigned_executive_id != user.id:
        notify_user_ids.add(lead.assigned_executive_id)
    if lead.assigned_admin_id and lead.assigned_admin_id != user.id:
        notify_user_ids.add(lead.assigned_admin_id)

    if notify_user_ids:
        notify_lead_status_changed(lead, old_stage, new_stage, list(notify_user_ids))
        db.session.commit()

    return lead


def get_pipeline_leads(user, stage: str = None) -> dict[str, list]:
    """
    Get leads grouped by pipeline stage for Kanban view.

    Respects role-based access control.
    """
    query = Lead.query.filter(Lead.is_deleted == False, Lead.is_active == True)

    if user.role == "employee":
        query = query.filter(Lead.assigned_executive_id == user.id)
    elif user.role == "admin" and user.branch_id:
        query = query.filter(Lead.branch_id == user.branch_id)

    if stage:
        query = query.filter(Lead.pipeline_stage == stage)

    leads = query.order_by(Lead.stage_updated_at.desc()).all()

    # Group by stage
    pipeline = {s: [] for s in PIPELINE_STAGES}
    for lead in leads:
        if lead.pipeline_stage in pipeline:
            pipeline[lead.pipeline_stage].append(lead)

    return pipeline


def get_filtered_leads(user, filters: dict, page: int = 1, per_page: int = 25):
    """
    Get paginated leads with advanced filtering.

    Returns SQLAlchemy pagination object.
    """
    query = Lead.query.filter(Lead.is_deleted == False)

    # Role-based access
    if user.role == "employee":
        query = query.filter(Lead.assigned_executive_id == user.id)
    elif user.role == "admin" and user.branch_id:
        query = query.filter(Lead.branch_id == user.branch_id)

    # Apply filters
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.filter(or_(
            Lead.customer_name.ilike(search_term),
            Lead.mobile_primary.ilike(search_term),
            Lead.email.ilike(search_term),
            Lead.lead_number.ilike(search_term),
        ))

    if filters.get("pipeline_stage"):
        query = query.filter(Lead.pipeline_stage == filters["pipeline_stage"])

    if filters.get("loan_type"):
        query = query.filter(Lead.loan_type == filters["loan_type"])

    if filters.get("priority_tag"):
        query = query.filter(Lead.priority_tag == filters["priority_tag"])

    if filters.get("lead_source"):
        query = query.filter(Lead.lead_source == filters["lead_source"])

    if filters.get("assigned_executive_id"):
        query = query.filter(Lead.assigned_executive_id == filters["assigned_executive_id"])

    if filters.get("date_from"):
        query = query.filter(Lead.created_at >= filters["date_from"])

    if filters.get("date_to"):
        query = query.filter(Lead.created_at <= filters["date_to"])

    if filters.get("city"):
        query = query.filter(Lead.city.ilike(f"%{filters['city']}%"))

    # Sort
    sort_by = filters.get("sort_by", "created_at")
    sort_dir = filters.get("sort_dir", "desc")
    sort_col = getattr(Lead, sort_by, Lead.created_at)
    if sort_dir == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_lead_timeline(lead_id: str) -> list[dict]:
    """
    Build a chronological timeline of all events for a lead.

    Combines: status changes, remarks, document uploads, tasks, commissions.
    """
    events = []

    lead = Lead.query.get_or_404(lead_id)

    # Status changes
    for history in lead.status_history.all():
        changer_name = "System"
        if history.changer:
            changer_name = history.changer.full_name
        events.append({
            "type": "status_change",
            "timestamp": history.changed_at,
            "title": f"Status: {history.from_stage or 'New'} → {history.to_stage}",
            "description": history.note,
            "actor": changer_name,
            "color": "blue",
            "icon": "git-branch",
        })

    # Remarks
    for remark in lead.remarks.all():
        author_name = remark.author.full_name if remark.author else "Unknown"
        events.append({
            "type": "remark",
            "timestamp": remark.created_at,
            "title": f"{remark.remark_type} Note",
            "description": remark.content,
            "actor": author_name,
            "color": "purple",
            "icon": "message-circle",
        })

    # Documents
    for doc in lead.documents.filter_by(is_deleted=False).all():
        uploader_name = doc.uploader.full_name if doc.uploader else "Unknown"
        events.append({
            "type": "document",
            "timestamp": doc.uploaded_at or doc.created_at,
            "title": f"Document: {doc.document_type}",
            "description": f"{doc.original_filename} uploaded",
            "actor": uploader_name,
            "color": "indigo",
            "icon": "file-up",
        })

    # Sort by timestamp descending
    events.sort(key=lambda e: e["timestamp"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    return events


def add_remark(lead_id: str, data: dict, user: User) -> Remark:
    """Add a remark/call note to a lead."""
    remark = Remark(
        lead_id=lead_id,
        remark_type=data["remark_type"],
        content=data["content"],
        call_duration_min=data.get("call_duration_min"),
        call_outcome=data.get("call_outcome"),
        created_by=user.id,
    )
    db.session.add(remark)
    db.session.commit()
    return remark
