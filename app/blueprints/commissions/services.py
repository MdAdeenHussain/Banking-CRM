"""LoanAxis CRM — Commission Services"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models.commission import Commission


def create_commission(data, lead_id, employee_id=None, bank_application_id=None):
    """Create a commission record with auto-calculated splits."""
    comm = Commission(
        lead_id=lead_id,
        bank_application_id=bank_application_id,
        gross_commission=data["gross_commission"],
        tds_rate_pct=data.get("tds_rate_pct", 5.0),
        company_share_pct=data.get("company_share_pct", 40.0),
        admin_share_pct=data.get("admin_share_pct", 20.0),
        employee_share_pct=data.get("employee_share_pct", 40.0),
        employee_id=employee_id,
        payout_status=data.get("payout_status", "Pending"),
        payment_reference=data.get("payment_reference"),
        remarks=data.get("remarks"),
    )
    comm.calculate_splits()
    db.session.add(comm)
    db.session.commit()
    return comm


def get_payout_summary(user=None):
    """Get commission payout summary for dashboard widgets."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    base = Commission.query.filter(Commission.is_deleted == False)
    if user and user.role == "employee":
        base = base.filter(Commission.employee_id == user.id)

    def _sum(query):
        return db.session.query(func.coalesce(func.sum(query.subquery().c.gross_commission), 0)).scalar() or 0

    return {
        "today": _sum(base.filter(Commission.created_at >= today_start)),
        "this_week": _sum(base.filter(Commission.created_at >= week_start)),
        "this_month": _sum(base.filter(Commission.created_at >= month_start)),
        "this_year": _sum(base.filter(Commission.created_at >= year_start)),
        "pending": _sum(base.filter(Commission.payout_status == "Pending")),
    }
