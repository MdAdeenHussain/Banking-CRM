"""LoanAxis CRM — Commission Forms"""
from flask_wtf import FlaskForm
from wtforms import FloatField, SelectField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional
from app.models.commission import PAYOUT_STATUSES


class CommissionForm(FlaskForm):
    gross_commission = FloatField("Gross Commission (₹)", validators=[DataRequired()])
    tds_rate_pct = FloatField("TDS Rate (%)", default=5.0, validators=[Optional()])
    company_share_pct = FloatField("Company Share (%)", default=40.0, validators=[Optional()])
    admin_share_pct = FloatField("Admin Share (%)", default=20.0, validators=[Optional()])
    employee_share_pct = FloatField("Employee Share (%)", default=40.0, validators=[Optional()])
    payout_status = SelectField("Payout Status", choices=[(s, s) for s in PAYOUT_STATUSES])
    payment_reference = StringField("Payment Reference", validators=[Optional()])
    remarks = TextAreaField("Remarks", validators=[Optional()])
    submit = SubmitField("Save Commission")
