from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app.models.user import User, db
from app.models.role import Role
from app.models.otp import OTP
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.utils.decorators import login_required, role_required, permission_required
from datetime import datetime, timedelta
import uuid

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_service = AuthService()
email_service = EmailService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User Login"""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Validate inputs
    if not email or not password:
        return render_template('auth/login.html', error='Email and password required'), 400
    
    # Find user
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return render_template('auth/login.html', error='Invalid email or password'), 401
    
    if not user.is_active:
        return render_template('auth/login.html', error='Account is inactive'), 403
    
    # Check if 2FA is enabled
    if user.is_2fa_enabled:
        # Send OTP
        otp_code = auth_service.generate_otp()
        email_service.send_otp(user.email, otp_code)
        session['temp_user_id'] = str(user.id)
        session['otp_sent_time'] = datetime.utcnow().isoformat()
        return redirect(url_for('auth.verify_otp'))
    
    # Create session
    session['user_id'] = str(user.id)
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Log audit
    from app.services.audit_service import AuditService
    audit = AuditService()
    audit.log_action(user.id, 'LOGIN', 'auth', None, None, request.remote_addr, request.user_agent.string)
    
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration"""
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    # Validate inputs
    email = request.form.get('email')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    mobile = request.form.get('mobile')
    
    if User.query.filter_by(email=email).first():
        return render_template('auth/register.html', error='Email already registered'), 409
    
    # Create new user (default role: EMPLOYEE)
    from app.models.role import Role
    employee_role = Role.query.filter_by(name='EMPLOYEE').first()
    
    user = User(
        id=uuid.uuid4(),
        email=email,
        full_name=full_name,
        mobile=mobile,
        role_id=employee_role.id
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = str(user.id)
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify OTP for 2FA"""
    if request.method == 'GET':
        return render_template('auth/verify_otp.html')
    
    otp_code = request.form.get('otp')
    temp_user_id = session.get('temp_user_id')
    
    if not temp_user_id:
        return render_template('auth/verify_otp.html', error='Session expired'), 400
    
    user = User.query.get(temp_user_id)
    
    # Verify OTP
    if auth_service.verify_otp(user.email, otp_code):
        session['user_id'] = str(user.id)
        session.pop('temp_user_id')
        user.last_login = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/verify_otp.html', error='Invalid OTP'), 400

@auth_bp.route('/logout')
@login_required
def logout():
    """User Logout"""
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password Recovery"""
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    
    if user:
        # Generate reset token
        reset_token = auth_service.generate_reset_token(user.id)
        email_service.send_password_reset(user.email, reset_token)
        return render_template('auth/forgot_password.html', message='Reset link sent to email'), 200
    
    return render_template('auth/forgot_password.html', error='Email not found'), 404

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset Password with Token"""
    if request.method == 'GET':
        return render_template('auth/reset_password.html')
    
    user_id = auth_service.verify_reset_token(token)
    if not user_id:
        return render_template('auth/reset_password.html', error='Invalid or expired token'), 400
    
    user = User.query.get(user_id)
    new_password = request.form.get('password')
    user.set_password(new_password)
    db.session.commit()
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/2fa-setup', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Setup 2FA"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        user.is_2fa_enabled = True
        db.session.commit()
        return redirect(url_for('dashboard.settings'))
    
    return render_template('auth/2fa_setup.html')