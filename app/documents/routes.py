"""Document Vault routes with dual HTML/JSON responses."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.documents.services import DocumentModuleService
from app.services.document_service import DocumentService


# ==========================================
# SECTION: Core Logic
# ==========================================
documents_bp = Blueprint("documents", __name__)


@documents_bp.get("/documents")
@login_required
def documents_list():
    """Document vault list endpoint (HTML + JSON)."""
    module_service = DocumentModuleService(
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
    )
    payload = module_service.list_documents_payload()

    if _wants_json():
        return jsonify({"status": "success", "data": payload}), 200

    return render_template("documents/documents_list.html", documents=payload)


@documents_bp.get("/documents/upload")
@login_required
def document_upload():
    """Render upload page for browser workflows."""
    return render_template("documents/document_upload.html")


@documents_bp.post("/documents/upload")
@login_required
def upload_document():
    """Upload a document and trigger OCR task."""
    service = DocumentService(tenant_id=current_user.tenant_id, actor_user_id=current_user.id)

    file = request.files.get("file")
    if file is None:
        return _error_response("File is required.", 400)

    json_payload = request.get_json(silent=True) or {}
    customer_id = request.form.get("customer_id") or json_payload.get("customer_id")
    doc_type = request.form.get("document_type") or json_payload.get("document_type")
    application_id = request.form.get("application_id") or json_payload.get("application_id")

    if not customer_id or not doc_type:
        return _error_response("customer_id and document_type are required.", 400)

    try:
        document = service.upload_document(
            file=file,
            customer_id=int(customer_id),
            doc_type=str(doc_type),
            application_id=int(application_id) if application_id else None,
        )
    except ValueError as exc:
        return _error_response(str(exc), 400)

    response_data = {
        "id": document.id,
        "customer_id": document.customer_id,
        "application_id": document.application_id,
        "document_type": document.document_type,
        "version": document.version,
        "ocr_status": document.ocr_status,
    }

    if _wants_json():
        return jsonify({"status": "success", "data": response_data}), 201

    flash("Document uploaded successfully.", "success")
    return redirect(url_for("documents.document_detail", document_id=document.id))


@documents_bp.get("/documents/<int:document_id>")
@login_required
def document_detail(document_id: int):
    """Document detail endpoint (HTML + JSON)."""
    service = DocumentService(tenant_id=current_user.tenant_id, actor_user_id=current_user.id)

    try:
        document = service.get_document_or_fail(document_id)
    except ValueError as exc:
        return _error_response(str(exc), 404)

    payload = {
        "id": document.id,
        "customer_id": document.customer_id,
        "application_id": document.application_id,
        "file_name": document.file_name,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "document_type": document.document_type,
        "version": document.version,
        "ocr_status": document.ocr_status,
        "ocr_data_json": document.ocr_data_json,
        "fraud_score": document.fraud_score,
        "fraud_flags_json": document.fraud_flags_json,
        "verification_status": document.verification_status,
    }

    if _wants_json():
        return jsonify({"status": "success", "data": payload}), 200

    return render_template("documents/document_detail.html", document=document, document_data=payload)


@documents_bp.post("/documents/<int:document_id>/ocr")
@login_required
def trigger_document_ocr(document_id: int):
    """Trigger OCR async processing for a document."""
    try:
        from app.documents.tasks import process_document_ocr

        process_document_ocr.delay(document_id)
    except Exception as exc:
        return _error_response(f"Unable to queue OCR task: {exc}", 500)

    if _wants_json():
        return jsonify({"status": "success", "message": "OCR task queued.", "document_id": document_id}), 202

    flash("OCR task queued successfully.", "success")
    return redirect(url_for("documents.document_detail", document_id=document_id))


@documents_bp.post("/documents/<int:document_id>/fraud-check")
@login_required
def trigger_document_fraud_check(document_id: int):
    """Run fraud checks synchronously and return score."""
    service = DocumentService(tenant_id=current_user.tenant_id, actor_user_id=current_user.id)

    try:
        document = service.run_fraud_check_for_document(document_id)
    except ValueError as exc:
        return _error_response(str(exc), 404)

    if _wants_json():
        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "document_id": document.id,
                        "fraud_score": document.fraud_score,
                        "fraud_flags_json": document.fraud_flags_json,
                    },
                }
            ),
            200,
        )

    flash("Fraud check completed.", "success")
    return redirect(url_for("documents.document_detail", document_id=document_id))


@documents_bp.post("/documents/<int:document_id>/verify")
@login_required
def verify_document(document_id: int):
    """Verify or reject a document based on payload action."""
    service = DocumentService(tenant_id=current_user.tenant_id, actor_user_id=current_user.id)

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    action = str(payload.get("action", "verify")).strip().lower()
    note = payload.get("note")

    try:
        if action == "reject":
            document = service.reject_document(document_id=document_id, note=note)
        else:
            document = service.verify_document(document_id=document_id, note=note)
    except ValueError as exc:
        return _error_response(str(exc), 404)

    if _wants_json():
        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "document_id": document.id,
                        "verification_status": document.verification_status,
                        "verified_by": document.verified_by,
                        "verified_at": document.verified_at.isoformat() if document.verified_at else None,
                    },
                }
            ),
            200,
        )

    flash(f"Document status updated to {document.verification_status}.", "success")
    return redirect(url_for("documents.document_detail", document_id=document_id))


@documents_bp.delete("/documents/<int:document_id>")
@login_required
def delete_document(document_id: int):
    """Soft-delete document record."""
    service = DocumentService(tenant_id=current_user.tenant_id, actor_user_id=current_user.id)

    try:
        service.delete_document(document_id)
    except ValueError as exc:
        return _error_response(str(exc), 404)

    if _wants_json():
        return jsonify({"status": "success", "message": "Document deleted."}), 200

    flash("Document deleted.", "success")
    return redirect(url_for("documents.documents_list"))


# ==========================================
# SECTION: Validation
# ==========================================
def _wants_json() -> bool:
    """Detect whether caller expects JSON response."""
    return request.is_json or request.args.get("format") == "json" or request.accept_mimetypes.best == "application/json"


def _error_response(message: str, status_code: int):
    """Return JSON error or HTML flash/redirect depending on client."""
    if _wants_json():
        return jsonify({"status": "error", "message": message}), status_code

    flash(message, "danger")
    return redirect(url_for("documents.documents_list"))


# ==========================================
# SECTION: Fraud Checks
# ==========================================
# Fraud check endpoint is /documents/<id>/fraud-check.
