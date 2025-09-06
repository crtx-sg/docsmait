"""
Docsmait Test Suite Configuration

This file contains shared fixtures and configuration for all tests.
"""

import os
import sys
import pytest
import requests
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

# Import centralized configuration for testing
try:
    sys.path.append(str(project_root))
    from config.environments import TestingConfig
    test_config = TestingConfig()
    
    # Test configuration using centralized config
    TEST_CONFIG = {
        "backend_url": test_config.backend_url,
        "frontend_url": test_config.frontend_url,
        "database_url": test_config.database_url,
        "test_timeout": getattr(test_config, 'DEFAULT_TIMEOUT', int(os.getenv("TEST_TIMEOUT", "30"))),
        "test_user_email": os.getenv("TEST_USER_EMAIL", "test@docsmait.com"),
        "test_user_password": os.getenv("TEST_USER_PASSWORD", "TestPassword123!"),
        "test_admin_email": os.getenv("TEST_ADMIN_EMAIL", "admin@docsmait.com"),
        "test_admin_password": os.getenv("TEST_ADMIN_PASSWORD", "AdminPassword123!"),
    }
except ImportError:
    # Fallback configuration
    TEST_CONFIG = {
        "backend_url": os.getenv("TEST_BACKEND_URL", "http://localhost:8001"),
        "frontend_url": os.getenv("TEST_FRONTEND_URL", "http://localhost:8501"),
        "database_url": os.getenv("TEST_DATABASE_URL", "postgresql://docsmait_user:docsmait_password@localhost:5433/docsmait_test"),
        "test_timeout": int(os.getenv("TEST_TIMEOUT", "30")),
        "test_user_email": os.getenv("TEST_USER_EMAIL", "test@docsmait.com"),
        "test_user_password": os.getenv("TEST_USER_PASSWORD", "TestPassword123!"),
        "test_admin_email": os.getenv("TEST_ADMIN_EMAIL", "admin@docsmait.com"),
        "test_admin_password": os.getenv("TEST_ADMIN_PASSWORD", "AdminPassword123!"),
    }

# Test results directory
TEST_RESULTS_DIR = Path(__file__).parent / "test_results"
TEST_RESULTS_DIR.mkdir(exist_ok=True)

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration to all tests."""
    return TEST_CONFIG

@pytest.fixture(scope="session")
def backend_url(test_config):
    """Backend API base URL."""
    return test_config["backend_url"]

@pytest.fixture(scope="session")
def frontend_url(test_config):
    """Frontend application base URL."""
    return test_config["frontend_url"]

@pytest.fixture(scope="session")
def api_client(backend_url):
    """HTTP client for API testing."""
    session = requests.Session()
    session.timeout = TEST_CONFIG["test_timeout"]
    session.base_url = backend_url
    return session

@pytest.fixture
def test_user_credentials(test_config):
    """Test user credentials."""
    return {
        "email": test_config["test_user_email"],
        "password": test_config["test_user_password"]
    }

@pytest.fixture
def test_admin_credentials(test_config):
    """Test admin credentials."""
    return {
        "email": test_config["test_admin_email"],
        "password": test_config["test_admin_password"]
    }

@pytest.fixture
def authenticated_client(api_client, test_admin_credentials, backend_url):
    """API client with authentication token."""
    # Login to get token
    login_response = api_client.post(
        f"{backend_url}/auth/login",
        json=test_admin_credentials
    )
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        api_client.headers.update({"Authorization": f"Bearer {token}"})
    else:
        # Try to create admin user if login fails
        signup_response = api_client.post(
            f"{backend_url}/auth/signup",
            json={
                "username": "testadmin",
                "email": test_admin_credentials["email"],
                "password": test_admin_credentials["password"],
                "confirm_password": test_admin_credentials["password"]
            }
        )
        if signup_response.status_code == 200:
            token = signup_response.json()["access_token"]
            api_client.headers.update({"Authorization": f"Bearer {token}"})
    
    return api_client

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before running tests."""
    # Check if services are running
    backend_health = check_service_health(TEST_CONFIG["backend_url"])
    
    if not backend_health:
        pytest.exit("Backend service is not running. Please start Docsmait with 'docker compose up -d'")
    
    # Create test results directory
    TEST_RESULTS_DIR.mkdir(exist_ok=True)
    
    # Log test session start
    with open(TEST_RESULTS_DIR / "test_session.log", "a") as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"Test session started: {datetime.now()}\n")
        f.write(f"Backend URL: {TEST_CONFIG['backend_url']}\n")
        f.write(f"Frontend URL: {TEST_CONFIG['frontend_url']}\n")
        f.write(f"{'='*50}\n")

def check_service_health(url):
    """Check if a service is healthy."""
    try:
        response = requests.get(f"{url}/settings", timeout=5)
        return response.status_code == 200
    except:
        return False

@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": f"Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "This is a test project created by automated tests"
    }

@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "name": f"Test Document {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "document_type": "SOP",
        "content": "# Test Document\n\nThis is a test document created by automated tests.",
        "status": "draft"
    }

@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return {
        "name": f"Test Template {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Test template for automated testing",
        "document_type": "SOP",
        "content": "# {{title}}\n\n{{content}}",
        "tags": ["test", "automation"]
    }

# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests as authentication tests"
    )
    config.addinivalue_line(
        "markers", "database: marks tests as database tests"
    )
    config.addinivalue_line(
        "markers", "frontend: marks tests as frontend tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )

def pytest_sessionfinish(session, exitstatus):
    """Log test session completion."""
    with open(TEST_RESULTS_DIR / "test_session.log", "a") as f:
        f.write(f"Test session finished: {datetime.now()}\n")
        f.write(f"Exit status: {exitstatus}\n")
        f.write(f"{'='*50}\n")

# Custom assertions
class DocsmaitAssertions:
    """Custom assertions for Docsmait testing."""
    
    @staticmethod
    def assert_api_success(response, expected_status=200):
        """Assert API response is successful."""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
    
    @staticmethod
    def assert_json_structure(data, expected_keys):
        """Assert JSON contains expected keys."""
        for key in expected_keys:
            assert key in data, f"Expected key '{key}' not found in response"
    
    @staticmethod
    def assert_valid_jwt(token):
        """Assert token looks like a valid JWT."""
        import re
        jwt_pattern = r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$'
        assert re.match(jwt_pattern, token), "Invalid JWT format"

@pytest.fixture
def assert_docsmait():
    """Provide custom assertions."""
    return DocsmaitAssertions()

# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    # Cleanup logic would go here
    # For now, we'll rely on test isolation
    pass