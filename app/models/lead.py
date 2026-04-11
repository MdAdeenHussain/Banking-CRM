"""Lead Model"""
from app.extensions import db
from datetime import datetime
import uuid


class Lead(db.Model):
    """Lead Model"""
    __tablename__ = 'leads'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = db.Column(db.String(50), unique=True, nullable=False)
    customer_full_name = db.Column(db.String(150), nullable=False, index=True)
    mobile_number = db.Column(db.String(15), nullable=False, index=True)
    alternate_mobile = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(120), nullable=True, index=True)
    city = db.Column(db.String(100), nullable=False)
    occupation = db.Column(db.String(100), nullable=True)
    annual_income = db.Column(db.Float, nullable=True)
    cibil_score = db.Column(db.Integer, nullable=True)
    bank_financer = db.Column(db.String(100), nullable=False, index=True)
    loan_type = db.Column(db.String(50), nullable=False, index=True)  # personal, business, home, mortgage, LAP, credit_card, vehicle
    loan_amount_applied = db.Column(db.Float, nullable=False)
    lead_source = db.Column(db.String(100), nullable=True)  # referral, website, call, social_media
    remarks = db.Column(db.Text, nullable=True)
    priority_tag = db.Column(db.String(50), nullable=True)  # high, medium, low
    is_high_value = db.Column(db.Boolean, default=False)
    is_duplicate = db.Column(db.Boolean, default=False)
    duplicate_of_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('leads.id'), nullable=True)
    
    # Foreign Keys
    assigned_executive_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('employees.id'), nullable=True)
    created_by_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('employees.id'), nullable=False)
    current_status_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('lead_statuses.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    status_history = db.relationship('LeadStatus', backref='lead', lazy='dynamic')
    client_financial = db.relationship('ClientFinancial', backref='lead', uselist=False, cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='lead', lazy='dynamic', cascade='all, delete-orphan')
    bank_applications = db.relationship('BankApplication', backref='lead', lazy='dynamic', cascade='all, delete-orphan')
    commissions = db.relationship('CommissionTracker', backref='lead', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='lead', lazy='dynamic', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='lead', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_status_timeline(self):
        """Get lead status history"""
        return LeadStatus.query.filter_by(lead_id=self.id).order_by(LeadStatus.created_at).all()