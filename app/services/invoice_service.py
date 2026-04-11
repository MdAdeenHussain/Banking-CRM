"""Invoice Service for invoice generation and management"""
from app.models.invoice import Invoice
from app.models.lead import Lead
from app.extensions import db
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO
import uuid


class InvoiceService:
    """Invoice Generation and Management Service"""
    
    @staticmethod
    def generate_invoice(lead_id, amount, gst_rate=18.0, due_days=30, description=''):
        """Generate invoice"""
        try:
            lead = Lead.query.get(lead_id)
            if not lead:
                return None
            
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            gst_amount = (amount * gst_rate) / 100
            total_amount = amount + gst_amount
            
            due_date = datetime.utcnow() + timedelta(days=due_days)
            
            invoice = Invoice(
                id=uuid.uuid4(),
                invoice_number=invoice_number,
                lead_id=lead_id,
                amount=amount,
                gst_rate=gst_rate,
                gst_amount=gst_amount,
                total_amount=total_amount,
                description=description,
                status='draft',
                payment_status='pending',
                due_date=due_date,
                created_at=datetime.utcnow()
            )
            
            db.session.add(invoice)
            db.session.commit()
            
            return invoice
        
        except Exception as e:
            print(f"Invoice generation failed: {str(e)}")
            return None
    
    @staticmethod
    def mark_invoice_paid(invoice_id, payment_method=None, payment_date=None):
        """Mark invoice as paid"""
        try:
            invoice = Invoice.query.get(invoice_id)
            if not invoice:
                return None
            
            invoice.payment_status = 'paid'
            invoice.paid_date = payment_date or datetime.utcnow()
            invoice.payment_method = payment_method
            invoice.status = 'finalized'
            
            db.session.commit()
            
            return invoice
        
        except Exception as e:
            print(f"Invoice payment marking failed: {str(e)}")
            return None
    
    @staticmethod
    def generate_invoice_pdf(invoice):
        """Generate invoice as PDF"""
        try:
            # Create PDF document
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
            elements = []
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=1
            )
            
            # Add title
            title = Paragraph("INVOICE", title_style)
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            # Add invoice details
            lead = Lead.query.get(invoice.lead_id) if invoice.lead_id else None
            
            details_data = [
                ['Invoice Number:', invoice.invoice_number],
                ['Date:', invoice.created_at.strftime('%d-%m-%Y')],
                ['Due Date:', (invoice.due_date or invoice.created_at).strftime('%d-%m-%Y')],
                ['Status:', invoice.payment_status.upper()]
            ]
            
            details_table = Table(details_data, colWidths=[200, 200])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(details_table)
            elements.append(Spacer(1, 20))
            
            # Add bill to
            if lead:
                elements.append(Paragraph("BILL TO:", styles['Heading3']))
                elements.append(Paragraph(lead.customer_full_name, styles['Normal']))
                elements.append(Paragraph(f"Email: {lead.email}", styles['Normal']))
                elements.append(Paragraph(f"Mobile: {lead.mobile_number}", styles['Normal']))
                elements.append(Spacer(1, 20))
            
            # Add itemization
            itemData = [['Description', 'Amount']]
            itemData.append([invoice.description or 'Service', f"₹{invoice.amount:.2f}"])
            itemData.append(['GST (' + str(invoice.gst_rate) + '%)', f"₹{invoice.gst_amount:.2f}"])
            itemData.append(['TOTAL', f"₹{invoice.total_amount:.2f}"])
            
            itemTable = Table(itemData, colWidths=[300, 150])
            itemTable.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(itemTable)
            
            # Build PDF
            doc.build(elements)
            pdf_buffer.seek(0)
            
            return pdf_buffer.getvalue()
        
        except Exception as e:
            print(f"PDF generation failed: {str(e)}")
            return None
        return invoice