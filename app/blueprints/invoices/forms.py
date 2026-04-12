"""LoanAxis CRM — Invoice Forms"""
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional
from app.models.invoice import PAYMENT_STATUSES


class InvoiceForm(FlaskForm):
    party_name = StringField("Party Name", validators=[DataRequired()])
    party_address = TextAreaField("Party Address", validators=[Optional()])
    party_gstin = StringField("Party GSTIN", validators=[Optional()])
    invoice_date = DateField("Invoice Date", validators=[DataRequired()])
    due_date = DateField("Due Date", validators=[Optional()])
    cgst_rate = FloatField("CGST %", default=9.0, validators=[Optional()])
    sgst_rate = FloatField("SGST %", default=9.0, validators=[Optional()])
    igst_rate = FloatField("IGST %", default=0.0, validators=[Optional()])
    payment_status = SelectField("Payment Status", choices=[(s, s) for s in PAYMENT_STATUSES])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Generate Invoice")
