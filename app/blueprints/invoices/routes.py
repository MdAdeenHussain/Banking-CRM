"""LoanAxis CRM — Invoice Routes"""
import json
from flask import render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app.blueprints.invoices import invoices_bp
from app.blueprints.invoices.forms import InvoiceForm
from app.blueprints.invoices.services import create_invoice
from app.models.invoice import Invoice
from app.utils.auth_helpers import require_permission


@invoices_bp.route("/")
@login_required
@require_permission("invoices.view")
def index():
    page = request.args.get("page", 1, type=int)
    pagination = Invoice.query.filter_by(is_deleted=False).order_by(
        Invoice.created_at.desc()).paginate(page=page, per_page=25)
    return render_template("invoices/index.html", invoices=pagination.items, pagination=pagination)


@invoices_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_permission("invoices.create")
def new():
    form = InvoiceForm()
    if form.validate_on_submit():
        line_items_json = request.form.get("line_items_json", "[]")
        try:
            line_items = json.loads(line_items_json)
        except json.JSONDecodeError:
            line_items = []
        invoice = create_invoice(
            data={f.name: f.data for f in form if f.name not in ("csrf_token", "submit")},
            line_items=line_items,
            generated_by_id=current_user.id,
        )
        flash(f"Invoice {invoice.invoice_number} generated!", "success")
        return redirect(url_for("invoices.detail", invoice_id=invoice.id))
    return render_template("invoices/new.html", form=form)


@invoices_bp.route("/<invoice_id>")
@login_required
@require_permission("invoices.view")
def detail(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template("invoices/detail.html", invoice=invoice)


@invoices_bp.route("/<invoice_id>/pdf")
@login_required
@require_permission("invoices.view")
def download_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    from app.utils.pdf_utils import render_invoice_pdf
    pdf_bytes = render_invoice_pdf(invoice)
    if not pdf_bytes:
        flash("PDF generation unavailable. Install WeasyPrint.", "warning")
        return redirect(url_for("invoices.detail", invoice_id=invoice_id))
    return Response(pdf_bytes, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={invoice.invoice_number}.pdf"})
