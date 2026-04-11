"""Employee Management Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.models.employee import Employee
from app.models.user import User
from app.models.lead import Lead
from app.models.commission_tracker import CommissionTracker
from app.models.audit_log import AuditLog
from app.utils.decorators import login_required, role_required, permission_required
from app.services.audit_service import AuditService
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
import uuid

employees_bp = Blueprint('employees', __name__, url_prefix='/employees')


@employees_bp.route('/')
@login_required
@permission_required('employees', 'view')
def list_employees():
    """List all employees with filter and pagination"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Employee.query
    
    if search:
        query = query.filter(
            db.or_(
                Employee.full_name.ilike(f'%{search}%'),
                Employee.email.ilike(f'%{search}%'),
                Employee.mobile.ilike(f'%{search}%'),
                Employee.employee_id.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    employees = query.paginate(page=page, per_page=20)
    
    # Get employee statistics
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(status='active').count()
    
    return render_template(
        'employees/list.html',
        employees=employees.items,
        total_pages=employees.pages,
        current_page=page,
        search=search,
        status_filter=status_filter,
        total_employees=total_employees,
        active_employees=active_employees,
        pagination=employees
    )


@employees_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def create_employee():
    """Create new employee"""
    if request.method == 'GET':
        return render_template('employees/create.html')
    
    try:
        # Check if employee already exists
        existing = Employee.query.filter_by(email=request.form.get('email')).first()
        if existing:
            return jsonify({'error': 'Employee with this email already exists'}), 400
        
        employee = Employee(
            id=uuid.uuid4(),
            employee_id=f"EMP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            full_name=request.form.get('full_name'),
            email=request.form.get('email'),
            mobile=request.form.get('mobile'),
            position=request.form.get('position'),
            department=request.form.get('department'),
            hire_date=datetime.strptime(request.form.get('hire_date'), '%Y-%m-%d').date(),
            salary=float(request.form.get('salary', 0)) if request.form.get('salary') else None,
            commission_percentage=float(request.form.get('commission_percentage', 5)),
            manager_id=request.form.get('manager_id') if request.form.get('manager_id') else None,
            status='active'
        )
        
        db.session.add(employee)
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='CREATE',
            resource='Employee',
            resource_id=str(employee.id),
            details=f"Created employee: {employee.full_name}"
        )
        
        return redirect(url_for('employees.list_employees'))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@employees_bp.route('/<employee_id>')
@login_required
@permission_required('employees', 'view')
def employee_detail(employee_id):
    """View employee details"""
    employee = Employee.query.get(employee_id)
    if not employee:
        return render_template('error.html', code=404), 404
    
    # Get employee statistics
    leads_count = Lead.query.filter_by(created_by_id=employee.id).count()
    commissions = CommissionTracker.query.filter_by(employee_id=employee.id).all()
    total_commission = sum(c.total_commission or 0 for c in commissions)
    
    # Calculate performance metrics
    leads_this_month = Lead.query.filter(
        Lead.created_by_id == employee.id,
        Lead.created_at >= datetime.utcnow().replace(day=1)
    ).count()
    
    return render_template(
        'employees/detail.html',
        employee=employee,
        leads_count=leads_count,
        commissions_count=len(commissions),
        total_commission=total_commission,
        leads_this_month=leads_this_month
    )


@employees_bp.route('/<employee_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def edit_employee(employee_id):
    """Edit employee details"""
    employee = Employee.query.get(employee_id)
    if not employee:
        return render_template('error.html', code=404), 404
    
    if request.method == 'GET':
        managers = Employee.query.filter(Employee.id != employee.id).all()
        return render_template('employees/edit.html', employee=employee, managers=managers)
    
    try:
        # Update employee fields
        employee.full_name = request.form.get('full_name')
        employee.position = request.form.get('position')
        employee.department = request.form.get('department')
        employee.salary = float(request.form.get('salary', 0)) if request.form.get('salary') else None
        employee.commission_percentage = float(request.form.get('commission_percentage', 5))
        employee.manager_id = request.form.get('manager_id') if request.form.get('manager_id') else None
        employee.status = request.form.get('status', 'active')
        
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='UPDATE',
            resource='Employee',
            resource_id=str(employee.id),
            details=f"Updated employee: {employee.full_name}"
        )
        
        return redirect(url_for('employees.employee_detail', employee_id=employee.id))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@employees_bp.route('/<employee_id>/delete', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def delete_employee(employee_id):
    """Delete employee (soft delete)"""
    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    try:
        # Soft delete
        employee.status = 'inactive'
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='DELETE',
            resource='Employee',
            resource_id=str(employee.id),
            details=f"Deleted employee: {employee.full_name}"
        )
        
        return jsonify({'success': True, 'message': 'Employee deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@employees_bp.route('/<employee_id>/performance')
@login_required
@permission_required('employees', 'view')
def employee_performance(employee_id):
    """View employee performance metrics"""
    employee = Employee.query.get(employee_id)
    if not employee:
        return render_template('error.html', code=404), 404
    
    # Get leads data
    leads_total = Lead.query.filter_by(created_by_id=employee.id).count()
    leads_this_month = Lead.query.filter(
        Lead.created_by_id == employee.id,
        Lead.created_at >= datetime.utcnow().replace(day=1)
    ).count()
    
    leads_this_quarter = Lead.query.filter(
        Lead.created_by_id == employee.id,
        Lead.created_at >= datetime.utcnow().replace(day=1, month=((datetime.utcnow().month - 1) // 3) * 3 + 1)
    ).count()
    
    # Get commission data
    commissions = CommissionTracker.query.filter_by(employee_id=employee.id).all()
    total_commission = sum(c.total_commission or 0 for c in commissions)
    commission_this_month = sum(
        c.total_commission or 0 for c in commissions 
        if c.created_at.month == datetime.utcnow().month and c.created_at.year == datetime.utcnow().year
    )
    
    # Get leads by status
    leads_by_status = db.session.query(
        Lead.status,
        func.count(Lead.id).label('count')
    ).filter(Lead.created_by_id == employee.id).group_by(Lead.status).all()
    
    return render_template(
        'employees/performance.html',
        employee=employee,
        leads_total=leads_total,
        leads_this_month=leads_this_month,
        leads_this_quarter=leads_this_quarter,
        total_commission=total_commission,
        commission_this_month=commission_this_month,
        leads_by_status=leads_by_status
    )


@employees_bp.route('/api/employees')
@login_required
@permission_required('employees', 'view')
def api_employees():
    """API endpoint for employee list (JSON)"""
    employees = Employee.query.filter_by(status='active').all()
    return jsonify([{
        'id': str(e.id),
        'full_name': e.full_name,
        'email': e.email,
        'position': e.position,
        'department': e.department
    } for e in employees])
