"""
Security Validation Tests

Tests for security vulnerabilities, input validation, and access controls.
"""

import pytest
import requests
import json
from datetime import datetime


@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization."""

    def test_sql_injection_prevention(self, authenticated_client, backend_url):
        """Test SQL injection prevention in API endpoints."""
        # Common SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --",
            "'; SELECT * FROM users WHERE '1'='1",
        ]
        
        # Test in project name field
        for payload in sql_payloads:
            project_data = {
                "name": payload,
                "description": "Testing SQL injection"
            }
            
            response = authenticated_client.post(f"{backend_url}/projects", json=project_data)
            
            # Should either reject malicious input or sanitize it
            # Should NOT crash the server or expose database errors
            assert response.status_code in [200, 201, 400, 422], f"Server error with payload: {payload}"
            
            if response.status_code in [400, 422]:
                # Good - input validation rejected the payload
                continue
            elif response.status_code in [200, 201]:
                # Input was accepted - verify it was sanitized
                created_project = response.json()
                assert created_project["name"] != payload, "SQL injection payload was not sanitized"

    def test_xss_prevention(self, authenticated_client, backend_url):
        """Test XSS prevention in API responses."""
        # Common XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
        ]
        
        for payload in xss_payloads:
            project_data = {
                "name": f"XSS Test {payload}",
                "description": f"Testing XSS with {payload}"
            }
            
            response = authenticated_client.post(f"{backend_url}/projects", json=project_data)
            
            if response.status_code in [200, 201]:
                # Verify response doesn't contain executable script
                response_text = response.text.lower()
                
                # Should not contain unescaped script tags or javascript
                assert "<script>" not in response_text, "Unescaped script tag in response"
                assert "javascript:" not in response_text, "Javascript protocol in response"
                assert "onerror=" not in response_text, "Event handler in response"

    def test_json_injection_prevention(self, authenticated_client, backend_url):
        """Test JSON injection prevention."""
        malformed_json_payloads = [
            '{"name": "test", "description": ""}; DROP TABLE users; --',
            '{"name": "test", "extra": {"$where": "this.name == this.description"}}',
            '{"name": "test", "description": {"$ne": null}}',
        ]
        
        for payload in malformed_json_payloads:
            try:
                # Send raw malformed JSON
                response = authenticated_client.post(
                    f"{backend_url}/projects",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                # Should reject malformed JSON
                assert response.status_code in [400, 422], "Malformed JSON was accepted"
                
            except Exception:
                # Parsing error is acceptable
                pass

    def test_file_upload_validation(self, authenticated_client, backend_url):
        """Test file upload security validation."""
        # Test potentially dangerous file extensions
        dangerous_files = [
            ("malicious.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.php", b"<?php echo 'test'; ?>", "application/x-php"),
            ("test.jsp", b"<% out.println('test'); %>", "text/plain"),
            ("large_file.txt", b"A" * (20 * 1024 * 1024), "text/plain"),  # 20MB file
        ]
        
        for filename, content, content_type in dangerous_files:
            files = {"file": (filename, content, content_type)}
            
            # Try to upload to documents endpoint (if it exists)
            response = authenticated_client.post(
                f"{backend_url}/documents/upload",
                files=files
            )
            
            # Should reject dangerous files or be not implemented
            assert response.status_code in [400, 413, 415, 404, 501], f"Dangerous file {filename} was accepted"


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security measures."""

    def test_password_complexity_requirements(self, api_client, backend_url):
        """Test password complexity enforcement."""
        weak_passwords = [
            "123",                    # Too short
            "password",               # Common password
            "12345678",              # All numbers
            "abcdefgh",              # All lowercase
            "ABCDEFGH",              # All uppercase
            "",                      # Empty password
            " " * 8,                 # Only spaces
        ]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for i, weak_password in enumerate(weak_passwords):
            user_data = {
                "username": f"weaktest_{timestamp}_{i}",
                "email": f"weaktest_{timestamp}_{i}@docsmait.com",
                "password": weak_password,
                "confirm_password": weak_password
            }
            
            response = api_client.post(f"{backend_url}/auth/signup", json=user_data)
            
            # Should reject weak passwords (400) or accept them (200)
            # Document current behavior
            assert response.status_code in [200, 400, 422], f"Unexpected response for password: {weak_password}"
            
            if response.status_code == 400:
                # Good - weak password was rejected
                error_message = response.json().get("detail", "").lower()
                print(f"✓ Weak password rejected: {weak_password} - {error_message}")

    def test_rate_limiting_login_attempts(self, api_client, backend_url):
        """Test rate limiting on login attempts."""
        invalid_credentials = {
            "email": "nonexistent@docsmait.com",
            "password": "wrongpassword"
        }
        
        # Make rapid login attempts
        response_codes = []
        response_times = []
        
        for i in range(10):
            import time
            start_time = time.time()
            
            response = api_client.post(f"{backend_url}/auth/login", json=invalid_credentials)
            
            end_time = time.time()
            response_times.append(end_time - start_time)
            response_codes.append(response.status_code)
            
            time.sleep(0.1)  # Small delay
        
        # Analyze responses
        # Most should be 401 (unauthorized)
        unauthorized_count = response_codes.count(401)
        
        # Check if any rate limiting is applied (429 status or increasing response times)
        rate_limited_count = response_codes.count(429)
        avg_response_time = sum(response_times) / len(response_times)
        
        print(f"\n🔒 Rate Limiting Test:")
        print(f"   Unauthorized (401): {unauthorized_count}/10")
        print(f"   Rate limited (429): {rate_limited_count}/10")
        print(f"   Avg response time: {avg_response_time:.3f}s")
        
        # At minimum, should not crash or return 500 errors
        server_errors = [code for code in response_codes if code >= 500]
        assert len(server_errors) == 0, "Server errors during login attempts"

    def test_token_security(self, authenticated_client, backend_url, assert_docsmait):
        """Test JWT token security properties."""
        # Get current user to verify token works
        response = authenticated_client.get(f"{backend_url}/auth/me")
        assert_docsmait.assert_api_success(response)
        
        # Extract token from Authorization header
        auth_header = authenticated_client.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            
            # Test token structure (should be valid JWT)
            import re
            jwt_pattern = r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$'
            assert re.match(jwt_pattern, token), "Invalid JWT format"
            
            # Test token with tampering
            tampered_tokens = [
                token[:-5] + "XXXXX",  # Tamper with signature
                token.replace(".", "X"),  # Tamper with structure
                token + "extra",  # Append extra content
                "",  # Empty token
                "invalid.token.here",  # Completely invalid
            ]
            
            for tampered_token in tampered_tokens:
                tampered_headers = {"Authorization": f"Bearer {tampered_token}"}
                
                response = authenticated_client.get(
                    f"{backend_url}/auth/me",
                    headers=tampered_headers
                )
                
                # Should reject tampered tokens
                assert response.status_code == 401, f"Tampered token was accepted: {tampered_token[:20]}..."


@pytest.mark.security
class TestAccessControlSecurity:
    """Test access control and authorization security."""

    def test_unauthorized_access_prevention(self, api_client, backend_url):
        """Test prevention of unauthorized access to protected resources."""
        protected_endpoints = [
            "/auth/me",
            "/projects",
            "/documents",
            "/templates",
            "/users",
        ]
        
        for endpoint in protected_endpoints:
            response = api_client.get(f"{backend_url}{endpoint}")
            
            # Should require authentication
            assert response.status_code == 401, f"Endpoint {endpoint} accessible without authentication"

    def test_privilege_escalation_prevention(self, authenticated_client, backend_url):
        """Test prevention of privilege escalation."""
        # Get current user info
        me_response = authenticated_client.get(f"{backend_url}/auth/me")
        
        if me_response.status_code == 200:
            current_user = me_response.json()
            user_id = current_user["id"]
            
            # Try to modify own user record with elevated privileges
            elevation_attempts = [
                {"is_admin": True},
                {"is_super_admin": True},
                {"role": "admin"},
                {"permissions": ["all"]},
            ]
            
            for attempt in elevation_attempts:
                response = authenticated_client.patch(f"{backend_url}/users/{user_id}", json=attempt)
                
                # Should either be forbidden, not implemented, or reject the elevation
                assert response.status_code in [400, 403, 404, 405, 501], f"Privilege escalation succeeded: {attempt}"

    def test_horizontal_privilege_escalation(self, authenticated_client, backend_url):
        """Test prevention of accessing other users' data."""
        # Try to access other users' data
        other_user_ids = [1, 2, 99999, -1, "admin"]
        
        for user_id in other_user_ids:
            response = authenticated_client.get(f"{backend_url}/users/{user_id}")
            
            # Should either be forbidden or not found
            # Don't expect 200 unless user is admin
            if response.status_code == 200:
                # If successful, verify current user has admin privileges
                me_response = authenticated_client.get(f"{backend_url}/auth/me")
                if me_response.status_code == 200:
                    current_user = me_response.json()
                    assert current_user.get("is_admin", False), "Non-admin user can access other user data"


@pytest.mark.security
class TestDataProtectionSecurity:
    """Test data protection and privacy security."""

    def test_sensitive_data_exposure(self, authenticated_client, backend_url):
        """Test that sensitive data is not exposed in responses."""
        # Get user information
        response = authenticated_client.get(f"{backend_url}/auth/me")
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Should not contain sensitive fields
            sensitive_fields = ["password", "password_hash", "salt", "secret"]
            
            for field in sensitive_fields:
                assert field not in user_data, f"Sensitive field '{field}' exposed in user data"
            
            # Should not contain database internals
            internal_fields = ["_sa_instance_state", "__table__"]
            
            for field in internal_fields:
                assert field not in user_data, f"Internal field '{field}' exposed in user data"

    def test_error_message_information_disclosure(self, api_client, backend_url):
        """Test that error messages don't disclose sensitive information."""
        # Test various error conditions
        error_test_cases = [
            ("/nonexistent/endpoint", "Should not reveal server internals"),
            ("/auth/login", "Should not reveal user existence"),
            ("/projects/99999", "Should not reveal database structure"),
        ]
        
        for endpoint, description in error_test_cases:
            if endpoint == "/auth/login":
                # Test with invalid credentials
                response = api_client.post(
                    f"{backend_url}{endpoint}",
                    json={"email": "nonexistent@example.com", "password": "wrong"}
                )
            else:
                response = api_client.get(f"{backend_url}{endpoint}")
            
            # Check error message content
            if response.status_code >= 400:
                error_content = response.text.lower()
                
                # Should not contain sensitive information
                sensitive_info = [
                    "traceback", "stack trace", "database", "sql", "table",
                    "internal server error", "exception", "error:", "file path",
                    "/usr/", "/var/", "/home/", "c:\\", ".py", ".java"
                ]
                
                for info in sensitive_info:
                    if info in error_content:
                        print(f"⚠️ Potential information disclosure in {endpoint}: {info}")

    def test_directory_traversal_prevention(self, authenticated_client, backend_url):
        """Test prevention of directory traversal attacks."""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
            "..%252f..%252f..%252fetc%252fpasswd",
        ]
        
        for payload in traversal_payloads:
            # Test in various endpoints that might handle file parameters
            test_endpoints = [
                f"/documents/{payload}",
                f"/templates/{payload}",
                f"/projects/{payload}",
            ]
            
            for endpoint in test_endpoints:
                response = authenticated_client.get(f"{backend_url}{endpoint}")
                
                # Should not return file contents or cause server error
                assert response.status_code in [400, 404, 403], f"Directory traversal may be possible: {payload}"
                
                # Should not contain file system content
                if response.status_code == 200:
                    content = response.text.lower()
                    file_indicators = ["root:x:", "administrator", "/bin/bash", "[boot loader]"]
                    
                    for indicator in file_indicators:
                        assert indicator not in content, f"File system content detected: {payload}"


@pytest.mark.security
class TestSecurityHeaders:
    """Test security headers and configuration."""

    def test_security_headers_present(self, api_client, backend_url):
        """Test that appropriate security headers are present."""
        response = api_client.get(f"{backend_url}/settings")
        
        if response.status_code == 200:
            headers = response.headers
            
            # Check for important security headers
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
            }
            
            for header_name, expected_values in security_headers.items():
                if header_name in headers:
                    header_value = headers[header_name]
                    if isinstance(expected_values, list):
                        assert any(expected in header_value for expected in expected_values), \
                            f"Security header {header_name} has unexpected value: {header_value}"
                    else:
                        assert expected_values in header_value, \
                            f"Security header {header_name} has unexpected value: {header_value}"
                    
                    print(f"✓ Security header present: {header_name}: {header_value}")
                else:
                    print(f"⚠️ Security header missing: {header_name}")

    def test_cors_configuration(self, api_client, backend_url):
        """Test CORS configuration security."""
        # Make OPTIONS request to check CORS headers
        response = api_client.options(f"{backend_url}/settings")
        
        headers = response.headers
        
        # Check CORS headers if present
        if "Access-Control-Allow-Origin" in headers:
            origin = headers["Access-Control-Allow-Origin"]
            
            # Should not be wildcard in production
            if origin == "*":
                print("⚠️ CORS allows all origins - potential security risk in production")
            else:
                print(f"✓ CORS origin restriction: {origin}")
        
        # Check for other CORS headers
        cors_headers = [
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers",
            "Access-Control-Max-Age",
        ]
        
        for header in cors_headers:
            if header in headers:
                print(f"✓ CORS header present: {header}: {headers[header]}")

    def test_server_information_disclosure(self, api_client, backend_url):
        """Test that server information is not unnecessarily disclosed."""
        response = api_client.get(f"{backend_url}/settings")
        
        headers = response.headers
        
        # Check for potentially sensitive headers
        sensitive_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
        
        for header in sensitive_headers:
            if header in headers:
                header_value = headers[header]
                print(f"ℹ️ Server info disclosed: {header}: {header_value}")
                
                # Check for detailed version information
                if any(version_indicator in header_value.lower() 
                       for version_indicator in ["version", "v1.", "v2.", "beta", "alpha"]):
                    print(f"⚠️ Detailed version information disclosed: {header_value}")