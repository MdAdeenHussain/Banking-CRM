"""
LoanAxis CRM — PDF Generation Utilities

Renders HTML invoice templates to PDF using WeasyPrint.
Falls back gracefully if WeasyPrint dependencies are not installed.
"""

import os
from typing import Optional

from flask import render_template, current_app


def render_invoice_pdf(invoice, save_path: str = None) -> Optional[bytes]:
    """
    Render an invoice to PDF using WeasyPrint.

    Args:
        invoice: Invoice model instance
        save_path: Optional filesystem path to save the PDF

    Returns:
        PDF bytes, or None if WeasyPrint is not available
    """
    try:
        from weasyprint import HTML
    except ImportError:
        current_app.logger.warning(
            "WeasyPrint not installed. PDF generation unavailable. "
            "Install with: pip install WeasyPrint "
            "Also requires: brew install cairo pango gdk-pixbuf libffi"
        )
        return None

    # Render the HTML template
    html_content = render_template(
        "invoices/pdf_template.html",
        invoice=invoice,
        agency_name=current_app.config.get("AGENCY_NAME", ""),
        agency_gstin=current_app.config.get("AGENCY_GSTIN", ""),
        agency_address=current_app.config.get("AGENCY_ADDRESS", ""),
    )

    # Generate PDF
    pdf_bytes = HTML(string=html_content).write_pdf()

    # Optionally save to disk
    if save_path and pdf_bytes:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
