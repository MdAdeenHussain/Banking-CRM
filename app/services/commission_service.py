"""Commission Service for calculating commissions"""
from app.models.commission_tracker import CommissionTracker
from app.models.lead import Lead
from app.models.employee import Employee
from app.extensions import db
from datetime import datetime
import uuid


class CommissionService:
    """Service for commission calculations and management"""
    
    # Commission split percentages
    EMPLOYEE_PERCENTAGE = 0.70  # 70% to employee
    ADMIN_PERCENTAGE = 0.15     # 15% to admin
    COMPANY_PERCENTAGE = 0.15   # 15% to company
    
    @staticmethod
    def calculate_commission(lead, commission_percentage=5):
        """Calculate commission for a lead"""
        try:
            if not lead.created_by_id or not lead.loan_amount_applied:
                return None
            
            employee = Employee.query.get(lead.created_by_id)
            if not employee:
                return None
            
            # Get employee's commission percentage
            emp_commission_percentage = employee.commission_percentage or commission_percentage
            
            # Calculate total commission
            total_commission = (lead.loan_amount_applied * emp_commission_percentage) / 100
            
            # Calculate splits
            employee_cut = total_commission * CommissionService.EMPLOYEE_PERCENTAGE
            admin_cut = total_commission * CommissionService.ADMIN_PERCENTAGE
            company_cut = total_commission * CommissionService.COMPANY_PERCENTAGE
            
            # Create commission record
            commission = CommissionTracker(
                id=uuid.uuid4(),
                commission_id=f"COM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                lead_id=lead.id,
                employee_id=lead.created_by_id,
                lead_amount=lead.loan_amount_applied,
                commission_percentage=emp_commission_percentage,
                total_commission=total_commission,
                employee_cut=employee_cut,
                admin_cut=admin_cut,
                company_cut=company_cut,
                status='pending',
                created_at=datetime.utcnow()
            )
            
            db.session.add(commission)
            lead.commission_calculated = True
            db.session.commit()
            
            return commission
        
        except Exception as e:
            print(f"Commission calculation failed: {str(e)}")
            return None
    
    @staticmethod
    def approve_commission(commission_id):
        """Approve a commission"""
        try:
            commission = CommissionTracker.query.get(commission_id)
            if not commission:
                return False
            
            commission.status = 'approved'
            commission.approved_at = datetime.utcnow()
            db.session.commit()
            
            return True
        
        except Exception as e:
            print(f"Commission approval failed: {str(e)}")
            return False
    
    @staticmethod
    def mark_commission_paid(commission_id, paid_amount=None):
        """Mark commission as paid"""
        try:
            commission = CommissionTracker.query.get(commission_id)
            if not commission:
                return False
            
            commission.status = 'paid'
            commission.paid_date = datetime.utcnow()
            commission.paid_amount = paid_amount or commission.gross_commission
            db.session.commit()
            
            return True
        
        except Exception as e:
            print(f"Commission payment marking failed: {str(e)}")
            return False
    
    @staticmethod
    def get_employee_commissions(employee_id, status=None):
        """Get all commissions for an employee"""
        query = CommissionTracker.query.filter_by(employee_id=employee_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.all()
    
    @staticmethod
    def get_total_commission_earned(employee_id):
        """Get total commission earned by employee"""
        commissions = CommissionService.get_employee_commissions(employee_id)
        return sum(c.employee_share for c in commissions if c.employee_share)
