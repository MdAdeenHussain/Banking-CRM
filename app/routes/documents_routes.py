"""Document module route controllers."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, render_template
from flask_login import login_required


# =====================================
# SECTION: Blueprint Definition
# =====================================
documents_bp = Blueprint("documents", __name__)


# =====================================
# SECTION: Document Routes
# =====================================
@documents_bp.get("/documents")
@login_required
def documents_list():
    return render_template("documents/documents_list.html")


@documents_bp.get("/documents/upload")
@login_required
def document_upload():
    return render_template("documents/document_upload.html")


@documents_bp.get("/documents/<int:document_id>")
@login_required
def document_detail(document_id: int):
    return render_template("documents/document_detail.html", document_id=document_id)
