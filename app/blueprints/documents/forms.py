"""
LoanAxis CRM — Document Forms
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SelectField, StringField, SubmitField, DateField
from wtforms.validators import Optional

from app.models.document import DOCUMENT_TYPES


class DocumentUploadForm(FlaskForm):
    """Document upload form."""
    document_type = SelectField("Document Type",
                                choices=[(dt, dt) for dt in DOCUMENT_TYPES],
                                validators=[])
    custom_label = StringField("Custom Label (for 'Other' type)", validators=[Optional()])
    file = FileField("Select File", validators=[
        FileRequired(message="Please select a file"),
        FileAllowed(["pdf", "jpg", "jpeg", "png", "docx"],
                     message="Only PDF, JPG, PNG, DOCX files allowed"),
    ])
    expiry_date = DateField("Expiry Date (optional)", validators=[Optional()])
    submit = SubmitField("Upload")
