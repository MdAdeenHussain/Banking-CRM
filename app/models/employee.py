"""Employee Model"""
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy import DateTime
from sqlalchemy.sql import func
import uuid


class Employee(db.Model):
    """Employee Model"""
    __tablename__ = 'employees'
    
    id = db.Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    position = db.Column(db.String(100), nullable=False)  # Loan Relationship Executive, Operations Manager
    department = db.Column(db.String(100), nullable=True)
    reporting_manager_id = db.Column(PGUUID(as_uuid=True), db.ForeignKey('employees.id'), nullable=True)
    bank_partners = db.Column(JSONB, default=[])  # List of assigned banks
    total_leads = db.Column(db.Integer, default=0)
    converted_leads = db.Column(db.Integer, default=0)
    total_commission = db.Column(db.Float, default=0.0)
    pending_tasks = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    hire_date = db.Column(DateTime(timezone=True), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    
    # Relationships
    assigned_leads = db.relationship('Lead', backref='assigned_executive', lazy='dynamic', foreign_keys='Lead.assigned_executive_id')
    created_leads = db.relationship('Lead', backref='created_by_employee', lazy='dynamic', foreign_keys='Lead.created_by_id')
    
    def get_performance_metrics(self):
        """Get employee performance"""
        return {
            'total_leads': self.total_leads,
            'converted_leads': self.converted_leads,
            'conversion_rate': (self.converted_leads / self.total_leads * 100) if self.total_leads > 0 else 0,
            'total_commission': self.total_commission,
            'pending_tasks': self.pending_tasks
        }