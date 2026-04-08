"""Customer service layer with tenant-safe behavior."""

# =====================================
# SECTION: Imports
# =====================================
from app.extensions import db
from app.models.customer import Customer


# =====================================
# SECTION: Service Definition
# =====================================
class CustomerService:
    """Customer domain operations."""

    @staticmethod
    def list_customers(tenant_id: int) -> list[Customer]:
        """Return customer list for tenant."""
        return (
            Customer.query.filter_by(tenant_id=tenant_id, is_deleted=False)
            .order_by(Customer.created_at.desc())
            .all()
        )

    @staticmethod
    def create_customer(tenant_id: int, payload: dict) -> Customer:
        """Create customer profile for tenant."""
        customer = Customer(
            tenant_id=tenant_id,
            full_name=payload.get("full_name", "Unknown"),
            mobile=payload.get("mobile", ""),
            email=payload.get("email"),
            pan=payload.get("pan"),
            aadhaar=payload.get("aadhaar"),
            occupation=payload.get("occupation"),
            monthly_income=payload.get("monthly_income"),
            existing_emis=payload.get("existing_emis"),
            risk_score_placeholder=payload.get("risk_score_placeholder"),
        )
        db.session.add(customer)
        db.session.commit()
        return customer

    @staticmethod
    def get_customer_profile(tenant_id: int, customer_id: int) -> Customer | None:
        """Get one customer by tenant scope."""
        return Customer.query.filter_by(
            id=customer_id,
            tenant_id=tenant_id,
            is_deleted=False,
        ).first()

    # Future AI placeholder:
    # - profile enrichment orchestrator
