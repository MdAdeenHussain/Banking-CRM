"""
tests/test_tenant_injection.py
Test tenant isolation and request context injection.

NOTE: Full integration tests with database (create_user_in_tenant, etc.)
require PostgreSQL. These tests focus on middleware behavior and can run
with in-memory database, while full ORM tests are deferred to integration tests.
"""

import pytest
from flask import g
from app import create_app
from app.extensions import db
from uuid import uuid4


@pytest.fixture
def app():
    """Create app with test config."""
    from app.config import TestingConfig
    
    app = create_app(config=TestingConfig)
    
    with app.app_context():
        # Note: db.create_all() skipped due to UUID type incompatibility with SQLite
        # Full database schema tests require PostgreSQL
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


class TestTenantInjectionMiddleware:
    """Test tenant injection middleware - context-only (no ORM)."""
    
    def test_health_check_no_tenant(self, client):
        """Health check should work without tenant."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json["status"] == "healthy"
    
    def test_request_context_initialized(self, app):
        """Request context should be initialized by before_request hook."""
        with app.test_request_context():
            from app.middleware import inject_tenant
            inject_tenant()
            
            assert g.tenant_id is None
            assert g.user_id is None
            assert g.user_roles == []
            assert hasattr(g, "request_ip")
            assert hasattr(g, "user_agent")
    
    def test_request_with_x_tenant_id_header(self, app):
        """X-Tenant-ID header should set g.tenant_id for testing."""
        test_tenant_id = uuid4()
        
        with app.test_request_context(
            "/health",
            headers={"X-Tenant-ID": str(test_tenant_id)}
        ):
            from app.middleware import inject_tenant
            inject_tenant()
            
            assert g.tenant_id == test_tenant_id
    
    def test_request_with_invalid_x_tenant_id_header(self, app):
        """Invalid X-Tenant-ID header should not crash."""
        with app.test_request_context(
            "/health",
            headers={"X-Tenant-ID": "invalid-uuid"}
        ):
            from app.middleware import inject_tenant
            # Should not raise, just skip tenant injection
            inject_tenant()
            
            assert g.tenant_id is None
    
    def test_request_ip_capture(self, app):
        """Request IP should be captured."""
        with app.test_request_context(
            "/health",
            environ_base={"REMOTE_ADDR": "192.168.1.100"}
        ):
            from app.middleware import inject_tenant
            inject_tenant()
            
            assert g.request_ip == "192.168.1.100"
    
    def test_user_agent_capture(self, app):
        """User agent should be captured."""
        with app.test_request_context(
            "/health",
            headers={"User-Agent": "Mozilla/5.0 Test"}
        ):
            from app.middleware import inject_tenant
            inject_tenant()
            
            assert "Mozilla" in g.user_agent
    
    def test_jwt_token_parsing_invalid(self, app):
        """Invalid JWT token should not crash."""
        with app.test_request_context(
            "/health",
            headers={"Authorization": "Bearer invalid.token.here"}
        ):
            from app.middleware import inject_tenant
            # Should not raise, just skip tenant injection
            inject_tenant()
            
            assert g.tenant_id is None
    
    def test_jwt_token_no_bearer_prefix(self, app):
        """Token without Bearer prefix should not crash."""
        with app.test_request_context(
            "/health",
            headers={"Authorization": "token-without-bearer"}
        ):
            from app.middleware import inject_tenant
            # Should not raise, just skip tenant injection
            inject_tenant()
            
            assert g.tenant_id is None
    
    def test_security_headers_added(self, client):
        """Response should include security headers."""
        response = client.get("/health")
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert "X-XSS-Protection" in response.headers
    
    def test_multiple_requests_context_cleanup(self, app, client):
        """Each request should have isolated g context."""
        test_tenant_id_1 = uuid4()
        test_tenant_id_2 = uuid4()
        
        # First request
        with app.test_request_context(
            "/health",
            headers={"X-Tenant-ID": str(test_tenant_id_1)}
        ):
            from app.middleware import inject_tenant
            inject_tenant()
            tenant_1 = g.tenant_id
        
        # Second request should have clean context
        with app.test_request_context(
            "/health",
            headers={"X-Tenant-ID": str(test_tenant_id_2)}
        ):
            from app.middleware import inject_tenant
            inject_tenant()
            tenant_2 = g.tenant_id
        
        assert tenant_1 == test_tenant_id_1
        assert tenant_2 == test_tenant_id_2
        assert tenant_1 != tenant_2


class TestAuthenticationServiceImports:
    """Test that AuthService imports and basic structure works."""
    
    def test_auth_service_imports(self, app):
        """AuthService should import without errors."""
        with app.app_context():
            from app.auth.services import AuthService, TokenService
            
            # Verify classes exist and have required methods
            assert hasattr(AuthService, "authenticate_user")
            assert hasattr(AuthService, "create_tenant_and_admin")
            assert hasattr(AuthService, "create_user_in_tenant")
            assert hasattr(AuthService, "request_password_reset")
            assert hasattr(AuthService, "reset_password")
            
            assert hasattr(TokenService, "generate_tokens")
            assert hasattr(TokenService, "generate_reset_token")
            assert hasattr(TokenService, "verify_reset_token")
    
    def test_token_generation_basic(self, app):
        """TokenService.generate_tokens should create valid JWT."""
        from app.auth.services import TokenService
        from uuid import uuid4
        
        with app.app_context():
            user_id = uuid4()
            tenant_id = uuid4()
            
            access_token, refresh_token = TokenService.generate_tokens(
                user_id=user_id,
                tenant_id=tenant_id
            )
            
            # Tokens should be non-empty strings
            assert isinstance(access_token, str)
            assert isinstance(refresh_token, str)
            assert len(access_token) > 0
            assert len(refresh_token) > 0
            assert access_token != refresh_token
    
    def test_reset_token_generation_and_verification(self, app):
        """TokenService reset token should be verifiable."""
        from app.auth.services import TokenService
        from uuid import uuid4
        
        with app.app_context():
            user_id = uuid4()
            tenant_id = uuid4()
            
            # Generate reset token
            reset_token = TokenService.generate_reset_token(
                user_id=user_id,
                tenant_id=tenant_id
            )
            
            # Verify token
            payload = TokenService.verify_reset_token(reset_token)
            
            assert payload is not None
            assert payload["user_id"] == str(user_id)
            assert payload["tenant_id"] == str(tenant_id)
            assert payload["type"] == "reset"
    
    def test_invalid_reset_token_returns_none(self, app):
        """Invalid reset token should return None."""
        from app.auth.services import TokenService
        
        with app.app_context():
            payload = TokenService.verify_reset_token("invalid.token.here")
            assert payload is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

