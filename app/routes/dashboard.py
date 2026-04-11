from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from app.models.user import User
from app.models.lead import Lead
from app.models.employee import Employee
from app.models.commission_tracker import CommissionTracker
from app.utils.decorators import login_required
from app.services.analytics_service import AnalyticsService
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
analytics = AnalyticsService()

@dashboard_bp.route('/')
@login_required
def index():
    """Main Dashboard"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        return redirect(url_for('auth.login'))
    
    # Get dashboard data based on role
    if user.role.name == 'SUPER_ADMIN':
        return render_template('dashboard/super_admin_dashboard.html', user=user, dashboard_data=analytics.get_super_admin_dashboard())
    elif user.role.name == 'ADMIN':
        return render_template('dashboard/admin_dashboard.html', user=user, dashboard_data=analytics.get_admin_dashboard())
    else:
        return render_template('dashboard/employee_dashboard.html', user=user, dashboard_data=analytics.get_employee_dashboard())

@dashboard_bp.route('/api/kpis')
@login_required
def get_kpis():
    """Get KPI data for AJAX"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    kpis = analytics.get_kpi_data(user)
    return jsonify(kpis)