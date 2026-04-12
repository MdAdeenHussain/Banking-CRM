"""Invoice Management Routes"""
from flask import Blueprint, render_template, request, jsonify, session, send_file, redirect, url_for
from app.models.invoice import Invoice
from app.models.lead import Lead
from app.models.commission_tracker import CommissionTracker
from app.extensions import db
from app.utils.decorators import login_required, role_required, permission_required
from app.services.invoice_service import InvoiceService
from app.services.audit_service import AuditService
from datetime import datetime
from io import BytesIO
from sqlalchemy import func
import uuid
import csv

invoices_bp = Blueprint('invoices', __name__, url_prefix='/invoices')


@invoices_bp.route('/')
@login_required
@permission_required('invoices', 'view')
def list_invoices():
    """List invoices with filters"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    payment_status_filter = request.args.get('payment_status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Invoice.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if payment_status_filter:
        query = query.filter_by(payment_status=payment_status_filter)
    
    if date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Invoice.created_at >= date_from_obj)
    
    if date_to:
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        query = query.filter(Invoice.created_at <= date_to_obj)
    
    invoices = query.order_by(Invoice.created_at.desc()).paginate(page=page, per_page=25)
    
    # Statistics
    total_invoices = Invoice.query.count()
    total_amount = db.session.query(func.sum(Invoice.amount)).scalar() or 0
    pending_amount = db.session.query(func.sum(Invoice.amount)).filter(
        Invoice.payment_status == 'pending'
    ).scalar() or 0
    
    return render_template(
        'invoices/list.html',
        invoices=invoices.items,
        pagination=invoices,
        status_filter=status_filter,
        payment_status_filter=payment_status_filter,
        date_from=date_from,
        date_to=date_to,
        total_invoices=total_invoices,
        total_amount=total_amount,
        pending_amount=pending_amount
    )


@invoices_bp.route('/<invoice_id>')
@login_required
@permission_required('invoices', 'view')
def invoice_detail(invoice_id):
    """View invoice details"""
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return render_template('error.html', code=404), 404
    
    lead = Lead.query.get(invoice.lead_id) if invoice.lead_id else None
    
    return render_template(
        'invoices/detail.html',
        invoice=invoice,
        lead=lead
    )


@invoices_bp.route('/<invoice_id>/download')
@login_required
@permission_required('invoices', 'view')
def download_invoice(invoice_id):
    """Download invoice as PDF"""
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    
    try:
        # Generate PDF
        pdf_data = InvoiceService.generate_invoice_pdf(invoice)
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='DOWNLOAD',
            resource='Invoice',
            resource_id=str(invoice.id),
            details=f"Downloaded invoice: {invoice.invoice_number}"
        )
        
        return send_file(
            BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{invoice.invoice_number}.pdf'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@invoices_bp.route('/<invoice_id>/mark-paid', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def mark_invoice_paid(invoice_id):
    """Mark invoice as paid"""
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    
    try:
        invoice.payment_status = 'paid'
        invoice.paid_date = datetime.utcnow()
        invoice.payment_method = request.form.get('payment_method', 'bank_transfer')
        invoice.payment_reference = request.form.get('payment_reference')
        
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='MARK_PAID',
            resource='Invoice',
            resource_id=str(invoice.id),
            details=f"Marked invoice as paid: {invoice.invoice_number}"
        )
        
        return redirect(url_for('invoices.invoice_detail', invoice_id=invoice_id))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@invoices_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def create_invoice():
    """Create new invoice"""
    if request.method == 'GET':
        leads = Lead.query.all()
        return render_template('invoices/create.html', leads=leads)
    
    try:
        invoice = Invoice(
            id=uuid.uuid4(),
            invoice_number=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            lead_id=request.form.get('lead_id'),
            amount=float(request.form.get('amount')),
            description=request.form.get('description'),
            gst_rate=float(request.form.get('gst_rate', 0)),
            status='draft',
            payment_status='pending',
            created_at=datetime.utcnow()
        )
        
        # Calculate GST
        gst_amount = (invoice.amount * invoice.gst_rate) / 100
        invoice.gst_amount = gst_amount
        invoice.total_amount = invoice.amount + gst_amount
        
        db.session.add(invoice)
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='CREATE',
            resource='Invoice',
            resource_id=str(invoice.id),
            details=f"Created invoice: {invoice.invoice_number}"
        )
        
        return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@invoices_bp.route('/<invoice_id>/send-email', methods=['POST'])
@login_required
@permission_required('invoices', 'edit')
def send_invoice_email(invoice_id):
    """Send invoice via email"""
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    
    try:
        from app.services.email_service import EmailService
        
        lead = Lead.query.get(invoice.lead_id) if invoice.lead_id else None
        if not lead or not lead.email:
            return jsonify({'error': 'Lead email not available'}), 400
        
        # Generate PDF
        pdf_data = InvoiceService.generate_invoice_pdf(invoice)
        
        # Send email
        EmailService.send_invoice_email(
            recipient=lead.email,
            invoice=invoice,
            pdf_attachment=pdf_data
        )
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='SEND_EMAIL',
            resource='Invoice',
            resource_id=str(invoice.id),
            details=f"Sent invoice email: {invoice.invoice_number}"
        )
        
        return jsonify({'success': True, 'message': 'Invoice sent via email'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@invoices_bp.route('/export-csv')
@login_required
@permission_required('invoices', 'view')
def export_invoices_csv():
    """Export invoices to CSV"""
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
        output = BytesIO()
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
        
        output.seek(0)
        
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
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@invoices_bp.route('/api/stats')
@login_required
@permission_required('invoices', 'view')
def api_invoice_stats():
    """API endpoint for invoice statistics"""
    stats = {
        'total_invoices': Invoice.query.count(),
        'paid': Invoice.query.filter_by(payment_status='paid').count(),
        'pending': Invoice.query.filter_by(payment_status='pending').count(),
        'total_amount': db.session.query(func.sum(Invoice.amount)).scalar() or 0,
        'pending_amount': db.session.query(func.sum(Invoice.amount)).filter(
            Invoice.payment_status == 'pending'
        ).scalar() or 0
    }
    return jsonify(stats)