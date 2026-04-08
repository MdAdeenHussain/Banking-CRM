"""
app/customers/services.py
Customer (KYC) management service.
"""

from app.extensions import db
from app.customers.models import Customer
from app.common.audit import AuditLogService
from app.errors import NotFoundError, ValidationError
from app.constants import AuditAction
from uuid import uuid4
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class CustomerService:
    """Customer KYC service."""
    
    @staticmethod
    def create_or_update_customer(
        tenant_id,
        name: str,
        mobile: str,
        email: str,
        pan: str = None,
        aadhaar: str = None,
        address: str = None,
        city: str = None,
        state: str = None,
        pincode: str = None,
        occupation: str = None,
        employer: str = None,
        employment_type: str = None,
        monthly_income: float = None,
        kyc_status: str = "PENDING",
        created_by_id: str = None
    ):
        """Create or update customer."""
        try:
            # Check if exists by PAN + Tenant
            customer = None
            if pan:
                customer = Customer.query.filter_by(
                    tenant_id=tenant_id,
                    pan=pan,
                    is_deleted=False
                ).first()
            
            if customer:
                # Update existing
                old_values = customer.to_dict()
                
                customer.name = name
                customer.mobile = mobile
                customer.email = email
                customer.address = address
                customer.city = city
                customer.state = state
                customer.pincode = pincode
                customer.occupation = occupation
                customer.employer = employer
                customer.employment_type = employment_type
                customer.monthly_income = monthly_income
                customer.kyc_status = kyc_status
                customer.updated_by = created_by_id
                
                db.session.commit()
                
                # Audit log
                AuditLogService.log_action(
                    tenant_id=tenant_id,
                    entity_type="Customer",
                    entity_id=str(customer.id),
                    action=AuditAction.UPDATE.value,
                    old_values=old_values,
                    new_values=customer.to_dict(),
                    user_id=created_by_id
                )
                
                logger.info(f"Customer updated: {customer.id}")
                
                return customer.to_dict()
            
            else:
                # Create new
                customer = Customer(
                    id=str(uuid4()),
                    tenant_id=tenant_id,
                    name=name,
                    mobile=mobile,
                    email=email,
                    pan=pan,
                    aadhaar=aadhaar,
                    address=address,
                    city=city,
                    state=state,
                    pincode=pincode,
                    occupation=occupation,
                    employer=employer,
                    employment_type=employment_type,
                    monthly_income=monthly_income,
                    kyc_status=kyc_status,
                    created_by=created_by_id,
                    is_active=True
                )
                
                db.session.add(customer)
                db.session.commit()
                
                # Audit log
                AuditLogService.log_action(
                    tenant_id=tenant_id,
                    entity_type="Customer",
                    entity_id=str(customer.id),
                    action=AuditAction.CREATE.value,
                    old_values=None,
                    new_values=customer.to_dict(),
                    user_id=created_by_id
                )
                
                logger.info(f"Customer created: {customer.id}")
                
                return customer.to_dict()
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating/updating customer: {str(e)}")
            raise ValidationError(f"Customer operation failed: {str(e)}")
    
    @staticmethod
    def get_customer(tenant_id, customer_id: str):
        """Get customer by ID."""
        from uuid import UUID
        customer = Customer.query.filter_by(
            id=customer_id,
            tenant_id=tenant_id,
            is_deleted=False
        ).first()
        
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        
        return customer.to_dict()
    
    @staticmethod
    def get_customers(tenant_id, filters: dict = None, skip: int = 0, limit: int = 20):
        """Get customers with filters."""
        query = Customer.query.filter_by(
            tenant_id=tenant_id,
            is_deleted=False
        )
        
        if filters:
            if filters.get("kyc_status"):
                query = query.filter_by(kyc_status=filters["kyc_status"])
            if filters.get("city"):
                query = query.filter_by(city=filters["city"])
            if filters.get("employment_type"):
                query = query.filter_by(employment_type=filters["employment_type"])
        
        total = query.count()
        customers = query.offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": [c.to_dict() for c in customers],
            "page": skip // limit + 1,
            "page_size": limit
        }
    
    @staticmethod
    def validate_pan(pan: str):
        """Validate PAN format (India)."""
        if not pan:
            return False
        
        pan_regex = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
        return bool(re.match(pan_regex, pan.upper()))
    
    @staticmethod
    def validate_aadhaar(aadhaar: str):
        """Validate Aadhaar format (India)."""
        if not aadhaar:
            return False
        
        aadhaar_regex = r"^[0-9]{12}$"
        return bool(re.match(aadhaar_regex, aadhaar))
    
    @staticmethod
    def update_kyc_status(
        tenant_id,
        customer_id: str,
        kyc_status: str,
        updated_by_id: str = None
    ):
        """Update customer KYC status."""
        from uuid import UUID
        customer = Customer.query.filter_by(
            id=customer_id,
            tenant_id=tenant_id
        ).first()
        
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        
        try:
            old_status = customer.kyc_status
            customer.kyc_status = kyc_status
            customer.kyc_verified_at = datetime.utcnow() if kyc_status == "VERIFIED" else customer.kyc_verified_at
            customer.updated_by = updated_by_id
            db.session.commit()
            
            # Audit log
            AuditLogService.log_action(
                tenant_id=tenant_id,
                entity_type="Customer",
                entity_id=str(customer.id),
                action=AuditAction.UPDATE.value,
                old_values={"kyc_status": old_status},
                new_values={"kyc_status": kyc_status},
                user_id=updated_by_id
            )
            
            logger.info(f"Customer KYC status updated: {customer_id} {old_status} -> {kyc_status}")
            
            return customer.to_dict()
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating KYC status: {str(e)}")
            raise ValidationError(f"KYC update failed: {str(e)}")
