"""LoanAxis CRM — Employee Services"""
from datetime import datetime, timezone
from sqlalchemy import func
from app.extensions import db
from app.models.user import User
from app.models.lead import Lead
from app.models.commission import Commission
from app.models.task import Task


def create_employee(data, created_by_id):
    """Create a new employee/admin account."""
    if User.query.filter_by(email=data["email"].lower().strip()).first():
        raise ValueError("Email already registered.")

    user = User(
        full_name=data["full_name"],
        email=data["email"].lower().strip(),
        mobile=data["mobile"],
        role=data["role"],
        branch_id=data.get("branch_id") or None,
        joining_date=data.get("joining_date") or datetime.now(timezone.utc),
        created_by=created_by_id,
        is_active=True,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return user


def get_performance_summary(user_id):
    """Compute an employee's performance metrics."""
    total_leads = Lead.query.filter_by(assigned_executive_id=user_id, is_deleted=False).count()
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    leads_this_month = Lead.query.filter(
        Lead.assigned_executive_id == user_id, Lead.is_deleted == False,
        Lead.created_at >= month_start
    ).count()
    total_disbursals = Lead.query.filter_by(
        assigned_executive_id=user_id, pipeline_stage="Disbursed", is_deleted=False).count()
    conversion_rate = round((total_disbursals / total_leads * 100), 1) if total_leads > 0 else 0
    total_commission = db.session.query(func.coalesce(func.sum(Commission.employee_amount), 0)).filter(
        Commission.employee_id == user_id, Commission.is_deleted == False).scalar() or 0
    pending_tasks = Task.query.filter(
        Task.assigned_to == user_id, Task.is_deleted == False, Task.status != "Done").count()

    return {
        "total_leads": total_leads, "leads_this_month": leads_this_month,
        "total_disbursals": total_disbursals, "conversion_rate": conversion_rate,
        "total_commission": total_commission, "pending_tasks": pending_tasks,
    }
