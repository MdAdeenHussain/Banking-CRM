"""Admin Management Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.models.user import User
from app.models.role import Role
from app.models.audit_log import AuditLog
from app.models.activity_log import ActivityLog
from app.utils.decorators import login_required, role_required, permission_required
from app.services.audit_service import AuditService
from app.extensions import db
from datetime import datetime
from sqlalchemy import func
import uuid

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users')
@login_required
@role_required(['SUPER_ADMIN'])
def manage_users():
    """Manage system users"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.mobile.ilike(f'%{search}%')
            )
        )
    
    if role_filter:
        query = query.filter_by(role_id=role_filter)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    users = query.paginate(page=page, per_page=25)
    roles = Role.query.all()
    
    total_users = User.query.count()
    active_users = User.query.filter_by(status='active').count()
    
    return render_template(
        'admin/users.html',
        users=users.items,
        pagination=users,
        roles=roles,
        total_users=total_users,
        active_users=active_users,
        search=search,
        role_filter=role_filter,
        status_filter=status_filter
    )


@admin_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['SUPER_ADMIN'])
def edit_user(user_id):
    """Edit user details and role"""
    user = User.query.get(user_id)
    if not user:
        return render_template('error.html', code=404), 404
    
    if request.method == 'GET':
        roles = Role.query.all()
        return render_template('admin/edit_user.html', user=user, roles=roles)
    
    try:
        # Update user
        user.full_name = request.form.get('full_name')
        user.mobile = request.form.get('mobile')
        user.role_id = request.form.get('role_id')
        user.status = request.form.get('status', 'active')
        
        db.session.commit()
        
        # Audit log
        current_user_id = session.get('user_id')
        AuditService.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource='User',
            resource_id=str(user.id),
            details=f"Updated user: {user.full_name}, New role: {user.role_id}"
        )
        
        return redirect(url_for('admin.manage_users'))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/users/<user_id>/disable', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN'])
def disable_user(user_id):
    """Disable user account"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        user.status = 'inactive'
        db.session.commit()
        
        # Audit log
        current_user_id = session.get('user_id')
        AuditService.log_action(
            user_id=current_user_id,
            action='DISABLE',
            resource='User',
            resource_id=str(user.id),
            details=f"Disabled user account: {user.email}"
        )
        
        return jsonify({'success': True, 'message': 'User disabled successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/users/<user_id>/reset-password', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN'])
def reset_user_password(user_id):
    """Admin reset user password"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        from app.services.auth_service import AuthService
        temp_password = AuthService.generate_password_reset_token()
        user.set_password(temp_password)
        user.password_reset_required = True
        db.session.commit()
        
        # Audit log
        current_user_id = session.get('user_id')
        AuditService.log_action(
            user_id=current_user_id,
            action='RESET_PASSWORD',
            resource='User',
            resource_id=str(user.id),
            details=f"Admin reset password for: {user.email}"
        )
        
        return jsonify({'success': True, 'message': 'Password reset successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/roles')
@login_required
@role_required(['SUPER_ADMIN'])
def manage_roles():
    """Manage system roles and permissions"""
    roles = Role.query.all()
    
    return render_template('admin/roles.html', roles=roles)


@admin_bp.route('/roles/<role_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['SUPER_ADMIN'])
def edit_role(role_id):
    """Edit role permissions"""
    role = Role.query.get(role_id)
    if not role:
        return render_template('error.html', code=404), 404
    
    if request.method == 'GET':
        return render_template('admin/edit_role.html', role=role)
    
    try:
        import json
        permissions = json.loads(request.form.get('permissions', '{}'))
        role.permissions = permissions
        db.session.commit()
        
        # Audit log
        current_user_id = session.get('user_id')
        AuditService.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource='Role',
            resource_id=str(role.id),
            details=f"Updated permissions for role: {role.name}"
        )
        
        return redirect(url_for('admin.manage_roles'))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/audit-logs')
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def view_audit_logs():
    """View system audit logs"""
    page = request.args.get('page', 1, type=int)
    resource_filter = request.args.get('resource', '')
    action_filter = request.args.get('action', '')
    user_filter = request.args.get('user', '')
    
    query = AuditLog.query
    
    if resource_filter:
        query = query.filter_by(resource=resource_filter)
    
    if action_filter:
        query = query.filter_by(action=action_filter)
    
    if user_filter:
        query = query.filter_by(performed_by_id=user_filter)
    
    logs = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50)
    
    # Get statistics
    total_logs = AuditLog.query.count()
    
    return render_template(
        'admin/audit_logs.html',
        logs=logs.items,
        pagination=logs,
        total_logs=total_logs,
        resource_filter=resource_filter,
        action_filter=action_filter,
        user_filter=user_filter
    )


@admin_bp.route('/activity-logs')
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def view_activity_logs():
    """View user activity logs"""
    page = request.args.get('page', 1, type=int)
    user_filter = request.args.get('user', '')
    activity_filter = request.args.get('activity', '')
    
    query = ActivityLog.query
    
    if user_filter:
        query = query.filter_by(user_id=user_filter)
    
    if activity_filter:
        query = query.filter_by(activity=activity_filter)
    
    logs = query.order_by(ActivityLog.created_at.desc()).paginate(page=page, per_page=50)
    
    return render_template(
        'admin/activity_logs.html',
        logs=logs.items,
        pagination=logs,
        user_filter=user_filter,
        activity_filter=activity_filter
    )


@admin_bp.route('/system-settings')
@login_required
@role_required(['SUPER_ADMIN'])
def system_settings():
    """System settings and configuration"""
    return render_template('admin/system_settings.html')


@admin_bp.route('/dashboard')
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def admin_dashboard():
    """Admin dashboard with statistics"""
    from app.models.employee import Employee
    from app.models.lead import Lead
    from app.models.commission_tracker import CommissionTracker
    from app.models.invoice import Invoice
    
    # User statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(status='active').count()
    new_users_this_month = User.query.filter(
        User.created_at >= datetime.utcnow().replace(day=1)
    ).count()
    
    # Employee statistics
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(status='active').count()
    
    # Lead statistics
    total_leads = Lead.query.count()
    leads_this_month = Lead.query.filter(
        Lead.created_at >= datetime.utcnow().replace(day=1)
    ).count()
    
    # Financial statistics
    total_commissions = db.session.query(func.sum(CommissionTracker.gross_commission)).scalar() or 0
    total_invoices = db.session.query(func.sum(Invoice.amount)).scalar() or 0
    
    # Recent audit logs
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        active_users=active_users,
        new_users_this_month=new_users_this_month,
        total_employees=total_employees,
        active_employees=active_employees,
        total_leads=total_leads,
        leads_this_month=leads_this_month,
        total_commissions=total_commissions,
        total_invoices=total_invoices,
        recent_logs=recent_logs
    )


@admin_bp.route('/api/stats')
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def api_stats():
    """API endpoint for admin statistics"""
    from app.models.employee import Employee
    from app.models.lead import Lead
    
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(status='active').count(),
        'total_employees': Employee.query.count(),
        'total_leads': Lead.query.count(),
        'recent_audit_logs': AuditLog.query.order_by(AuditLog.created_at.desc()).limit(5).count()
    }
    
    return jsonify(stats)
