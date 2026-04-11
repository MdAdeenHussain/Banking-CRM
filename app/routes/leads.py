from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.models.lead import Lead
from app.models.lead_status import LeadStatus
from app.models.employee import Employee
from app.models.user import User, db
from app.utils.decorators import login_required, permission_required
from datetime import datetime
import uuid

leads_bp = Blueprint('leads', __name__, url_prefix='/leads')

@leads_bp.route('/')
@login_required
def list_leads():
    """List all leads"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    bank_filter = request.args.get('bank', '')
    loan_type_filter = request.args.get('loan_type', '')
    
    query = Lead.query
    
    if search_query:
        query = query.filter(
            Lead.customer_full_name.ilike(f'%{search_query}%') |
            Lead.mobile_number.ilike(f'%{search_query}%') |
            Lead.email.ilike(f'%{search_query}%') |
            Lead.loan_account_number.ilike(f'%{search_query}%')
        )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if bank_filter:
        query = query.filter_by(bank_financer=bank_filter)
    
    if loan_type_filter:
        query = query.filter_by(loan_type=loan_type_filter)
    
    # Apply role-based filtering
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if user.role.name == 'EMPLOYEE':
        query = query.filter_by(assigned_executive_id=user.employee_id)
    
    leads = query.paginate(page=page, per_page=20)
    
    return render_template('leads/leads_list.html', leads=leads, search_query=search_query)

@leads_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('leads', 'create')
def create_lead():
    """Create new lead"""
    if request.method == 'GET':
        return render_template('leads/lead_create.html')
    
    # Create new lead
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # Get or create employee for user
    from app.models.employee import Employee
    employee = Employee.query.filter_by(email=user.email).first()
    if not employee:
        # Create employee record if doesn't exist
        employee = Employee(
            id=uuid.uuid4(),
            employee_id=f"EMP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            full_name=user.full_name,
            email=user.email,
            mobile=user.mobile,
            position='Loan Relationship Executive',
            hire_date=datetime.utcnow()
        )
        db.session.add(employee)
        db.session.flush()
    
    lead = Lead(
        id=uuid.uuid4(),
        lead_id=f"LD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        customer_full_name=request.form.get('customer_full_name'),
        mobile_number=request.form.get('mobile_number'),
        alternate_mobile=request.form.get('alternate_mobile'),
        email=request.form.get('email'),
        city=request.form.get('city'),
        occupation=request.form.get('occupation'),
        annual_income=float(request.form.get('annual_income', 0)) if request.form.get('annual_income') else None,
        cibil_score=int(request.form.get('cibil_score', 0)) if request.form.get('cibil_score') else None,
        bank_financer=request.form.get('bank_financer'),
        loan_type=request.form.get('loan_type'),
        loan_amount_applied=float(request.form.get('loan_amount_applied')),
        lead_source=request.form.get('lead_source'),
        remarks=request.form.get('remarks'),
        priority_tag=request.form.get('priority_tag'),
        created_by_id=employee.id
    )
    
    db.session.add(lead)
    db.session.commit()
    
    return redirect(url_for('leads.list_leads'))

@leads_bp.route('/<lead_id>')
@login_required
def detail_lead(lead_id):
    """Lead detail view"""
    lead = Lead.query.get(lead_id)
    if not lead:
        return render_template('404.html'), 404
    
    return render_template('leads/lead_detail.html', lead=lead)

@leads_bp.route('/<lead_id>/kanban')
@login_required
def kanban_view():
    """Kanban board view"""
    # Get all leads grouped by status
    statuses = LeadStatus.STATUS_CHOICES
    leads_by_status = {}
    
    for status in statuses:
        leads_by_status[status] = Lead.query.join(LeadStatus).filter(LeadStatus.status == status).all()
    
    return render_template('leads/lead_kanban.html', leads_by_status=leads_by_status)