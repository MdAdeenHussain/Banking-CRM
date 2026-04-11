from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from app.config import config
from app.models.user import db

migrate = Migrate()

def create_app(config_name='development'):
    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, supports_credentials=True)
    
    # Register Blueprints
    from app.routes import auth_bp, dashboard_bp, leads_bp, employees_bp, commissions_bp, tasks_bp, documents_bp, analytics_bp, invoices_bp, exports_bp, admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(commissions_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(admin_bp)
    
    # Context Processors - Make variables available in templates
    @app.context_processor
    def inject_user():
        """Inject current user into template context"""
        from flask import session
        from app.models.user import User
        user = None
        if 'user_id' in session:
            try:
                user = User.query.get(session.get('user_id'))
            except:
                user = None
        return dict(current_user=user)
    
    # Create Tables
    with app.app_context():
        db.create_all()
        _init_roles()
    
    return app

def _init_roles():
    """Initialize default roles"""
    from app.models.role import Role
    if Role.query.count() == 0:
        roles = [
            Role(name='SUPER_ADMIN', description='Super Administrator', permissions=Role.SUPER_ADMIN_PERMS),
            Role(name='ADMIN', description='Operations Manager', permissions=Role.ADMIN_PERMS),
            Role(name='EMPLOYEE', description='Loan Relationship Executive', permissions=Role.EMPLOYEE_PERMS)
        ]
        for role in roles:
            db.session.add(role)
        db.session.commit()