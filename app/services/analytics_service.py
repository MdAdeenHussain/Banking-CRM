"""Analytics Service for reporting and KPIs"""
from app.models.lead import Lead
from app.models.employee import Employee
from app.models.commission_tracker import CommissionTracker
from app.models.invoice import Invoice
from app.models.task import Task
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func


class AnalyticsService:
    """Analytics and Reporting Service"""
    
    @staticmethod
    def get_dashboard_kpis(days=30):
        """Get dashboard KPIs"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Lead statistics
        total_leads = Lead.query.count()
        new_leads = Lead.query.filter(Lead.created_at >= start_date).count()
        approved_leads = Lead.query.filter_by(status='approved').count()
        
        # Commission statistics
        total_commission = db.session.query(func.sum(CommissionTracker.total_commission)).scalar() or 0
        period_commission = db.session.query(
            func.sum(CommissionTracker.total_commission)
        ).filter(CommissionTracker.created_at >= start_date).scalar() or 0
        
        # Invoice statistics
        total_invoices = Invoice.query.count()
        total_invoice_amount = db.session.query(func.sum(Invoice.amount)).scalar() or 0
        
        # Task statistics
        total_tasks = Task.query.count()
        completed_tasks = Task.query.filter_by(status='completed').count()
        pending_tasks = Task.query.filter(Task.status != 'completed').count()
        
        # Employee statistics
        total_employees = Employee.query.filter_by(status='active').count()
        
        # Conversion rate
        conversion_rate = (approved_leads / total_leads * 100) if total_leads > 0 else 0
        
        return {
            'total_leads': total_leads,
            'new_leads': new_leads,
            'approved_leads': approved_leads,
            'conversion_rate': round(conversion_rate, 2),
            'total_commission': float(total_commission),
            'period_commission': float(period_commission),
            'total_invoices': total_invoices,
            'total_invoice_amount': float(total_invoice_amount),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'total_employees': total_employees
        }
    
    @staticmethod
    def get_leads_trend(start_date):
        """Get leads trend data"""
        trend_data = []
        
        for i in range(30):
            date = start_date + timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0)
            date_end = date.replace(hour=23, minute=59, second=59)
            
            count = Lead.query.filter(
                Lead.created_at >= date_start,
                Lead.created_at <= date_end
            ).count()
            
            trend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        return trend_data
    
    @staticmethod
    def get_commission_trend(start_date):
        """Get commission trend data"""
        trend_data = []
        
        for i in range(30):
            date = start_date + timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0)
            date_end = date.replace(hour=23, minute=59, second=59)
            
            amount = db.session.query(
                func.sum(CommissionTracker.total_commission)
            ).filter(
                CommissionTracker.created_at >= date_start,
                CommissionTracker.created_at <= date_end
            ).scalar() or 0
            
            trend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'amount': float(amount)
            })
        
        return trend_data
    
    @staticmethod
    def get_leads_by_status():
        """Get leads grouped by status"""
        leads_by_status = db.session.query(
            Lead.status,
            func.count(Lead.id)
        ).group_by(Lead.status).all()
        
        return [{'status': status, 'count': count} for status, count in leads_by_status]
    
    @staticmethod
    def get_top_employees(limit=10):
        """Get top employees by commission"""
        top_employees = db.session.query(
            Employee.full_name,
            func.count(Lead.id).label('leads_count'),
            func.sum(CommissionTracker.employee_cut).label('total_earned'),
            func.avg(CommissionTracker.employee_cut).label('avg_commission')
        ).outerjoin(Lead, Lead.created_by_id == Employee.id).outerjoin(
            CommissionTracker, CommissionTracker.employee_id == Employee.id
        ).filter(Employee.status == 'active').group_by(
            Employee.id, Employee.full_name
        ).order_by(
            func.sum(CommissionTracker.employee_cut).desc()
        ).limit(limit).all()
        
        return [{
            'name': emp[0],
            'leads': emp[1] or 0,
            'total_earned': float(emp[2]) if emp[2] else 0,
            'avg_commission': float(emp[3]) if emp[3] else 0
        } for emp in top_employees]
    
    @staticmethod
    def get_monthly_analytics(year=None):
        """Get monthly analytics"""
        if not year:
            year = datetime.utcnow().year
        
        monthly_data = []
        
        for month in range(1, 13):
            month_start = datetime(year, month, 1)
            if month == 12:
                month_end = datetime(year + 1, 1, 1)
            else:
                month_end = datetime(year, month + 1, 1)
            
            leads = Lead.query.filter(
                Lead.created_at >= month_start,
                Lead.created_at < month_end
            ).count()
            
            commissions = db.session.query(
                func.sum(CommissionTracker.total_commission)
            ).filter(
                CommissionTracker.created_at >= month_start,
                CommissionTracker.created_at < month_end
            ).scalar() or 0
            
            monthly_data.append({
                'month': month_start.strftime('%B'),
                'leads': leads,
                'commissions': float(commissions)
            })
        
        return monthly_data
        
        return funnel_data