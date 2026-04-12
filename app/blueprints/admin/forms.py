"""Banking DSA CRM — Admin Forms"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional


class BranchForm(FlaskForm):
    name = StringField("Branch Name", validators=[DataRequired()])
    city = StringField("City", validators=[Optional()])
    state = StringField("State", validators=[Optional()])
    address = TextAreaField("Address", validators=[Optional()])
    gstin = StringField("GSTIN", validators=[Optional()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Branch")


class SystemSettingsForm(FlaskForm):
    agency_name = StringField("Agency Name", validators=[DataRequired()])
    agency_gstin = StringField("Agency GSTIN", validators=[Optional()])
    agency_address = TextAreaField("Agency Address", validators=[Optional()])
    submit = SubmitField("Save Settings")
