"""Export and Reporting Routes"""
from flask import Blueprint, send_file, request, session, jsonify
from app.models.lead import Lead
from app.models.commission_tracker import CommissionTracker
from app.models.employee import Employee
from app.models.invoice import Invoice
from app.services.export_service import ExportService
from app.services.audit_service import AuditService
from app.utils.decorators import login_required, permission_required
from datetime import datetime
from io import BytesIO, StringIO
import csv

exports_bp = Blueprint('exports', __name__, url_prefix='/exports')


@exports_bp.route('/leads-csv')
@login_required
@permission_required('leads', 'view')
def export_leads_csv():
    """Export leads as CSV"""
    try:
        status_filter = request.args.get('status', '')
        bank_filter = request.args.get('bank', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Get filtered leads
        query = Lead.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if bank_filter:
            query = query.filter_by(bank_financer=bank_filter)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Lead.created_at >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Lead.created_at <= date_to_obj)
        
        leads = query.all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Lead ID',
            'Customer Name',
            'Mobile',
            'Email',
            'City',
            'Loan Amount',
            'Loan Type',
            'Bank',
            'Status',
            'Priority',
            'Created Date'
        ])
        
        for lead in leads:
            writer.writerow([
                lead.lead_id,
                lead.customer_full_name,
                lead.mobile_number,
                lead.email,
                lead.city,
                lead.loan_amount_applied,
                lead.loan_type,
                lead.bank_financer,
                lead.status,
                lead.priority_tag,
                lead.created_at.strftime('%Y-%m-%d')
            ])
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='EXPORT',
            resource='Lead',
            resource_id='CSV',
            details=f"Exported {len(leads)} leads to CSV"
        )
        
        return send_file(
            BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@exports_bp.route('/leads-excel')
@login_required
@permission_required('leads', 'view')
def export_leads_excel():
    """Export leads as Excel"""
    try:
        from openpyxl import Workbook
        
        status_filter = request.args.get('status', '')
        bank_filter = request.args.get('bank', '')
        
        query = Lead.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if bank_filter:
            query = query.filter_by(bank_financer=bank_filter)
        
        leads = query.all()
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Leads"
        
        # Write headers
        headers = ['Lead ID', 'Customer Name', 'Mobile', 'Email', 'City', 'Loan Amount', 
                   'Loan Type', 'Bank', 'Status', 'Priority', 'Created Date']
        ws.append(headers)
        
        # Write data
        for lead in leads:
            ws.append([
                lead.lead_id,
                lead.customer_full_name,
                lead.mobile_number,
                lead.email,
                lead.city,
                lead.loan_amount_applied,
                lead.loan_type,
                lead.bank_financer,
                lead.status,
                lead.priority_tag,
                lead.created_at.strftime('%Y-%m-%d')
            ])
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='EXPORT',
            resource='Lead',
            resource_id='EXCEL',
            details=f"Exported {len(leads)} leads to Excel"
        )
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    
    except ImportError:
        return jsonify({'error': 'openpyxl package not installed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@exports_bp.route('/commissions-csv')
@login_required
@permission_required('commissions', 'view')
def export_commissions_csv():
    """Export commissions as CSV"""
    try:
        status_filter = request.args.get('status', '')
        employee_filter = request.args.get('employee', '')
        
        query = CommissionTracker.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if employee_filter:
            query = query.filter_by(employee_id=employee_filter)
        
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
        
        return send_file(
            BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'commissions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@exports_bp.route('/invoices-csv')
@login_required
@permission_required('invoices', 'view')
def export_invoices_csv():
    """Export invoices as CSV"""
    try:
        status_filter = request.args.get('status', '')
        payment_status_filter = request.args.get('payment_status', '')
        
        query = Invoice.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if payment_status_filter:
            query = query.filter_by(payment_status=payment_status_filter)
        
        invoices = query.all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Invoice Number',
            'Lead',
            'Amount',
            'GST',
            'Total',
            'Status',
            'Payment Status',
            'Created Date',
            'Paid Date'
        ])
        
        for invoice in invoices:
            lead = Lead.query.get(invoice.lead_id) if invoice.lead_id else None
            writer.writerow([
                invoice.invoice_number,
                lead.customer_full_name if lead else 'N/A',
                invoice.amount,
                invoice.gst_amount,
                invoice.total_amount,
                invoice.status,
                invoice.payment_status,
                invoice.created_at.strftime('%Y-%m-%d'),
                invoice.paid_date.strftime('%Y-%m-%d') if invoice.paid_date else 'N/A'
            ])
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='EXPORT',
            resource='Invoice',
            resource_id='CSV',
            details=f"Exported {len(invoices)} invoices to CSV"
        )
        
        return send_file(
            BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@exports_bp.route('/employees-csv')
@login_required
@permission_required('employees', 'view')
def export_employees_csv():
    """Export employees as CSV"""
    try:
        department_filter = request.args.get('department', '')
        status_filter = request.args.get('status', '')
        
        query = Employee.query
        
        if department_filter:
            query = query.filter_by(department=department_filter)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        employees = query.all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Employee ID',
            'Full Name',
            'Email',
            'Mobile',
            'Position',
            'Department',
            'Commission %',
            'Status',
            'Hire Date'
        ])
        
        for employee in employees:
            writer.writerow([
                employee.employee_id,
                employee.full_name,
                employee.email,
                employee.mobile,
                employee.position,
                employee.department,
                employee.commission_percentage,
                employee.status,
                employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else 'N/A'
            ])
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='EXPORT',
            resource='Employee',
            resource_id='CSV',
            details=f"Exported {len(employees)} employees to CSV"
        )
        
        return send_file(
            BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    
    return send_file(
        BytesIO(csv_data.encode()),
        mimetype='text/csv',
        attachment_filename=f'commissions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@exports_bp.route('/employee-report/<employee_id>')
@login_required
def export_employee_report(employee_id):
    """Export employee report as Excel"""
    excel_data = ExportService.export_employee_report(employee_id)
    
    if not excel_data:
        return 'Employee not found', 404
    
    return send_file(
        BytesIO(excel_data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        attachment_filename=f'employee_report_{employee_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )