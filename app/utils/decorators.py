"""Custom decorators for CRM"""

from functools import wraps
from flask import redirect, url_for, session, flash, abort, jsonify, request
from app.models.user import User
from app.utils.constants import ADMIN_ROLES


def login_required(f):
    """
    Decorator to require user to be logged in.
    Redirects to login page if not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session.get('user_id'))
        if not user or not user.is_active:
            session.clear()
            flash('User account is inactive or has been deleted.', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    Decorator to require admin role.
    Returns 403 Forbidden if user is not admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session.get('user_id'))
        if not user or user.role not in ADMIN_ROLES:
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def role_required(*allowed_roles):
    """
    Decorator to require specific role(s).
    
    Args:
        allowed_roles: Role or tuple of allowed roles
        
    Usage:
        @role_required('admin', 'manager')
        def protected_view():
            pass
    """
    if len(allowed_roles) == 1 and isinstance(allowed_roles[0], (list, tuple)):
        allowed_roles = allowed_roles[0]
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))
            
            user = User.query.get(session.get('user_id'))
            if not user or not user.role or user.role.name not in allowed_roles:
                abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def permission_required(module, action):
    """Check if user has permission for module+action"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return redirect(url_for('auth.login'))
            
            user = User.query.get(user_id)
            if not user or not user.role.has_permission(module, action):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def json_required(f):
    """
    Decorator to require JSON request content type.
    Returns 400 Bad Request if not JSON.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        return f(*args, **kwargs)
    
    return decorated_function


def api_auth_required(f):
    """
    Decorator to require API authentication via token.
    Returns 401 Unauthorized if token is missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authorization token required'}), 401
        
        user = User.query.filter_by(api_key=token, is_active=True).first()
        if not user:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def audit_log(action_type, resource_type):
    """
    Decorator to log user actions automatically.
    
    Args:
        action_type: Type of action (create, update, delete, view, etc.)
        resource_type: Type of resource being acted upon
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.models.activity_log import ActivityLog
            from app.extensions import db
            
            user_id = session.get('user_id')
            result = f(*args, **kwargs)
            
            try:
                activity = ActivityLog(
                    user_id=user_id,
                    action=action_type,
                    resource_type=resource_type,
                    status='success'
                )
                db.session.add(activity)
                db.session.commit()
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
            
            return result
        
        return decorated_function
    
    return decorator


def rate_limit(max_calls, window_seconds):
    """
    Decorator to rate limit function calls.
    
    Args:
        max_calls: Maximum number of calls allowed
        window_seconds: Time window in seconds
    """
    def decorator(f):
        calls = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from datetime import datetime, timedelta
            
            client_ip = request.remote_addr
            now = datetime.utcnow()
            
            if client_ip not in calls:
                calls[client_ip] = []
            
            calls[client_ip] = [
                call_time for call_time in calls[client_ip]
                if (now - call_time).total_seconds() < window_seconds
            ]
            
            if len(calls[client_ip]) >= max_calls:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            calls[client_ip].append(now)
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def cache_result(timeout_seconds=300):
    """
    Decorator to cache function results.
    
    Args:
        timeout_seconds: Cache timeout in seconds
    """
    def decorator(f):
        cache = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from datetime import datetime, timedelta
            
            key = str(args) + str(kwargs)
            
            if key in cache:
                result, timestamp = cache[key]
                if (datetime.utcnow() - timestamp).total_seconds() < timeout_seconds:
                    return result
            
            result = f(*args, **kwargs)
            cache[key] = (result, datetime.utcnow())
            return result
        
        return decorated_function
    
    return decorator