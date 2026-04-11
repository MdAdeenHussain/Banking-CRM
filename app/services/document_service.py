"""Document Service for document management"""
import os
from app.models.document import Document
from app.extensions import db
from datetime import datetime
from werkzeug.utils import secure_filename


class DocumentService:
    """Service for document management"""
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xlsx', 'xls', 'jpg', 'jpeg', 'png'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in DocumentService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_document(file, document_type, lead_id=None, uploaded_by_id=None):
        """Save uploaded document"""
        try:
            if not file or file.filename == '':
                return None, "No file provided"
            
            if not DocumentService.allowed_file(file.filename):
                return None, "File type not allowed"
            
            if file.content_length > DocumentService.MAX_FILE_SIZE:
                return None, "File size exceeds maximum"
            
            # Create uploads folder if doesn't exist
            os.makedirs(DocumentService.UPLOAD_FOLDER, exist_ok=True)
            
            # Save file
            filename = secure_filename(file.filename)
            import uuid
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(DocumentService.UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create document record
            document = Document(
                id=uuid.UUID(hex=unique_filename.split('_')[0]),
                document_id=f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                filename=filename,
                stored_filename=unique_filename,
                file_path=file_path,
                file_size=file_size,
                document_type=document_type,
                lead_id=lead_id,
                status='uploaded',
                uploaded_by_id=uploaded_by_id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(document)
            db.session.commit()
            
            return document, None
        
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def delete_document(document_id):
        """Delete document"""
        try:
            document = Document.query.get(document_id)
            if not document:
                return False, "Document not found"
            
            # Delete file from server
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete from database
            db.session.delete(document)
            db.session.commit()
            
            return True, None
        
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def verify_document(document_id, verified_by_id):
        """Verify document"""
        try:
            document = Document.query.get(document_id)
            if not document:
                return False, "Document not found"
            
            document.status = 'verified'
            document.verified_at = datetime.utcnow()
            document.verified_by_id = verified_by_id
            db.session.commit()
            
            return True, None
        
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_lead_documents(lead_id):
        """Get all documents for a lead"""
        return Document.query.filter_by(lead_id=lead_id).all()
