"""
LoanAxis CRM — Dashboard Services

KPI computation, recent leads, task summaries, and chart data.
"""

from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import func, and_

from app.extensions import db
from app.models.lead import Lead, PIPELINE_STAGES
from app.models.commission import Commission
from app.models.task import Task
from app.models.user import User
from app.models.notification import Notification


def get_kpi_data(user) -> dict[str, Any]:
    """
    Compute KPI card data based on user role.

    Super Admin / Admin: aggregate data across all (or branch) leads.
    Employee: own leads only.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # Base query filtered by role
    base_query = Lead.query.filter(Lead.is_deleted == False)
    if user.role == "employee":
        base_query = base_query.filter(Lead.assigned_executive_id == user.id)
    elif user.role == "admin" and user.branch_id:
        base_query = base_query.filter(Lead.branch_id == user.branch_id)

    # Total leads
    total_leads = base_query.count()

    # Today's new leads
    todays_leads = base_query.filter(Lead.created_at >= today_start).count()

    # Converted (Disbursed) leads
    converted_leads = base_query.filter(Lead.pipeline_stage == "Disbursed").count()

    # This month's leads
    this_month_leads = base_query.filter(Lead.created_at >= month_start).count()
    last_month_leads = base_query.filter(
        and_(Lead.created_at >= last_month_start, Lead.created_at < month_start)
    ).count()

    # Lead growth percentage
    if last_month_leads > 0:
        lead_growth_pct = round(((this_month_leads - last_month_leads) / last_month_leads) * 100, 1)
    else:
        lead_growth_pct = 100.0 if this_month_leads > 0 else 0.0

    # Commission data
    comm_query = Commission.query.filter(Commission.is_deleted == False)
    if user.role == "employee":
        comm_query = comm_query.filter(Commission.employee_id == user.id)

    total_commission = db.session.query(
        func.coalesce(func.sum(comm_query.subquery().c.gross_commission), 0)
    ).scalar() or 0

    pending_payout = db.session.query(
        func.coalesce(func.sum(
            Commission.gross_commission
        ), 0)
    ).filter(
        Commission.is_deleted == False,
        Commission.payout_status == "Pending",
    ).scalar() or 0

    # Disbursed amount
    from app.models.client_financial import ClientFinancial
    disbursed_amount = db.session.query(
        func.coalesce(func.sum(ClientFinancial.loan_amount_disbursed), 0)
    ).scalar() or 0

    return {
        "total_leads": total_leads,
        "todays_leads": todays_leads,
        "converted_leads": converted_leads,
        "this_month_leads": this_month_leads,
        "lead_growth_pct": lead_growth_pct,
        "total_commission": total_commission,
        "pending_payout": pending_payout,
        "disbursed_amount": disbursed_amount,
    }


def get_recent_leads(user, limit: int = 10) -> list:
    """Get the most recently created leads visible to the user."""
    query = Lead.query.filter(Lead.is_deleted == False)

    if user.role == "employee":
        query = query.filter(Lead.assigned_executive_id == user.id)
    elif user.role == "admin" and user.branch_id:
        query = query.filter(Lead.branch_id == user.branch_id)

    return query.order_by(Lead.created_at.desc()).limit(limit).all()


def get_tasks_due_today(user) -> list:
    """Get tasks due today for the user."""
    today = datetime.now(timezone.utc).date()
    query = Task.query.filter(
        Task.is_deleted == False,
        Task.due_date == today,
        Task.status != "Done",
    )

    if user.role == "employee":
        query = query.filter(Task.assigned_to == user.id)
    elif user.role == "admin" and user.branch_id:
        # Admin sees tasks for their team
        team_ids = [u.id for u in User.query.filter_by(
            branch_id=user.branch_id, is_deleted=False
        ).all()]
        query = query.filter(Task.assigned_to.in_(team_ids))

    return query.order_by(Task.priority.desc()).all()


def get_pipeline_summary(user) -> dict[str, int]:
    """Get lead count per pipeline stage for funnel visualization."""
    query = Lead.query.filter(Lead.is_deleted == False, Lead.is_active == True)

    if user.role == "employee":
        query = query.filter(Lead.assigned_executive_id == user.id)
    elif user.role == "admin" and user.branch_id:
        query = query.filter(Lead.branch_id == user.branch_id)

    results = db.session.query(
        Lead.pipeline_stage,
        func.count(Lead.id),
    ).filter(
        Lead.is_deleted == False,
        Lead.is_active == True,
    ).group_by(Lead.pipeline_stage).all()

    # Return ordered by pipeline stages
    summary = {stage: 0 for stage in PIPELINE_STAGES}
    for stage, count in results:
        if stage in summary:
            summary[stage] = count

    return summary


def get_monthly_lead_data(user, months: int = 12) -> dict:
    """Get monthly lead creation counts for bar chart."""
    now = datetime.now(timezone.utc)
    labels = []
    values = []

    for i in range(months - 1, -1, -1):
        month_date = now - timedelta(days=30 * i)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            next_month = (month_start + timedelta(days=32)).replace(day=1)
        else:
            next_month = now

        count = Lead.query.filter(
            Lead.is_deleted == False,
            Lead.created_at >= month_start,
            Lead.created_at < next_month,
        ).count()

        labels.append(month_start.strftime("%b %Y"))
        values.append(count)

    return {"labels": labels, "values": values}
