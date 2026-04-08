"""Lead model definition for CRM lead lifecycle."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.base import BaseModel


# =====================================
# SECTION: Model Definition
# =====================================
class Lead(BaseModel):
    """Lead record with stage tracking."""

    __tablename__ = "leads"

    STAGE_NEW = "NEW"
    STAGE_CONTACTED = "CONTACTED"
    STAGE_INTERESTED = "INTERESTED"
    STAGE_DOCS_PENDING = "DOCS_PENDING"
    STAGE_SANCTIONED = "SANCTIONED"
    STAGE_DISBURSED = "DISBURSED"
    STAGE_LOST = "LOST"

    ALLOWED_STAGES = (
        STAGE_NEW,
        STAGE_CONTACTED,
        STAGE_INTERESTED,
        STAGE_DOCS_PENDING,
        STAGE_SANCTIONED,
        STAGE_DISBURSED,
        STAGE_LOST,
    )

    tenant_id = db.Column(db.BigInteger, db.ForeignKey("tenants.id"), nullable=False, index=True)
    customer_name = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    loan_type = db.Column(db.String(80), nullable=True)
    loan_amount = db.Column(db.Numeric(14, 2), nullable=True)
    stage = db.Column(db.String(40), default=STAGE_NEW, nullable=False)
    source = db.Column(db.String(80), nullable=True)
    assigned_agent = db.Column(db.String(120), nullable=True)
    ai_score_placeholder = db.Column(db.Float, nullable=True)

    # Future AI placeholders:
    # - lead_intent_vector
    # - conversion_probability_model_version
