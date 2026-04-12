"""LoanAxis CRM — Employee Forms"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, Length, Optional


class EmployeeForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=150)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    mobile = StringField("Mobile", validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    role = SelectField("Role", choices=[], validators=[DataRequired()])
    branch_id = SelectField("Branch", choices=[], validators=[Optional()])
    joining_date = DateField("Joining Date", validators=[Optional()])
    submit = SubmitField("Create Employee")
