"""
tests/test_auth_routes_and_services.py
Test authentication routes and services (Subphase 4-5).
"""

import pytest
from flask import g
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.auth.models import User, Role, UserRole
from app.auth.services import AuthService, TokenService
from app.leads.services import LeadService
from app.customers.services import CustomerService
from app.dashboard.services import DashboardService
from app.notifications.services import NotificationService
from app.utils import hash_password
from uuid import uuid4
import json


@pytest.fixture
def app():
    """Create test app."""
    app = create_app(config=TestingConfig)
    
    with app.app_context():
        db.create_all()  # Create all tables
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def tenant_admin_auth(app):
    """Fixture: Tenant with admin user ready for auth tests."""
    with app.app_context():
        result = AuthService.create_tenant_and_admin(
            tenant_name="Test Corp",
            tenant_slug="test-corp",
            admin_email="owner@testcorp.com",
            admin_password="SecurePass123!",
            admin_first_name="Test",
            admin_last_name="Owner"
        )
        
        return {
            "tenant_slug": "test-corp",
            "admin_email": "owner@testcorp.com",
            "admin_password": "SecurePass123!",
            "tenant_id": result["tenant"]["id"],
            "user_id": result["user"]["id"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"]
        }


class TestAuthRoutes:
    """Test authentication routes."""
    
    def test_login_get_form(self, client):
        """GET /auth/login should return form."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert "fields" in response.json
    
    def test_login_post_success(self, client, tenant_admin_auth):
        """POST /auth/login should authenticate and return tokens."""
        response = client.post("/auth/login", json={
            "tenant_slug": tenant_admin_auth["tenant_slug"],
            "email": tenant_admin_auth["admin_email"],
            "password": tenant_admin_auth["admin_password"]
        })
        
        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert "access_token" in response.json
        assert "refresh_token" in response.json
        assert response.json["user"]["email"] == tenant_admin_auth["admin_email"]
    
    def test_login_post_invalid_password(self, client, tenant_admin_auth):
        """POST /auth/login with wrong password should fail."""
        response = client.post("/auth/login", json={
            "tenant_slug": tenant_admin_auth["tenant_slug"],
            "email": tenant_admin_auth["admin_email"],
            "password": "WrongPassword123!"
        })
        
        assert response.status_code == 401
        assert "error" in response.json
    
    def test_login_post_nonexistent_tenant(self, client):
        """POST /auth/login to non-existent tenant should fail."""
        response = client.post("/auth/login", json={
            "tenant_slug": "nonexistent-tenant",
            "email": "test@example.com",
            "password": "Password123!"
        })
        
        assert response.status_code == 403
        assert "error" in response.json
    
    def test_register_tenant_get(self, client):
        """GET /auth/register/tenant should return form."""
        response = client.get("/auth/register/tenant")
        assert response.status_code == 200
        assert "fields" in response.json
    
    def test_register_tenant_post_success(self, client):
        """POST /auth/register/tenant should create new tenant."""
        response = client.post("/auth/register/tenant", json={
            "tenant_name": "New Bank Inc",
            "tenant_slug": "newbank-inc",
            "admin_email": "founder@newbank.com",
            "admin_password": "SecurePass123!",
            "admin_first_name": "John",
            "admin_last_name": "Founder"
        })
        
        assert response.status_code == 201
        assert response.json["status"] == "success"
        assert "access_token" in response.json
        assert response.json["tenant"]["name"] == "New Bank Inc"
    
    def test_register_tenant_post_duplicate_slug(self, client, tenant_admin_auth):
        """POST /auth/register/tenant with duplicate slug should fail."""
        response = client.post("/auth/register/tenant", json={
            "tenant_name": "Duplicate",
            "tenant_slug": tenant_admin_auth["tenant_slug"],
            "admin_email": "another@example.com",
            "admin_password": "SecurePass123!",
            "admin_first_name": "Another",
            "admin_last_name": "Admin"
        })
        
        assert response.status_code == 400
        assert "error" in response.json
    
    def test_register_tenant_post_weak_password(self, client):
        """POST /auth/register/tenant with weak password should fail."""
        response = client.post("/auth/register/tenant", json={
            "tenant_name": "Test Tenant",
            "tenant_slug": "test-weak",
            "admin_email": "test@example.com",
            "admin_password": "weak",
            "admin_first_name": "Test",
            "admin_last_name": "User"
        })
        
        assert response.status_code == 400
        assert "8 characters" in response.json["error"]
    
    def test_logout_authenticated(self, client, tenant_admin_auth):
        """POST /auth/logout should work when authenticated."""
        # First login
        login_response = client.post("/auth/login", json={
            "tenant_slug": tenant_admin_auth["tenant_slug"],
            "email": tenant_admin_auth["admin_email"],
            "password": tenant_admin_auth["admin_password"]
        })
        
        # Then logout (using Flask-Login session, not JWT)
        logout_response = client.post("/auth/logout")
        
        assert logout_response.status_code == 200
        assert logout_response.json["status"] == "success"
    
    def test_forgot_password_get(self, client):
        """GET /auth/forgot-password should return form."""
        response = client.get("/auth/forgot-password")
        assert response.status_code == 200
        assert "fields" in response.json
    
    def test_forgot_password_post(self, client, tenant_admin_auth):
        """POST /auth/forgot-password should generate reset token."""
        response = client.post("/auth/forgot-password", json={
            "tenant_slug": tenant_admin_auth["tenant_slug"],
            "email": tenant_admin_auth["admin_email"]
        })
        
        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert "reset_token" in response.json
    
    def test_reset_password_get_valid_token(self, client, tenant_admin_auth):
        """GET /auth/reset-password/<token> with valid token should work."""
        # Generate reset token
        from app.auth.services import TokenService
        reset_token = TokenService.generate_reset_token(
            user_id=tenant_admin_auth["user_id"],
            tenant_id=tenant_admin_auth["tenant_id"]
        )
        
        response = client.get(f"/auth/reset-password/{reset_token}")
        assert response.status_code == 200
        assert "fields" in response.json
    
    def test_reset_password_post_success(self, client, tenant_admin_auth):
        """POST /auth/reset-password/<token> should reset password."""
        from app.auth.services import TokenService
        reset_token = TokenService.generate_reset_token(
            user_id=tenant_admin_auth["user_id"],
            tenant_id=tenant_admin_auth["tenant_id"]
        )
        
        response = client.post(f"/auth/reset-password/{reset_token}", json={
            "password": "NewPassword123!",
            "password_confirm": "NewPassword123!"
        })
        
        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert "access_token" in response.json


class TestLeadService:
    """Test lead CRUD service."""
    
    def test_create_lead(self, app, tenant_admin_auth):
        """LeadService.create_lead should create lead."""
        with app.app_context():
            result = LeadService.create_lead(
                tenant_id=tenant_admin_auth["tenant_id"],
                name="John Doe",
                mobile="9876543210",
                email="john@example.com",
                loan_type="HOME_LOAN",
                loan_amount=500000,
                source="WEBSITE",
                city="Mumbai",
                created_by_id=tenant_admin_auth["user_id"]
            )
            
            assert result["name"] == "John Doe"
            assert result["status"] == "NEW_LEAD"
            assert result["mobile"] == "9876543210"
    
    def test_update_lead(self, app, tenant_admin_auth):
        """LeadService.update_lead should update lead."""
        with app.app_context():
            # Create lead
            lead = LeadService.create_lead(
                tenant_id=tenant_admin_auth["tenant_id"],
                name="John Doe",
                mobile="9876543210",
                email="john@example.com",
                loan_type="HOME_LOAN",
                loan_amount=500000,
                source="WEBSITE",
                city="Mumbai",
                created_by_id=tenant_admin_auth["user_id"]
            )
            
            # Update lead
            updated = LeadService.update_lead(
                tenant_id=tenant_admin_auth["tenant_id"],
                lead_id=lead["id"],
                name="John Smith",
                city="Delhi",
                updated_by_id=tenant_admin_auth["user_id"]
            )
            
            assert updated["name"] == "John Smith"
            assert updated["city"] == "Delhi"
    
    def test_change_lead_status(self, app, tenant_admin_auth):
        """LeadService.change_lead_status should update status."""
        with app.app_context():
            # Create lead
            lead = LeadService.create_lead(
                tenant_id=tenant_admin_auth["tenant_id"],
                name="John Doe",
                mobile="9876543210",
                email="john@example.com",
                loan_type="HOME_LOAN",
                loan_amount=500000,
                source="WEBSITE",
                city="Mumbai",
                created_by_id=tenant_admin_auth["user_id"]
            )
            
            # Change status
            updated = LeadService.change_lead_status(
                tenant_id=tenant_admin_auth["tenant_id"],
                lead_id=lead["id"],
                new_status="CONTACTED",
                reason="Called customer",
                updated_by_id=tenant_admin_auth["user_id"]
            )
            
            assert updated["status"] == "CONTACTED"


class TestCustomerService:
    """Test customer service."""
    
    def test_create_customer(self, app, tenant_admin_auth):
        """CustomerService.create_or_update_customer should create."""
        with app.app_context():
            result = CustomerService.create_or_update_customer(
                tenant_id=tenant_admin_auth["tenant_id"],
                name="Rajesh Sharma",
                mobile="9876543210",
                email="rajesh@example.com",
                pan="ABCDE1234F",
                city="Mumbai",
                state="Maharashtra",
                monthly_income=75000,
                created_by_id=tenant_admin_auth["user_id"]
            )
            
            assert result["name"] == "Rajesh Sharma"
            assert result["kyc_status"] == "PENDING"
    
    def test_validate_pan(self):
        """CustomerService.validate_pan should validate PAN."""
        assert CustomerService.validate_pan("ABCDE1234F") == True
        assert CustomerService.validate_pan("INVALID") == False
    
    def test_validate_aadhaar(self):
        """CustomerService.validate_aadhaar should validate Aadhaar."""
        assert CustomerService.validate_aadhaar("123456789012") == True
        assert CustomerService.validate_aadhaar("INVALID") == False


class TestDashboardService:
    """Test dashboard KPI service."""
    
    def test_get_owner_dashboard(self, app, tenant_admin_auth):
        """DashboardService.get_owner_dashboard should return KPIs."""
        with app.app_context():
            # Create some leads
            for i in range(3):
                LeadService.create_lead(
                    tenant_id=tenant_admin_auth["tenant_id"],
                    name=f"Lead {i}",
                    mobile=f"987654321{i}",
                    email=f"lead{i}@example.com",
                    loan_type="HOME_LOAN",
                    loan_amount=500000,
                    source="WEBSITE",
                    city="Mumbai",
                    created_by_id=tenant_admin_auth["user_id"]
                )
            
            result = DashboardService.get_owner_dashboard(
                tenant_id=tenant_admin_auth["tenant_id"]
            )
            
            assert result["dashboard_type"] == "owner"
            assert result["totals"]["leads"] == 3
            assert "status_breakdown" in result


class TestNotificationService:
    """Test notification service."""
    
    def test_create_notification(self, app, tenant_admin_auth):
        """NotificationService.create_notification should create."""
        with app.app_context():
            result = NotificationService.create_notification(
                user_id=tenant_admin_auth["user_id"],
                message="Test notification",
                notification_type="ASSIGNMENT",
                priority="HIGH"
            )
            
            assert result["message"] == "Test notification"
            assert result["is_read"] == False
    
    def test_mark_as_read(self, app, tenant_admin_auth):
        """NotificationService.mark_as_read should mark as read."""
        with app.app_context():
            # Create notification
            notif = NotificationService.create_notification(
                user_id=tenant_admin_auth["user_id"],
                message="Test notification"
            )
            
            # Mark as read
            updated = NotificationService.mark_as_read(notif["id"])
            
            assert updated["is_read"] == True
            assert updated["read_at"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
