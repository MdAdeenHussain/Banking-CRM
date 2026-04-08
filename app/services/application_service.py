"""Application service layer."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.application import Application


# =====================================
# SECTION: Service Definition
# =====================================
class ApplicationService:
    """Application workflow operations."""

    @staticmethod
    def list_applications(tenant_id: int) -> list[Application]:
        """List tenant applications."""
        return (
            Application.query.filter_by(tenant_id=tenant_id, is_deleted=False)
            .order_by(Application.created_at.desc())
            .all()
        )

    @staticmethod
    def create_application(tenant_id: int, payload: dict) -> Application:
        """Create tenant application record."""
        application = Application(
            tenant_id=tenant_id,
            customer_id=payload["customer_id"],
            loan_type=payload.get("loan_type", "Unknown"),
            loan_amount=payload.get("loan_amount", 0),
            status=payload.get("status", "active"),
            current_stage=payload.get("current_stage", "INITIATED"),
        )
        db.session.add(application)
        db.session.commit()
        return application

    @staticmethod
    def update_stage(tenant_id: int, application_id: int, stage: str) -> bool:
        """Update application current stage by tenant scope."""
        application = Application.query.filter_by(
            id=application_id,
            tenant_id=tenant_id,
            is_deleted=False,
        ).first()
        if not application:
            return False

        application.current_stage = stage
        db.session.commit()
        return True

    # Future AI placeholder:
    # - automated underwriting recommendation endpoint
