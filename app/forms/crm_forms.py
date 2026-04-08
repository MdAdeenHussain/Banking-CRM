"""CRM form definitions for lead/customer workflows."""

# =====================================
# SECTION: Imports
# =====================================
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional


# =====================================
# SECTION: Form Definitions
# =====================================
class LeadCreateForm(FlaskForm):
    """Lead creation form placeholder."""

    customer_name = StringField("Customer Name", validators=[DataRequired(), Length(max=150)])
    mobile = StringField("Mobile", validators=[DataRequired(), Length(max=20)])
    email = StringField("Email", validators=[Optional(), Length(max=255)])
    loan_type = StringField("Loan Type", validators=[Optional(), Length(max=80)])
    loan_amount = DecimalField("Loan Amount", validators=[Optional()], places=2)
    source = StringField("Source", validators=[Optional(), Length(max=80)])
    assigned_agent = StringField("Assigned Agent", validators=[Optional(), Length(max=120)])


class CustomerCreateForm(FlaskForm):
    """Customer creation form placeholder."""

    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=150)])
    mobile = StringField("Mobile", validators=[DataRequired(), Length(max=20)])
    email = StringField("Email", validators=[Optional(), Length(max=255)])
    occupation = StringField("Occupation", validators=[Optional(), Length(max=120)])
    monthly_income = DecimalField("Monthly Income", validators=[Optional()], places=2)
    existing_emis = DecimalField("Existing EMIs", validators=[Optional()], places=2)
    pan = StringField("PAN", validators=[Optional(), Length(max=20)])
    aadhaar = StringField("Aadhaar", validators=[Optional(), Length(max=20)])
    risk_score_placeholder = SelectField(
        "Risk Score Placeholder",
        choices=[("", "Select"), ("35", "Low"), ("60", "Medium"), ("80", "High")],
        validators=[Optional()],
    )
