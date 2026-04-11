"""Commission Management Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.models.commission_tracker import CommissionTracker
from app.models.employee import Employee
from app.models.lead import Lead
from app.models.invoice import Invoice
from app.utils.decorators import login_required, role_required, permission_required
from app.services.audit_service import AuditService
from app.services.commission_service import CommissionService
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
import uuid
import csv
from io import StringIO

commissions_bp = Blueprint('commissions', __name__, url_prefix='/commissions')


@commissions_bp.route('/')
@login_required
@permission_required('commissions', 'view')
def list_commissions():
    """List all commissions with filters"""
    page = request.args.get('page', 1, type=int)
    employee_filter = request.args.get('employee', '')
    status_filter = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = CommissionTracker.query
    
    if employee_filter:
        query = query.filter_by(employee_id=employee_filter)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(CommissionTracker.created_at >= date_from_obj)
    
    if date_to:
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        query = query.filter(CommissionTracker.created_at <= date_to_obj)
    
    commissions = query.order_by(CommissionTracker.created_at.desc()).paginate(page=page, per_page=25)
    employees = Employee.query.filter_by(status='active').all()
    
    # Statistics
    total_commissions = db.session.query(func.sum(CommissionTracker.total_commission)).scalar() or 0
    pending_commissions = db.session.query(func.sum(CommissionTracker.total_commission)).filter(
        CommissionTracker.status == 'pending'
    ).scalar() or 0
    
    return render_template(
        'commissions/list.html',
        commissions=commissions.items,
        pagination=commissions,
        employees=employees,
        employee_filter=employee_filter,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        total_commissions=total_commissions,
        pending_commissions=pending_commissions
    )


@commissions_bp.route('/<commission_id>')
@login_required
@permission_required('commissions', 'view')
def commission_detail(commission_id):
    """View commission details"""
    commission = CommissionTracker.query.get(commission_id)
    if not commission:
        return render_template('error.html', code=404), 404
    
    lead = Lead.query.get(commission.lead_id) if commission.lead_id else None
    employee = Employee.query.get(commission.employee_id)
    
    return render_template(
        'commissions/detail.html',
        commission=commission,
        lead=lead,
        employee=employee
    )


@commissions_bp.route('/<commission_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def edit_commission(commission_id):
    """Edit commission status"""
    commission = CommissionTracker.query.get(commission_id)
    if not commission:
        return render_template('error.html', code=404), 404
    
    if request.method == 'GET':
        return render_template('commissions/edit.html', commission=commission)
    
    try:
        commission.status = request.form.get('status')
        commission.notes = request.form.get('notes')
        
        if request.form.get('status') == 'paid':
            commission.paid_date = datetime.utcnow()
            commission.paid_amount = commission.total_commission
        
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='UPDATE',
            resource='Commission',
            resource_id=str(commission.id),
            details=f"Updated commission status to: {request.form.get('status')}"
        )
        
        return redirect(url_for('commissions.commission_detail', commission_id=commission.id))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@commissions_bp.route('/calculate', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def calculate_commissions():
    """Calculate commissions for all leads"""
    try:
        leads = Lead.query.filter(
            Lead.status.in_(['approved', 'disbursed']),
            Lead.commission_calculated == False
        ).all()
        
        count = 0
        for lead in leads:
            commission = CommissionService.calculate_commission(lead)
            if commission:
                count += 1
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='CALCULATE',
            resource='Commission',
            resource_id='BATCH',
            details=f"Calculated commissions for {count} leads"
        )
        
        return jsonify({
            'success': True,
            'message': f'Calculated commissions for {count} leads'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@commissions_bp.route('/<commission_id>/approve', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def approve_commission(commission_id):
    """Approve commission for payment"""
    commission = CommissionTracker.query.get(commission_id)
    if not commission:
        return jsonify({'error': 'Commission not found'}), 404
    
    try:
        commission.status = 'approved'
        commission.approved_at = datetime.utcnow()
        commission.approved_by = session.get('user_id')
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='APPROVE',
            resource='Commission',
            resource_id=str(commission.id),
            details=f"Approved commission: {commission.total_commission}"
        )
        
        return jsonify({'success': True, 'message': 'Commission approved'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@commissions_bp.route('/mark-paid', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def mark_commissions_paid():
    """Mark selected commissions as paid"""
    try:
        commission_ids = request.json.get('commission_ids', [])
        paid_date = datetime.strptime(request.json.get('paid_date'), '%Y-%m-%d')
        
        commissions = CommissionTracker.query.filter(
            CommissionTracker.id.in_(commission_ids)
        ).all()
        
        for commission in commissions:
            commission.status = 'paid'
            commission.paid_date = paid_date
            commission.paid_amount = commission.total_commission
        
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='MARK_PAID',
            resource='Commission',
            resource_id='BATCH',
            details=f"Marked {len(commissions)} commissions as paid"
        )
        
        return jsonify({
            'success': True,
            'message': f'Marked {len(commissions)} commissions as paid'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@commissions_bp.route('/export')
@login_required
@permission_required('commissions', 'view')
def export_commissions():
    """Export commissions to CSV"""
    try:
        employee_filter = request.args.get('employee', '')
        status_filter = request.args.get('status', '')
        
        query = CommissionTracker.query
        
        if employee_filter:
            query = query.filter_by(employee_id=employee_filter)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        commissions = query.all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Commission ID',
            'Employee',
            'Lead Amount',
            'Commission %',
            'Total Commission',
            'Employee Cut',
            'Admin Cut',
            'Company Cut',
            'Status',
            'Created Date',
            'Paid Date'
        ])
        
        for commission in commissions:
            employee = Employee.query.get(commission.employee_id)
            writer.writerow([
                commission.commission_id,
                employee.full_name if employee else 'N/A',
                commission.lead_amount,
                commission.commission_percentage,
                commission.total_commission,
                commission.employee_cut,
                commission.admin_cut,
                commission.company_cut,
                commission.status,
                commission.created_at.strftime('%Y-%m-%d'),
                commission.paid_date.strftime('%Y-%m-%d') if commission.paid_date else 'N/A'
            ])
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='EXPORT',
            resource='Commission',
            resource_id='CSV',
            details=f"Exported {len(commissions)} commissions to CSV"
        )
        
        return output.getvalue(), 200, {
            'Content-Disposition': 'attachment; filename=commissions.csv',
            'Content-Type': 'text/csv'
        }
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@commissions_bp.route('/employee/<employee_id>')
@login_required
@permission_required('commissions', 'view')
def employee_commissions(employee_id):
    """View commissions for specific employee"""
    employee = Employee.query.get(employee_id)
    if not employee:
        return render_template('error.html', code=404), 404
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = CommissionTracker.query.filter_by(employee_id=employee_id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    commissions = query.order_by(CommissionTracker.created_at.desc()).paginate(page=page, per_page=25)
    
    # Statistics for this employee
    total_earned = db.session.query(func.sum(CommissionTracker.employee_cut)).filter(
        CommissionTracker.employee_id == employee_id
    ).scalar() or 0
    
    pending_amount = db.session.query(func.sum(CommissionTracker.employee_cut)).filter(
        CommissionTracker.employee_id == employee_id,
        CommissionTracker.status == 'pending'
    ).scalar() or 0
    
    return render_template(
        'commissions/employee_commissions.html',
        employee=employee,
        commissions=commissions.items,
        pagination=commissions,
        status_filter=status_filter,
        total_earned=total_earned,
        pending_amount=pending_amount
    )


@commissions_bp.route('/api/stats')
@login_required
@permission_required('commissions', 'view')
def api_commission_stats():
    """API endpoint for commission statistics"""
    stats = {
        'total_commissions': db.session.query(func.sum(CommissionTracker.total_commission)).scalar() or 0,
        'pending': db.session.query(func.count(CommissionTracker.id)).filter(
            CommissionTracker.status == 'pending'
        ).scalar() or 0,
        'approved': db.session.query(func.count(CommissionTracker.id)).filter(
            CommissionTracker.status == 'approved'
        ).scalar() or 0,
        'paid': db.session.query(func.count(CommissionTracker.id)).filter(
            CommissionTracker.status == 'paid'
        ).scalar() or 0
    }
    return jsonify(stats)
