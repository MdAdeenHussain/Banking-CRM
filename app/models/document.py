"""Document model definition."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class Document(BaseModel):
    """Uploaded customer document metadata."""

    __tablename__ = "documents"

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id = db.Column(db.BigInteger, db.ForeignKey("customers.id"), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(1000), nullable=False)
    document_type = db.Column(db.String(80), nullable=False)
    ocr_status = db.Column(db.String(40), default="PENDING", nullable=False)
    fraud_status = db.Column(db.String(40), default="UNKNOWN", nullable=False)
    uploaded_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    # Future AI placeholders:
    # - ocr_extracted_json
    # - fraud_explanation_notes
