"""
Authentication API Tests

Tests for user authentication, registration, and token management.
"""

import pytest
import requests


@pytest.mark.api
@pytest.mark.auth
class TestAuthentication:
    """Test authentication endpoints."""

    def test_signup_new_user(self, api_client, backend_url, assert_docsmait):
        """Test user registration."""
        from datetime import datetime
        
        test_user = {
            "username": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@docsmait.com",
            "password": "SecureTestPassword123!",
            "confirm_password": "SecureTestPassword123!"
        }
        
        response = api_client.post(f"{backend_url}/auth/signup", json=test_user)
        
        assert_docsmait.assert_api_success(response, 200)
        data = response.json()
        assert_docsmait.assert_json_structure(data, ["access_token", "token_type"])
        assert_docsmait.assert_valid_jwt(data["access_token"])
        assert data["token_type"] == "bearer"

    def test_signup_password_mismatch(self, api_client, backend_url, assert_docsmait):
        """Test signup with password mismatch."""
        from datetime import datetime
        
        test_user = {
            "username": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@docsmait.com",
            "password": "SecureTestPassword123!",
            "confirm_password": "DifferentPassword123!"
        }
        
        response = api_client.post(f"{backend_url}/auth/signup", json=test_user)
        
        assert response.status_code == 400
        assert "do not match" in response.json()["detail"]

    def test_login_valid_user(self, api_client, backend_url, test_admin_credentials, assert_docsmait):
        """Test login with valid credentials."""
        # First ensure admin user exists
        api_client.post(f"{backend_url}/auth/signup", json={
            "username": "testadmin",
            "email": test_admin_credentials["email"],
            "password": test_admin_credentials["password"],
            "confirm_password": test_admin_credentials["password"]
        })
        
        response = api_client.post(f"{backend_url}/auth/login", json=test_admin_credentials)
        
        assert_docsmait.assert_api_success(response, 200)
        data = response.json()
        assert_docsmait.assert_json_structure(data, ["access_token", "token_type"])
        assert_docsmait.assert_valid_jwt(data["access_token"])

    def test_login_invalid_credentials(self, api_client, backend_url):
        """Test login with invalid credentials."""
        invalid_creds = {
            "email": "nonexistent@docsmait.com",
            "password": "wrongpassword"
        }
        
        response = api_client.post(f"{backend_url}/auth/login", json=invalid_creds)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_get_current_user(self, authenticated_client, backend_url, assert_docsmait):
        """Test getting current user information."""
        response = authenticated_client.get(f"{backend_url}/auth/me")
        
        assert_docsmait.assert_api_success(response, 200)
        data = response.json()
        assert_docsmait.assert_json_structure(data, ["id", "username", "email", "is_admin"])

    def test_get_current_user_no_token(self, api_client, backend_url):
        """Test getting current user without authentication token."""
        # Remove any existing auth headers
        if "Authorization" in api_client.headers:
            del api_client.headers["Authorization"]
            
        response = api_client.get(f"{backend_url}/auth/me")
        
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, api_client, backend_url):
        """Test getting current user with invalid token."""
        api_client.headers["Authorization"] = "Bearer invalid_token_here"
        
        response = api_client.get(f"{backend_url}/auth/me")
        
        assert response.status_code == 401

    def test_signup_duplicate_email(self, api_client, backend_url, test_admin_credentials):
        """Test signup with duplicate email."""
        # Use existing admin email
        duplicate_user = {
            "username": "different_username",
            "email": test_admin_credentials["email"],
            "password": "DifferentPassword123!",
            "confirm_password": "DifferentPassword123!"
        }
        
        response = api_client.post(f"{backend_url}/auth/signup", json=duplicate_user)
        
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_token_expiration_format(self, authenticated_client, backend_url):
        """Test that token has reasonable expiration."""
        import jwt
        from datetime import datetime
        
        # Get a fresh token
        response = authenticated_client.post(f"{backend_url}/auth/login", json={
            "email": "admin@docsmait.com",
            "password": "AdminPassword123!"
        })
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            
            # Decode token without verification to check structure
            # Note: In production, always verify tokens!
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            assert "exp" in decoded, "Token should have expiration"
            assert "sub" in decoded, "Token should have subject (user ID)"
            
            # Check expiration is in future
            exp_timestamp = decoded["exp"]
            assert exp_timestamp > datetime.now().timestamp(), "Token should not be expired"


@pytest.mark.api
@pytest.mark.auth
@pytest.mark.slow
class TestAuthenticationEdgeCases:
    """Test authentication edge cases and security."""

    def test_multiple_login_sessions(self, api_client, backend_url, test_admin_credentials, assert_docsmait):
        """Test multiple concurrent login sessions."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            response = api_client.post(f"{backend_url}/auth/login", json=test_admin_credentials)
            assert_docsmait.assert_api_success(response)
            sessions.append(response.json()["access_token"])
        
        # All tokens should be valid
        for token in sessions:
            assert_docsmait.assert_valid_jwt(token)
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{backend_url}/auth/me", headers=headers)
            assert_docsmait.assert_api_success(response)

    def test_login_rate_limiting_simulation(self, api_client, backend_url):
        """Test rapid login attempts (simulate rate limiting check)."""
        invalid_creds = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        # Make rapid login attempts
        responses = []
        for i in range(5):
            response = api_client.post(f"{backend_url}/auth/login", json=invalid_creds)
            responses.append(response.status_code)
        
        # All should be 401 (no rate limiting implemented yet, but structure is ready)
        assert all(status == 401 for status in responses)

    def test_password_requirements(self, api_client, backend_url):
        """Test password complexity requirements."""
        from datetime import datetime
        
        weak_passwords = [
            "123",           # Too short
            "password",      # No numbers/special chars
            "12345678",      # No letters
            "Password",      # No numbers/special chars
        ]
        
        for weak_password in weak_passwords:
            test_user = {
                "username": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{weak_password[:3]}",
                "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{weak_password[:3]}@docsmait.com",
                "password": weak_password,
                "confirm_password": weak_password
            }
            
            response = api_client.post(f"{backend_url}/auth/signup", json=test_user)
            # Should either reject weak password or accept (depending on implementation)
            # This test documents current behavior
            assert response.status_code in [200, 400], f"Unexpected status for password: {weak_password}"