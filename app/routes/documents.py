"""Document Management Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, send_file
from app.models.document import Document
from app.models.lead import Lead
from app.extensions import db
from app.utils.decorators import login_required, role_required, permission_required
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid
import os

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xlsx', 'xls', 'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@documents_bp.route('/')
@login_required
@permission_required('documents', 'view')
def list_documents():
    """List all documents with filters"""
    page = request.args.get('page', 1, type=int)
    doc_type_filter = request.args.get('doc_type', '')
    lead_filter = request.args.get('lead', '')
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Document.query
    
    if doc_type_filter:
        query = query.filter_by(document_type=doc_type_filter)
    
    if lead_filter:
        query = query.filter_by(lead_id=lead_filter)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if search:
        query = query.filter(Document.filename.ilike(f'%{search}%'))
    
    documents = query.order_by(Document.created_at.desc()).paginate(page=page, per_page=25)
    leads = Lead.query.filter_by(status='active').all()
    
    total_documents = Document.query.count()
    total_size = db.session.query(db.func.sum(Document.file_size)).scalar() or 0
    
    return render_template(
        'documents/list.html',
        documents=documents.items,
        pagination=documents,
        leads=leads,
        doc_type_filter=doc_type_filter,
        lead_filter=lead_filter,
        status_filter=status_filter,
        search=search,
        total_documents=total_documents,
        total_size=total_size
    )


@documents_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@permission_required('documents', 'create')
def upload_document():
    """Upload new document"""
    if request.method == 'GET':
        leads = Lead.query.filter_by(status='active').all()
        return render_template('documents/upload.html', leads=leads)
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Create uploads folder if doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create document record
        document = Document(
            id=uuid.uuid4(),
            document_id=f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            filename=filename,
            stored_filename=unique_filename,
            file_path=file_path,
            file_size=file_size,
            document_type=request.form.get('document_type'),
            lead_id=request.form.get('lead_id') if request.form.get('lead_id') else None,
            status='uploaded',
            uploaded_by_id=session.get('user_id'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(document)
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='UPLOAD',
            resource='Document',
            resource_id=str(document.id),
            details=f"Uploaded document: {filename}"
        )
        
        return redirect(url_for('documents.list_documents'))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@documents_bp.route('/<document_id>')
@login_required
@permission_required('documents', 'view')
def document_detail(document_id):
    """View document details"""
    document = Document.query.get(document_id)
    if not document:
        return render_template('error.html', code=404), 404
    
    lead = Lead.query.get(document.lead_id) if document.lead_id else None
    
    return render_template(
        'documents/detail.html',
        document=document,
        lead=lead
    )


@documents_bp.route('/<document_id>/download')
@login_required
@permission_required('documents', 'view')
def download_document(document_id):
    """Download document"""
    document = Document.query.get(document_id)
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    try:
        # Verify file exists
        if not os.path.exists(document.file_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='DOWNLOAD',
            resource='Document',
            resource_id=str(document.id),
            details=f"Downloaded document: {document.filename}"
        )
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@documents_bp.route('/<document_id>/delete', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def delete_document(document_id):
    """Delete document"""
    document = Document.query.get(document_id)
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    try:
        # Delete file from server
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete from database
        db.session.delete(document)
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='DELETE',
            resource='Document',
            resource_id=document_id,
            details=f"Deleted document: {document.filename}"
        )
        
        return jsonify({'success': True, 'message': 'Document deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@documents_bp.route('/<document_id>/verify', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def verify_document(document_id):
    """Verify document"""
    document = Document.query.get(document_id)
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    try:
        document.status = 'verified'
        document.verified_at = datetime.utcnow()
        document.verified_by_id = session.get('user_id')
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='VERIFY',
            resource='Document',
            resource_id=str(document.id),
            details=f"Verified document: {document.filename}"
        )
        
        return jsonify({'success': True, 'message': 'Document verified successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@documents_bp.route('/<document_id>/reject', methods=['POST'])
@login_required
@role_required(['SUPER_ADMIN', 'ADMIN'])
def reject_document(document_id):
    """Reject document"""
    document = Document.query.get(document_id)
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    try:
        document.status = 'rejected'
        document.rejection_reason = request.json.get('reason')
        db.session.commit()
        
        # Audit log
        user_id = session.get('user_id')
        AuditService.log_action(
            user_id=user_id,
            action='REJECT',
            resource='Document',
            resource_id=str(document.id),
            details=f"Rejected document: {document.filename}"
        )
        
        return jsonify({'success': True, 'message': 'Document rejected successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@documents_bp.route('/lead/<lead_id>')
@login_required
@permission_required('documents', 'view')
def lead_documents(lead_id):
    """View all documents for a lead"""
    lead = Lead.query.get(lead_id)
    if not lead:
        return render_template('error.html', code=404), 404
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Document.query.filter_by(lead_id=lead_id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    documents = query.order_by(Document.created_at.desc()).paginate(page=page, per_page=25)
    
    return render_template(
        'documents/lead_documents.html',
        lead=lead,
        documents=documents.items,
        pagination=documents,
        status_filter=status_filter
    )


@documents_bp.route('/api/stats')
@login_required
@permission_required('documents', 'view')
def api_document_stats():
    """API endpoint for document statistics"""
    stats = {
        'total_documents': Document.query.count(),
        'verified': Document.query.filter_by(status='verified').count(),
        'pending_verification': Document.query.filter_by(status='uploaded').count(),
        'rejected': Document.query.filter_by(status='rejected').count(),
        'total_size': db.session.query(db.func.sum(Document.file_size)).scalar() or 0
    }
    return jsonify(stats)
