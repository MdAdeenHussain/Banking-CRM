"""Banking DSA CRM — Analytics Services"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, extract
from app.extensions import db
from app.models.lead import Lead, PIPELINE_STAGES, LOAN_TYPES, LEAD_SOURCES
from app.models.commission import Commission
from app.models.user import User
from app.models.bank_partner import BankPartner


def monthly_leads_data(months=12):
    """Monthly leads vs disbursals for grouped bar chart."""
    now = datetime.now(timezone.utc)
    labels, leads_data, disbursals_data = [], [], []
    for i in range(months - 1, -1, -1):
        d = now - timedelta(days=30 * i)
        ms = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        me = (ms + timedelta(days=32)).replace(day=1)
        labels.append(ms.strftime("%b %Y"))
        leads_data.append(Lead.query.filter(Lead.is_deleted == False, Lead.created_at >= ms, Lead.created_at < me).count())
        disbursals_data.append(Lead.query.filter(Lead.is_deleted == False, Lead.pipeline_stage == "Disbursed",
                                                  Lead.stage_updated_at >= ms, Lead.stage_updated_at < me).count())
    return {"labels": labels, "leads": leads_data, "disbursals": disbursals_data}


def conversion_funnel_data():
    """Lead conversion funnel."""
    result = {}
    for stage in PIPELINE_STAGES:
        result[stage] = Lead.query.filter(Lead.is_deleted == False, Lead.pipeline_stage == stage).count()
    return result


def lead_source_breakdown():
    """Lead source distribution for donut chart."""
    results = db.session.query(Lead.lead_source, func.count(Lead.id)).filter(
        Lead.is_deleted == False).group_by(Lead.lead_source).all()
    return {(s or "Unknown"): c for s, c in results}


def loan_type_distribution():
    """Loan type distribution for pie chart."""
    results = db.session.query(Lead.loan_type, func.count(Lead.id)).filter(
        Lead.is_deleted == False).group_by(Lead.loan_type).all()
    return {t: c for t, c in results}


def commission_trend_data(months=12):
    """Monthly commission payout trend."""
    now = datetime.now(timezone.utc)
    labels, values = [], []
    for i in range(months - 1, -1, -1):
        d = now - timedelta(days=30 * i)
        ms = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        me = (ms + timedelta(days=32)).replace(day=1)
        labels.append(ms.strftime("%b %Y"))
        total = db.session.query(func.coalesce(func.sum(Commission.gross_commission), 0)).filter(
            Commission.is_deleted == False, Commission.created_at >= ms, Commission.created_at < me
        ).scalar() or 0
        values.append(float(total))
    return {"labels": labels, "values": values}


def employee_performance_data():
    """Employee performance matrix for radar/bubble chart."""
    employees = User.query.filter_by(
        role="employee",
        is_deleted=False,
        is_active_flag=True,
    ).all()
    data = []
    for emp in employees:
        leads_count = Lead.query.filter_by(assigned_executive_id=emp.id, is_deleted=False).count()
        converted = Lead.query.filter_by(assigned_executive_id=emp.id, pipeline_stage="Disbursed", is_deleted=False).count()
        commission = db.session.query(func.coalesce(func.sum(Commission.employee_amount), 0)).filter(
            Commission.employee_id == emp.id, Commission.is_deleted == False).scalar() or 0
        data.append({
            "name": emp.full_name, "employee_id": emp.employee_id,
            "leads": leads_count, "converted": converted, "commission": float(commission),
        })
    return data


def cibil_distribution():
    """CIBIL score histogram."""
    buckets = {"300-499": 0, "500-599": 0, "600-649": 0, "650-699": 0, "700-749": 0, "750-799": 0, "800-900": 0}
    leads = Lead.query.filter(Lead.is_deleted == False, Lead.cibil_score.isnot(None)).all()
    for lead in leads:
        s = lead.cibil_score
        if s < 500: buckets["300-499"] += 1
        elif s < 600: buckets["500-599"] += 1
        elif s < 650: buckets["600-649"] += 1
        elif s < 700: buckets["650-699"] += 1
        elif s < 750: buckets["700-749"] += 1
        elif s < 800: buckets["750-799"] += 1
        else: buckets["800-900"] += 1
    return buckets
