"""Analytics and Reporting Routes"""
from flask import Blueprint, render_template, request, jsonify, session
from app.models.lead import Lead
from app.models.commission_tracker import CommissionTracker
from app.models.employee import Employee
from app.models.invoice import Invoice
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.utils.decorators import login_required, role_required, permission_required
from app.services.analytics_service import AnalyticsService
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
import json

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/dashboard')
@login_required
@permission_required('analytics', 'view')
def analytics_dashboard():
    """Main analytics dashboard"""
    time_period = request.args.get('period', '30')  # 7, 30, 90, 365
    time_period = int(time_period)
    
    start_date = datetime.utcnow() - timedelta(days=time_period)
    
    # Get KPIs
    kpis = AnalyticsService.get_dashboard_kpis(time_period)
    
    # Get trend data for charts
    leads_trend = AnalyticsService.get_leads_trend(start_date)
    commission_trend = AnalyticsService.get_commission_trend(start_date)
    leads_by_status = AnalyticsService.get_leads_by_status()
    top_employees = AnalyticsService.get_top_employees(limit=10)
    
    return render_template(
        'analytics/dashboard.html',
        kpis=kpis,
        leads_trend=json.dumps(leads_trend),
        commission_trend=json.dumps(commission_trend),
        leads_by_status=json.dumps(leads_by_status),
        top_employees=json.dumps(top_employees),
        time_period=time_period
    )


@analytics_bp.route('/leads')
@login_required
@permission_required('analytics', 'view')
def leads_analytics():
    """Leads analytics report"""
    time_period = request.args.get('period', '30')
    time_period = int(time_period)
    
    start_date = datetime.utcnow() - timedelta(days=time_period)
    
    # Lead statistics
    total_leads = Lead.query.count()
    new_leads_period = Lead.query.filter(Lead.created_at >= start_date).count()
    
    # Leads by status
    leads_by_status = db.session.query(
        Lead.status,
        func.count(Lead.id).label('count')
    ).group_by(Lead.status).all()
    
    # Leads by source
    leads_by_source = db.session.query(
        Lead.lead_source,
        func.count(Lead.id).label('count')
    ).filter(Lead.created_at >= start_date).group_by(Lead.lead_source).all()
    
    # Average loan amount by priority
    avg_by_priority = db.session.query(
        Lead.priority_tag,
        func.avg(Lead.loan_amount_applied).label('avg_amount')
    ).group_by(Lead.priority_tag).all()
    
    # Conversion rate (approved/total)
    approved_leads = Lead.query.filter(Lead.status == 'approved').count()
    conversion_rate = (approved_leads / total_leads * 100) if total_leads > 0 else 0
    
    return render_template(
        'analytics/leads.html',
        total_leads=total_leads,
        new_leads_period=new_leads_period,
        leads_by_status=leads_by_status,
        leads_by_source=leads_by_source,
        avg_by_priority=avg_by_priority,
        conversion_rate=conversion_rate,
        time_period=time_period
    )


@analytics_bp.route('/commissions')
@login_required
@permission_required('analytics', 'view')
def commissions_analytics():
    """Commission analytics report"""
    time_period = request.args.get('period', '30')
    time_period = int(time_period)
    
    start_date = datetime.utcnow() - timedelta(days=time_period)
    
    # Commission statistics
    total_commission = db.session.query(func.sum(CommissionTracker.total_commission)).scalar() or 0
    period_commission = db.session.query(
        func.sum(CommissionTracker.total_commission)
    ).filter(CommissionTracker.created_at >= start_date).scalar() or 0
    
    # Commission by status
    commission_by_status = db.session.query(
        CommissionTracker.status,
        func.count(CommissionTracker.id).label('count'),
        func.sum(CommissionTracker.total_commission).label('amount')
    ).group_by(CommissionTracker.status).all()
    
    # Top commission earners
    top_earners = db.session.query(
        Employee.full_name,
        func.sum(CommissionTracker.employee_cut).label('total_cut')
    ).join(CommissionTracker).filter(
        CommissionTracker.created_at >= start_date
    ).group_by(Employee.id, Employee.full_name).order_by(
        func.sum(CommissionTracker.employee_cut).desc()
    ).limit(10).all()
    
    # Commission split analysis
    total_employee_cut = db.session.query(func.sum(CommissionTracker.employee_cut)).scalar() or 0
    total_admin_cut = db.session.query(func.sum(CommissionTracker.admin_cut)).scalar() or 0
    total_company_cut = db.session.query(func.sum(CommissionTracker.company_cut)).scalar() or 0
    
    return render_template(
        'analytics/commissions.html',
        total_commission=total_commission,
        period_commission=period_commission,
        commission_by_status=commission_by_status,
        top_earners=top_earners,
        total_employee_cut=total_employee_cut,
        total_admin_cut=total_admin_cut,
        total_company_cut=total_company_cut,
        time_period=time_period
    )


@analytics_bp.route('/employees')
@login_required
@permission_required('analytics', 'view')
def employees_analytics():
    """Employee performance analytics"""
    time_period = request.args.get('period', '30')
    time_period = int(time_period)
    
    start_date = datetime.utcnow() - timedelta(days=time_period)
    
    # Employee statistics
    total_employees = Employee.query.filter_by(status='active').count()
    
    # Employee performance metrics
    employee_performance = db.session.query(
        Employee.full_name,
        Employee.position,
        func.count(Lead.id).label('leads_count'),
        func.sum(Lead.loan_amount_applied).label('total_loan_amount'),
        func.sum(CommissionTracker.employee_cut).label('total_commission')
    ).outerjoin(Lead, Lead.created_by_id == Employee.id).outerjoin(
        CommissionTracker, CommissionTracker.employee_id == Employee.id
    ).filter(
        Employee.status == 'active',
        Lead.created_at >= start_date
    ).group_by(Employee.id, Employee.full_name, Employee.position).order_by(
        func.count(Lead.id).desc()
    ).all()
    
    # Department statistics
    dept_stats = db.session.query(
        Employee.department,
        func.count(Employee.id).label('emp_count'),
        func.sum(Lead.loan_amount_applied).label('total_amount')
    ).outerjoin(Lead, Lead.created_by_id == Employee.id).filter(
        Employee.status == 'active'
    ).group_by(Employee.department).all()
    
    return render_template(
        'analytics/employees.html',
        total_employees=total_employees,
        employee_performance=employee_performance,
        dept_stats=dept_stats,
        time_period=time_period
    )


@analytics_bp.route('/invoices')
@login_required
@permission_required('analytics', 'view')
def invoices_analytics():
    """Invoice analytics report"""
    time_period = request.args.get('period', '30')
    time_period = int(time_period)
    
    start_date = datetime.utcnow() - timedelta(days=time_period)
    
    # Invoice statistics
    total_invoices = Invoice.query.count()
    total_amount = db.session.query(func.sum(Invoice.amount)).scalar() or 0
    period_amount = db.session.query(
        func.sum(Invoice.amount)
    ).filter(Invoice.created_at >= start_date).scalar() or 0
    
    # Invoices by status
    invoices_by_status = db.session.query(
        Invoice.status,
        func.count(Invoice.id).label('count'),
        func.sum(Invoice.amount).label('amount')
    ).group_by(Invoice.status).all()
    
    # Monthly invoice trend
    monthly_invoices = db.session.query(
        func.date_trunc('month', Invoice.created_at).label('month'),
        func.sum(Invoice.amount).label('amount')
    ).group_by(func.date_trunc('month', Invoice.created_at)).order_by(
        func.date_trunc('month', Invoice.created_at)
    ).all()
    
    return render_template(
        'analytics/invoices.html',
        total_invoices=total_invoices,
        total_amount=total_amount,
        period_amount=period_amount,
        invoices_by_status=invoices_by_status,
        monthly_invoices=monthly_invoices,
        time_period=time_period
    )


@analytics_bp.route('/api/trends')
@login_required
@permission_required('analytics', 'view')
def api_trends():
    """API endpoint for trend data"""
    time_period = request.args.get('period', '30')
    time_period = int(time_period)
    
    start_date = datetime.utcnow() - timedelta(days=time_period)
    
    leads_trend = AnalyticsService.get_leads_trend(start_date)
    commission_trend = AnalyticsService.get_commission_trend(start_date)
    
    return jsonify({
        'leads_trend': leads_trend,
        'commission_trend': commission_trend
    })


@analytics_bp.route('/api/kpis')
@login_required
@permission_required('analytics', 'view')
def api_kpis():
    """API endpoint for KPI data"""
    time_period = request.args.get('period', '30')
    time_period = int(time_period)
    
    kpis = AnalyticsService.get_dashboard_kpis(time_period)
    
    return jsonify(kpis)


@analytics_bp.route('/api/top-employees')
@login_required
@permission_required('analytics', 'view')
def api_top_employees():
    """API endpoint for top employees"""
    limit = request.args.get('limit', 10, type=int)
    
    top_employees = AnalyticsService.get_top_employees(limit=limit)
    
    return jsonify(top_employees)


@analytics_bp.route('/api/leads-by-status')
@login_required
@permission_required('analytics', 'view')
def api_leads_by_status():
    """API endpoint for leads by status distribution"""
    leads_by_status = AnalyticsService.get_leads_by_status()
    
    return jsonify(leads_by_status)
