"""
LoanAxis CRM — Document Routes
"""
import os
from flask import render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import login_required, current_user

from app.blueprints.documents import documents_bp
from app.blueprints.documents.forms import DocumentUploadForm
from app.blueprints.documents.services import handle_upload, get_document_by_token
from app.models.lead import Lead
from app.models.document import Document, DOCUMENT_TYPES
from app.utils.auth_helpers import check_lead_access


@documents_bp.route("/upload/<lead_id>", methods=["GET", "POST"])
@login_required
def upload(lead_id):
    """Upload a document for a lead."""
    lead = Lead.query.get_or_404(lead_id)
    if not check_lead_access(lead, "update"):
        abort(403)

    form = DocumentUploadForm()

    if form.validate_on_submit():
        try:
            doc = handle_upload(
                file=form.file.data,
                lead_id=lead_id,
                document_type=form.document_type.data,
                uploaded_by_id=current_user.id,
                custom_label=form.custom_label.data,
                expiry_date=form.expiry_date.data,
            )
            flash(f"Document '{doc.original_filename}' uploaded successfully!", "success")
            return redirect(url_for("leads.detail", lead_id=lead_id))
        except ValueError as e:
            flash(str(e), "danger")

    # Get existing documents for this lead
    documents = Document.query.filter_by(
        lead_id=lead_id, is_deleted=False
    ).order_by(Document.document_type, Document.version_number.desc()).all()

    return render_template(
        "documents/upload.html",
        form=form, lead=lead, documents=documents,
        document_types=DOCUMENT_TYPES,
    )


@documents_bp.route("/<token>/view")
@login_required
def view_document(token):
    """Serve a document securely via its access token."""
    doc = get_document_by_token(token)
    if not doc:
        abort(404)

    # Check access to parent lead
    lead = Lead.query.get(doc.lead_id)
    if lead and not check_lead_access(lead, "view"):
        abort(403)

    if not os.path.exists(doc.file_path):
        abort(404)

    return send_file(
        doc.file_path,
        mimetype=doc.mime_type,
        as_attachment=False,
        download_name=doc.original_filename,
    )


@documents_bp.route("/<token>/download")
@login_required
def download_document(token):
    """Download a document as attachment."""
    doc = get_document_by_token(token)
    if not doc:
        abort(404)

    lead = Lead.query.get(doc.lead_id)
    if lead and not check_lead_access(lead, "view"):
        abort(403)

    if not os.path.exists(doc.file_path):
        abort(404)

    return send_file(
        doc.file_path,
        mimetype=doc.mime_type,
        as_attachment=True,
        download_name=doc.original_filename,
    )


@documents_bp.route("/<doc_id>/verify", methods=["POST"])
@login_required
def verify_document(doc_id):
    """Mark a document as verified (Admin/Super Admin only)."""
    if current_user.role == "employee":
        abort(403)

    from datetime import datetime, timezone
    from app.extensions import db

    doc = Document.query.get_or_404(doc_id)
    doc.is_verified = True
    doc.verified_by = current_user.id
    doc.verification_date = datetime.now(timezone.utc)
    db.session.commit()

    flash(f"Document '{doc.original_filename}' verified.", "success")
    return redirect(url_for("leads.detail", lead_id=doc.lead_id))
