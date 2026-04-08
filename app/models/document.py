"""Document model definition."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Core Logic
# =====================================
class Document(BaseModel):
    """Uploaded customer document metadata + intelligence state."""

    __tablename__ = "documents"

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id = db.Column(db.BigInteger, db.ForeignKey("customers.id"), nullable=False, index=True)
    application_id = db.Column(db.BigInteger, db.ForeignKey("applications.id"), nullable=True, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(1000), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False, default=0)
    file_type = db.Column(db.String(120), nullable=False)
    document_type = db.Column(db.String(80), nullable=False)
    uploaded_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True, index=True)
    ocr_status = db.Column(db.String(40), default="PENDING", nullable=False)
    ocr_data_json = db.Column(db.JSON, nullable=True)
    fraud_score = db.Column(db.Integer, default=0, nullable=False)
    fraud_flags_json = db.Column(db.JSON, nullable=True)
    verification_status = db.Column(db.String(40), default="PENDING", nullable=False)
    verified_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True, index=True)
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    file_hash = db.Column(db.String(64), nullable=False, index=True)
    version = db.Column(db.Integer, default=1, nullable=False)
    uploaded_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    # =====================================
    # SECTION: Relationships
    # =====================================
    customer = db.relationship("Customer", back_populates="documents")
    application = db.relationship("Application", back_populates="documents")
    uploader = db.relationship("User", foreign_keys=[uploaded_by], lazy="joined")
    verifier = db.relationship("User", foreign_keys=[verified_by], lazy="joined")

    # =====================================
    # SECTION: Validation
    # =====================================
    # Validation for this model is handled in app.documents.validators and
    # app.services.document_service before persistence.

    # =====================================
    # SECTION: Fraud Checks
    # =====================================
    # Fraud signal fields:
    # - fraud_score
    # - fraud_flags_json

    # Future AI placeholders:
    # - ocr_extracted_json
    # - fraud_explanation_notes
