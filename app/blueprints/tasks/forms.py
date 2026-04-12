"""LoanAxis CRM — Task Forms"""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, DateField, TimeField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional, Length
from app.models.task import TASK_TYPES, TASK_PRIORITIES


class TaskForm(FlaskForm):
    task_type = SelectField("Type", choices=[(t, t) for t in TASK_TYPES], validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired(), Length(max=300)])
    description = TextAreaField("Description", validators=[Optional()])
    lead_id = HiddenField("Lead ID")
    assigned_to = SelectField("Assign To", choices=[], validators=[DataRequired()])
    due_date = DateField("Due Date", validators=[DataRequired()])
    due_time = TimeField("Due Time", validators=[Optional()])
    priority = SelectField("Priority", choices=[(p, p) for p in TASK_PRIORITIES], default="Medium")
    submit = SubmitField("Create Task")
