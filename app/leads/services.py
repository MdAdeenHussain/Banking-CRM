"""
app/leads/services.py
Lead management service: CRUD, status changes, assignments, notes.
"""

from app.extensions import db
from app.leads.models import Lead, LeadNote, LeadAssignment, LeadStatusHistory
from app.auth.models import User
from app.customers.models import Customer
from app.common.audit import AuditLogService
from app.errors import NotFoundError, ValidationError, TenantError
from app.constants import LeadStatus, AuditAction
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LeadService:
    """Lead management service."""
    
    @staticmethod
    def create_lead(
        tenant_id,
        name: str,
        mobile: str,
        email: str,
        loan_type: str,
        loan_amount: float,
        source: str,
        city: str,
        priority: str = "MEDIUM",
        assigned_to_id: str = None,
        custom_data: dict = None,
        created_by_id: str = None
    ):
        """Create new lead."""
        try:
            lead = Lead(
                id=str(uuid4()),
                tenant_id=tenant_id,
                name=name,
                mobile=mobile,
                email=email,
                loan_type=loan_type,
                loan_amount=loan_amount,
                source=source,
                city=city,
                status=LeadStatus.NEW_LEAD.value,
                priority=priority,
                assigned_to=assigned_to_id,
                custom_data=custom_data or {},
                created_by=created_by_id,
                is_active=True
            )
            
            db.session.add(lead)
            
            # Log status history
            status_history = LeadStatusHistory(
                id=str(uuid4()),
                tenant_id=tenant_id,
                lead_id=lead.id,
                old_status=None,
                new_status=LeadStatus.NEW_LEAD.value,
                reason="Lead created",
                custom_data={"created": True}
            )
            db.session.add(status_history)
            
            db.session.commit()
            
            # Audit log
            AuditLogService.log_action(
                tenant_id=tenant_id,
                entity_type="Lead",
                entity_id=str(lead.id),
                action=AuditAction.CREATE.value,
                old_values=None,
                new_values=lead.to_dict(),
                user_id=created_by_id
            )
            
            logger.info(f"Lead created: {lead.id} in tenant {tenant_id}")
            
            return lead.to_dict()
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating lead: {str(e)}")
            raise ValidationError(f"Lead creation failed: {str(e)}")
    
    @staticmethod
    def update_lead(
        tenant_id,
        lead_id: str,
        name: str = None,
        email: str = None,
        loan_amount: float = None,
        city: str = None,
        priority: str = None,
        custom_data: dict = None,
        updated_by_id: str = None
    ):
        """Update lead."""
        from uuid import UUID
        lead = Lead.query.filter_by(
            id=lead_id,
            tenant_id=tenant_id,
            is_deleted=False
        ).first()
        
        if not lead:
            raise NotFoundError(f"Lead {lead_id} not found")
        
        try:
            old_values = lead.to_dict()
            
            if name:
                lead.name = name
            if email:
                lead.email = email
            if loan_amount is not None:
                lead.loan_amount = loan_amount
            if city:
                lead.city = city
            if priority:
                lead.priority = priority
            if custom_data:
                lead.custom_data = {**(lead.custom_data or {}), **custom_data}
            
            lead.updated_by = updated_by_id
            db.session.commit()
            
            # Audit log
            AuditLogService.log_action(
                tenant_id=tenant_id,
                entity_type="Lead",
                entity_id=str(lead.id),
                action=AuditAction.UPDATE.value,
                old_values=old_values,
                new_values=lead.to_dict(),
                user_id=updated_by_id
            )
            
            logger.info(f"Lead updated: {lead_id}")
            
            return lead.to_dict()
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating lead: {str(e)}")
            raise ValidationError(f"Lead update failed: {str(e)}")
    
    @staticmethod
    def change_lead_status(
        tenant_id,
        lead_id: str,
        new_status: str,
        reason: str = None,
        updated_by_id: str = None
    ):
        """Change lead status and create history record."""
        from uuid import UUID
        lead = Lead.query.filter_by(
            id=lead_id,
            tenant_id=tenant_id,
            is_deleted=False
        ).first()
        
        if not lead:
            raise NotFoundError(f"Lead {lead_id} not found")
        
        try:
            old_status = lead.status
            lead.status = new_status
            lead.updated_by = updated_by_id
            db.session.commit()
            
            # Create status history
            status_history = LeadStatusHistory(
                id=str(uuid4()),
                tenant_id=tenant_id,
                lead_id=lead.id,
                old_status=old_status,
                new_status=new_status,
                reason=reason or f"Status changed to {new_status}"
            )
            db.session.add(status_history)
            db.session.commit()
            
            # Audit log
            AuditLogService.log_action(
                tenant_id=tenant_id,
                entity_type="Lead",
                entity_id=str(lead.id),
                action=AuditAction.STATUS_CHANGE.value,
                old_values={"status": old_status},
                new_values={"status": new_status},
                reason=reason,
                user_id=updated_by_id
            )
            
            logger.info(f"Lead status changed: {lead_id} {old_status} -> {new_status}")
            
            return lead.to_dict()
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error changing lead status: {str(e)}")
            raise ValidationError(f"Status change failed: {str(e)}")
    
    @staticmethod
    def assign_lead(
        tenant_id,
        lead_id: str,
        user_id: str,
        assignment_type: str = "MANUAL",
        updated_by_id: str = None
    ):
        """Assign lead to user."""
        from uuid import UUID
        lead = Lead.query.filter_by(
            id=lead_id,
            tenant_id=tenant_id,
            is_deleted=False
        ).first()
        
        if not lead:
            raise NotFoundError(f"Lead {lead_id} not found")
        
        try:
            old_assigned_to = lead.assigned_to_id
            lead.assigned_to_id = user_id
            db.session.commit()
            
            # Create assignment record
            assignment = LeadAssignment(
                id=str(uuid4()),
                tenant_id=tenant_id,
                lead_id=lead.id,
                user_id=user_id,
                assignment_type=assignment_type,
                is_active=True
            )
            db.session.add(assignment)
            db.session.commit()
            
            # Audit log
            AuditLogService.log_action(
                tenant_id=tenant_id,
                entity_type="Lead",
                entity_id=str(lead.id),
                action=AuditAction.ASSIGN.value,
                old_values={"assigned_to_id": str(old_assigned_to) if old_assigned_to else None},
                new_values={"assigned_to_id": user_id},
                reason=f"Assigned to {user_id}",
                user_id=updated_by_id
            )
            
            logger.info(f"Lead assigned: {lead_id} to {user_id}")
            
            return lead.to_dict()
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning lead: {str(e)}")
            raise ValidationError(f"Assignment failed: {str(e)}")
    
    @staticmethod
    def add_lead_note(
        tenant_id,
        lead_id: str,
        note_text: str,
        note_type: str = "CALL_LOG",
        created_by_id: str = None
    ):
        """Add note to lead."""
        from uuid import UUID
        lead = Lead.query.filter_by(
            id=lead_id,
            tenant_id=tenant_id,
            is_deleted=False
        ).first()
        
        if not lead:
            raise NotFoundError(f"Lead {lead_id} not found")
        
        try:
            note = LeadNote(
                id=str(uuid4()),
                tenant_id=tenant_id,
                lead_id=lead.id,
                note_text=note_text,
                note_type=note_type,
                created_by=created_by_id
            )
            db.session.add(note)
            db.session.commit()
            
            logger.info(f"Note added to lead: {lead_id}")
            
            return note.to_dict()
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding note: {str(e)}")
            raise ValidationError(f"Note creation failed: {str(e)}")
    
    @staticmethod
    def get_leads(tenant_id, filters: dict = None, skip: int = 0, limit: int = 20):
        """Get leads with filters."""
        query = Lead.query.filter_by(
            tenant_id=tenant_id,
            is_deleted=False
        )
        
        if filters:
            if filters.get("status"):
                query = query.filter_by(status=filters["status"])
            if filters.get("assigned_to_id"):
                query = query.filter_by(assigned_to_id=filters["assigned_to_id"])
            if filters.get("source"):
                query = query.filter_by(source=filters["source"])
            if filters.get("city"):
                query = query.filter_by(city=filters["city"])
        
        total = query.count()
        leads = query.offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": [lead.to_dict() for lead in leads],
            "page": skip // limit + 1,
            "page_size": limit
        }
    
    @staticmethod
    def get_lead(tenant_id, lead_id: str):
        """Get single lead with notes and assignments."""
        from uuid import UUID
        lead = Lead.query.filter_by(
            id=lead_id,
            tenant_id=tenant_id,
            is_deleted=False
        ).first()
        
        if not lead:
            raise NotFoundError(f"Lead {lead_id} not found")
        
        result = lead.to_dict()
        
        # Add notes
        notes = LeadNote.query.filter_by(
            lead_id=lead.id,
            is_deleted=False
        ).all()
        result["notes"] = [note.to_dict() for note in notes]
        
        # Add assignments
        assignments = LeadAssignment.query.filter_by(
            lead_id=lead.id,
            is_active=True
        ).all()
        result["assignments"] = [assignment.to_dict() for assignment in assignments]
        
        return result
