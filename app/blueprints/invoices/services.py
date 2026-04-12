"""LoanAxis CRM — Invoice Services"""
from datetime import datetime, timezone
from app.extensions import db
from app.models.invoice import Invoice
from app.utils.number_utils import amount_in_words


def generate_invoice_number():
    """Generate auto-incrementing invoice number: INV-YYYY-XXXXX."""
    year = datetime.now().year
    last = Invoice.query.filter(Invoice.invoice_number.like(f"INV-{year}-%")).order_by(
        Invoice.created_at.desc()).first()
    if last:
        seq = int(last.invoice_number.split("-")[-1]) + 1
    else:
        seq = 1
    return f"INV-{year}-{seq:05d}"


def create_invoice(data, line_items, generated_by_id):
    """Create an invoice with line items and auto-computed totals."""
    invoice = Invoice(
        invoice_number=generate_invoice_number(),
        invoice_date=data["invoice_date"],
        due_date=data.get("due_date"),
        party_name=data["party_name"],
        party_address=data.get("party_address"),
        party_gstin=data.get("party_gstin"),
        line_items=line_items,
        cgst_rate=data.get("cgst_rate", 9.0),
        sgst_rate=data.get("sgst_rate", 9.0),
        igst_rate=data.get("igst_rate", 0.0),
        payment_status=data.get("payment_status", "Unpaid"),
        notes=data.get("notes"),
        generated_by=generated_by_id,
    )
    invoice.calculate_totals()
    invoice.amount_in_words = amount_in_words(invoice.total_amount)
    db.session.add(invoice)
    db.session.commit()
    return invoice
