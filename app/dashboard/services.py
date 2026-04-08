"""
app/dashboard/services.py
Dashboard KPI service: metrics for owner, branch manager, agent.
"""

from app.extensions import db
from app.leads.models import Lead, LeadStatusHistory
from app.auth.models import User, UserRole
from app.customers.models import Customer
from app.notifications.models import Notification
from app.constants import UserRole as UserRoleEnum, LeadStatus
from datetime import datetime, timedelta
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)


class DashboardService:
    """Dashboard KPI calculations."""
    
    @staticmethod
    def get_owner_dashboard(tenant_id):
        """Get platform/owner dashboard KPIs."""
        try:
            # Total metrics
            total_leads = Lead.query.filter_by(
                tenant_id=tenant_id,
                is_deleted=False
            ).count()
            
            total_customers = Customer.query.filter_by(
                tenant_id=tenant_id,
                is_deleted=False
            ).count()
            
            total_users = User.query.filter_by(
                tenant_id=tenant_id,
                is_active=True,
                is_deleted=False
            ).count()
            
            # Leads by status
            leads_by_status = db.session.query(
                Lead.status,
                func.count(Lead.id).label("count")
            ).filter_by(
                tenant_id=tenant_id,
                is_deleted=False
            ).group_by(Lead.status).all()
            
            status_breakdown = {status: count for status, count in leads_by_status}
            
            # Conversion metrics
            total_disbursed = Lead.query.filter_by(
                tenant_id=tenant_id,
                status=LeadStatus.DISBURSED.value,
                is_deleted=False
            ).count()
            
            conversion_rate = (total_disbursed / total_leads * 100) if total_leads > 0 else 0
            
            # Today's activity
            today = datetime.utcnow().date()
            leads_today = Lead.query.filter(
                Lead.tenant_id == tenant_id,
                Lead.created_at >= datetime.combine(today, datetime.min.time()),
                Lead.is_deleted == False
            ).count()
            
            # Pipeline value
            pipeline_value = db.session.query(
                func.sum(Lead.loan_amount)
            ).filter_by(
                tenant_id=tenant_id,
                is_deleted=False
            ).filter(
                Lead.status.in_([
                    LeadStatus.NEW_LEAD.value,
                    LeadStatus.CONTACTED.value,
                    LeadStatus.INTERESTED.value,
                    LeadStatus.DOCS_PENDING.value
                ])
            ).scalar() or 0
            
            return {
                "dashboard_type": "owner",
                "totals": {
                    "leads": total_leads,
                    "customers": total_customers,
                    "users": total_users,
                    "leads_today": leads_today
                },
                "status_breakdown": status_breakdown,
                "conversion": {
                    "rate_percent": round(conversion_rate, 2),
                    "total_disbursed": total_disbursed
                },
                "pipeline": {
                    "value": float(pipeline_value)
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating owner dashboard: {str(e)}")
            raise
    
    @staticmethod
    def get_branch_dashboard(tenant_id, branch_id):
        """Get branch manager dashboard KPIs."""
        try:
            from app.tenants.models import Branch
            
            # Verify branch
            branch = Branch.query.filter_by(
                id=branch_id,
                tenant_id=tenant_id,
                is_deleted=False
            ).first()
            
            if not branch:
                return {"error": "Branch not found"}
            
            # Get users in branch
            branch_users = User.query.filter_by(
                tenant_id=tenant_id,
                branch_id=branch_id,
                is_active=True,
                is_deleted=False
            ).all()
            
            user_ids = [u.id for u in branch_users]
            
            # Leads assigned to branch users
            total_leads = Lead.query.filter(
                Lead.tenant_id == tenant_id,
                Lead.assigned_to_id.in_(user_ids),
                Lead.is_deleted == False
            ).count() if user_ids else 0
            
            # Status breakdown
            leads_by_status = db.session.query(
                Lead.status,
                func.count(Lead.id).label("count")
            ).filter(
                Lead.tenant_id == tenant_id,
                Lead.assigned_to_id.in_(user_ids),
                Lead.is_deleted == False
            ).group_by(Lead.status).all() if user_ids else []
            
            status_breakdown = {status: count for status, count in leads_by_status}
            
            # Team metrics
            team_size = len(branch_users)
            
            return {
                "dashboard_type": "branch",
                "branch": branch.to_dict(),
                "team_size": team_size,
                "totals": {
                    "leads": total_leads
                },
                "status_breakdown": status_breakdown
            }
        
        except Exception as e:
            logger.error(f"Error generating branch dashboard: {str(e)}")
            raise
    
    @staticmethod
    def get_agent_dashboard(tenant_id, user_id):
        """Get agent dashboard KPIs."""
        try:
            from uuid import UUID
            
            # Agent's leads
            total_leads = Lead.query.filter_by(
                tenant_id=tenant_id,
                assigned_to=user_id,
                is_deleted=False
            ).count()
            
            # Status breakdown
            leads_by_status = db.session.query(
                Lead.status,
                func.count(Lead.id).label("count")
            ).filter_by(
                tenant_id=tenant_id,
                assigned_to=user_id,
                is_deleted=False
            ).group_by(Lead.status).all()
            
            status_breakdown = {status: count for status, count in leads_by_status}
            
            # Follow-ups pending
            today = datetime.utcnow().date()
            pending_followups = Lead.query.filter(
                Lead.tenant_id == tenant_id,
                Lead.assigned_to == user_id,
                Lead.next_follow_up != None,
                Lead.next_follow_up <= datetime.combine(today, datetime.max.time()),
                Lead.is_deleted == False
            ).count()
            
            # Recent activity
            today = datetime.utcnow().date()
            leads_today = Lead.query.filter(
                Lead.tenant_id == tenant_id,
                Lead.assigned_to == user_id,
                Lead.created_at >= datetime.combine(today, datetime.min.time()),
                Lead.is_deleted == False
            ).count()
            
            # Notifications
            notifications = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).count()
            
            return {
                "dashboard_type": "agent",
                "totals": {
                    "leads": total_leads,
                    "pending_followups": pending_followups,
                    "leads_today": leads_today,
                    "unread_notifications": notifications
                },
                "status_breakdown": status_breakdown
            }
        
        except Exception as e:
            logger.error(f"Error generating agent dashboard: {str(e)}")
            raise
    
    @staticmethod
    def get_platform_dashboard(tenant_id):
        """Get platform admin dashboard (same as owner)."""
        return DashboardService.get_owner_dashboard(tenant_id)
