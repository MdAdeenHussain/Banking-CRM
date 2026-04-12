"""
LoanAxis CRM — Lead Forms
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, FloatField, IntegerField, SelectField,
    TextAreaField, BooleanField, SubmitField, HiddenField,
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, Email

from app.models.lead import LOAN_TYPES, LEAD_SOURCES, PRIORITY_TAGS, PIPELINE_STAGES
from app.models.remark import REMARK_TYPES, CALL_OUTCOMES


class LeadForm(FlaskForm):
    """Lead creation/edit form."""
    # Personal Info
    customer_name = StringField("Customer Name", validators=[DataRequired(), Length(max=200)])
    mobile_primary = StringField("Primary Mobile", validators=[DataRequired(), Length(min=10, max=15)])
    mobile_alternate = StringField("Alternate Mobile", validators=[Optional(), Length(max=15)])
    email = StringField("Email", validators=[Optional(), Email()])
    city = StringField("City", validators=[Optional(), Length(max=100)])
    state = StringField("State", validators=[Optional(), Length(max=100)])
    pincode = StringField("Pincode", validators=[Optional(), Length(max=10)])
    occupation = StringField("Occupation", validators=[Optional(), Length(max=100)])
    employer_name = StringField("Employer Name", validators=[Optional(), Length(max=200)])
    monthly_income = FloatField("Monthly Income (₹)", validators=[Optional()])
    annual_income = FloatField("Annual Income (₹)", validators=[Optional()])

    # CIBIL
    cibil_score = IntegerField("CIBIL Score", validators=[
        Optional(), NumberRange(min=300, max=900, message="CIBIL score must be 300-900")
    ])

    # Loan Details
    loan_type = SelectField("Loan Type", choices=[(lt, lt) for lt in LOAN_TYPES],
                            validators=[DataRequired()])
    loan_amount_applied = FloatField("Loan Amount Applied (₹)", validators=[Optional()])
    bank_preferred = StringField("Preferred Bank", validators=[Optional(), Length(max=150)])

    # Source & Priority
    lead_source = SelectField("Lead Source",
                              choices=[("", "Select Source")] + [(ls, ls) for ls in LEAD_SOURCES],
                              validators=[Optional()])
    priority_tag = SelectField("Priority",
                               choices=[(pt, pt) for pt in PRIORITY_TAGS],
                               default="Warm", validators=[Optional()])

    # Assignment
    assigned_executive_id = SelectField("Assigned Executive", choices=[], validators=[Optional()])
    branch_id = SelectField("Branch", choices=[], validators=[Optional()])

    # Duplicate override
    override_duplicate = BooleanField("Override duplicate warning")
    duplicate_reason = StringField("Duplicate override reason", validators=[Optional()])

    submit = SubmitField("Save Lead")


class StatusUpdateForm(FlaskForm):
    """Quick status update form."""
    pipeline_stage = SelectField("Status", choices=[(s, s) for s in PIPELINE_STAGES],
                                 validators=[DataRequired()])
    note = TextAreaField("Note", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Update Status")


class RemarkForm(FlaskForm):
    """Add remark/call note form."""
    remark_type = SelectField("Type", choices=[(rt, rt) for rt in REMARK_TYPES],
                              validators=[DataRequired()])
    content = TextAreaField("Remark", validators=[DataRequired(), Length(min=1, max=2000)])
    call_duration_min = IntegerField("Call Duration (min)", validators=[Optional()])
    call_outcome = SelectField("Call Outcome",
                               choices=[("", "Select")] + [(co, co) for co in CALL_OUTCOMES],
                               validators=[Optional()])
    submit = SubmitField("Add Remark")
