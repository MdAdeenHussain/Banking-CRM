"""
app/auth/services.py
Authentication business logic: user creation, password verification, token generation.
"""

from app.extensions import db, jwt
from app.auth.models import User, Role, UserRole, UserSession
from app.tenants.models import Tenant, Branch
from app.utils import hash_password, verify_password
from app.errors import AuthenticationError, ValidationError, NotFoundError, TenantError
from flask_jwt_extended import create_access_token
import os
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service: login, register, password management."""
    
    @staticmethod
    def authenticate_user(tenant_slug: str, email: str, password: str, ip_address: str = None):
        """
        Authenticate user by tenant slug, email, password.
        
        Returns:
            dict with 'user', 'access_token', 'refresh_token'
        
        Raises:
            TenantError if tenant not found
            AuthenticationError if credentials invalid
        """
        # Find tenant by slug
        tenant = Tenant.query.filter_by(slug=tenant_slug, is_active=True, is_deleted=False).first()
        if not tenant:
            logger.warning(f"Login attempt for non-existent tenant: {tenant_slug}")
            raise TenantError(f"Tenant '{tenant_slug}' not found")
        
        # Find user in this tenant
        user = User.query.filter_by(
            tenant_id=tenant.id,
            email=email,
            is_active=True,
            is_deleted=False
        ).first()
        
        if not user:
            logger.warning(f"Login attempt for non-existent user: {email} in tenant {tenant_slug}")
            raise AuthenticationError("Invalid email or password")
        
        # Check account locked
        if user.is_locked:
            if user.locked_until and user.locked_until > datetime.utcnow():
                raise AuthenticationError("Account temporarily locked. Try again later.")
            else:
                # Unlock account
                user.is_locked = False
                user.locked_until = None
                user.failed_login_attempts = 0
                db.session.commit()
        
        # Verify password
        if not verify_password(password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.is_locked = True
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.session.commit()
            
            logger.warning(f"Failed login for user {email} (attempt {user.failed_login_attempts})")
            raise AuthenticationError("Invalid email or password")
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        db.session.commit()
        
        logger.info(f"User authenticated: {email} in tenant {tenant_slug}")
        
        # Generate tokens
        access_token, refresh_token = TokenService.generate_tokens(
            user_id=user.id,
            tenant_id=tenant.id
        )
        
        return {
            "user": user.to_dict(),
            "tenant": tenant.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    @staticmethod
    def create_tenant_and_admin(
        tenant_name: str,
        tenant_slug: str,
        admin_email: str,
        admin_password: str,
        admin_first_name: str,
        admin_last_name: str,
        ip_address: str = None
    ):
        """
        Register new tenant with admin user.
        
        Flow:
        1. Create tenant
        2. Create default branch
        3. Create admin user
        4. Assign tenant_admin role
        
        Returns:
            dict with 'tenant', 'user', 'access_token', 'refresh_token'
        
        Raises:
            ValidationError if validation fails
        """
        # Check tenant not exists
        existing_tenant = Tenant.query.filter_by(slug=tenant_slug).first()
        if existing_tenant:
            raise ValidationError(f"Tenant '{tenant_slug}' already exists")
        
        # Check user not exists
        existing_user = User.query.filter_by(email=admin_email).first()
        if existing_user:
            raise ValidationError(f"Email '{admin_email}' already registered")
        
        try:
            # Create tenant
            tenant = Tenant(
                id=str(uuid4()),
                name=tenant_name,
                slug=tenant_slug.lower(),
                email=admin_email,
                status="ACTIVE",
                plan_type="STARTER"
            )
            db.session.add(tenant)
            db.session.flush()  # Get tenant.id without committing
            
            # Create default branch
            branch = Branch(
                id=str(uuid4()),
                tenant_id=tenant.id,
                name="Head Office",
                code="HO",
                city="Mumbai",
                phone=None,
                email=admin_email
            )
            db.session.add(branch)
            
            # Create admin user
            user = User(
                id=str(uuid4()),
                tenant_id=tenant.id,
                email=admin_email,
                password_hash=hash_password(admin_password),
                first_name=admin_first_name,
                last_name=admin_last_name,
                is_email_verified=True,  # Admin pre-verified
                email_verified_at=datetime.utcnow(),
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            # Get or create tenant_admin role
            role = Role.query.filter_by(name="tenant_admin").first()
            if not role:
                role = Role(id=str(uuid4()), name="tenant_admin")
                db.session.add(role)
                db.session.flush()
            
            # Assign role to user
            user_role = UserRole(
                id=str(uuid4()),
                user_id=user.id,
                role_id=role.id,
                tenant_id=tenant.id,
                is_active=True
            )
            db.session.add(user_role)
            
            db.session.commit()
            logger.info(f"Tenant registered: {tenant_slug} with admin {admin_email}")
            
            # Generate tokens
            access_token, refresh_token = TokenService.generate_tokens(
                user_id=user.id,
                tenant_id=tenant.id
            )
            
            return {
                "tenant": tenant.to_dict(),
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering tenant {tenant_slug}: {str(e)}")
            raise ValidationError(f"Tenant registration failed: {str(e)}")
    
    @staticmethod
    def create_user_in_tenant(
        tenant_id: UUID,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role_name: str,
        created_by_user_id: UUID = None
    ):
        """
        Create new user in tenant with specified role.
        Only tenant_admin can create users.
        
        Returns:
            dict with 'user', 'access_token', 'refresh_token'
        
        Raises:
            ValidationError if validation fails
        """
        # Check tenant exists
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            raise TenantError(f"Tenant {tenant_id} not found")
        
        # Check email not exists in tenant
        existing_user = User.query.filter_by(
            tenant_id=tenant_id,
            email=email
        ).first()
        if existing_user:
            raise ValidationError(f"Email '{email}' already exists in tenant")
        
        # Check role exists
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            raise ValidationError(f"Role '{role_name}' does not exist")
        
        try:
            # Create user
            user = User(
                id=str(uuid4()),
                tenant_id=tenant_id,
                email=email,
                password_hash=hash_password(password),
                first_name=first_name,
                last_name=last_name,
                created_by=created_by_user_id,
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            # Assign role
            user_role = UserRole(
                id=str(uuid4()),
                user_id=user.id,
                role_id=role.id,
                tenant_id=tenant_id,
                is_active=True
            )
            db.session.add(user_role)
            
            db.session.commit()
            logger.info(f"User created: {email} with role {role_name} in tenant {tenant_id}")
            
            # Generate tokens
            access_token, refresh_token = TokenService.generate_tokens(
                user_id=user.id,
                tenant_id=tenant_id
            )
            
            return {
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user {email}: {str(e)}")
            raise ValidationError(f"User creation failed: {str(e)}")
    
    @staticmethod
    def request_password_reset(tenant_id: UUID, email: str):
        """
        Request password reset token.
        
        Returns:
            dict with 'reset_token', 'expires_in'
        
        Raises:
            NotFoundError if user not found
        """
        user = User.query.filter_by(
            tenant_id=tenant_id,
            email=email,
            is_active=True,
            is_deleted=False
        ).first()
        
        if not user:
            # Don't reveal if user exists for security
            logger.warning(f"Password reset request for non-existent user: {email}")
            raise NotFoundError("User not found")
        
        # PHASE_2_HOOK: Send reset token email
        # For now, return token (in Phase 2, send via email)
        reset_token = TokenService.generate_reset_token(user_id=user.id, tenant_id=tenant_id)
        
        logger.info(f"Password reset token generated for user {email}")
        
        return {
            "reset_token": reset_token,
            "expires_in": "1h"
        }
    
    @staticmethod
    def reset_password(tenant_id: UUID, reset_token: str, new_password: str):
        """
        Reset password using token.
        
        Returns:
            dict with 'user', 'access_token', 'refresh_token'
        
        Raises:
            AuthenticationError if token invalid
        """
        payload = TokenService.verify_reset_token(reset_token)
        
        if not payload or payload.get("tenant_id") != str(tenant_id):
            raise AuthenticationError("Invalid or expired reset token")
        
        user = User.query.filter_by(
            id=payload.get("user_id"),
            tenant_id=tenant_id
        ).first()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Update password
        user.password_hash = hash_password(new_password)
        db.session.commit()
        
        logger.info(f"Password reset for user {user.email}")
        
        # Generate new tokens
        access_token, refresh_token = TokenService.generate_tokens(
            user_id=user.id,
            tenant_id=tenant_id
        )
        
        return {
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token
        }


class TokenService:
    """Token generation and verification."""
    
    @staticmethod
    def generate_tokens(user_id: UUID, tenant_id: UUID, additional_claims: dict = None):
        """
        Generate JWT access and refresh tokens.
        
        Access token: 15 minutes
        Refresh token: 7 days
        
        Returns:
            tuple of (access_token, refresh_token)
        """
        secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret")
        
        # Access token claims
        access_claims = {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "type": "access"
        }
        if additional_claims:
            access_claims.update(additional_claims)
        
        # Generate JWT access token
        access_token = create_access_token(
            identity=str(user_id),
            additional_claims=access_claims,
            expires_delta=timedelta(minutes=15)
        )
        
        # Refresh token claims
        refresh_claims = {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "type": "refresh"
        }
        
        refresh_token = create_access_token(
            identity=str(user_id),
            additional_claims=refresh_claims,
            expires_delta=timedelta(days=7)
        )
        
        return access_token, refresh_token
    
    @staticmethod
    def generate_reset_token(user_id: UUID, tenant_id: UUID):
        """
        Generate password reset token (1 hour expiry).
        """
        secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret")
        
        claims = {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "type": "reset"
        }
        
        token = create_access_token(
            identity=str(user_id),
            additional_claims=claims,
            expires_delta=timedelta(hours=1)
        )
        
        return token
    
    @staticmethod
    def verify_reset_token(token: str):
        """
        Verify password reset token.
        
        Returns:
            dict with payload if valid, None if invalid/expired
        """
        try:
            # Use Flask-JWT-Extended to decode
            from flask_jwt_extended import decode_token
            
            payload = decode_token(token)
            
            if payload.get("type") != "reset":
                return None
            
            return payload
        except Exception as e:
            logger.warning(f"Invalid password reset token: {str(e)}")
            return None
