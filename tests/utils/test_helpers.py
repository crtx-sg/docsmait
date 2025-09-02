"""
Test Utilities and Helpers

Utility functions and helpers for testing Docsmait functionality.
"""

import pytest
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class DocsmaitTestHelper:
    """Helper class for common test operations."""
    
    def __init__(self, backend_url: str, api_client: requests.Session):
        self.backend_url = backend_url
        self.api_client = api_client
        self._admin_token = None
    
    def create_test_user(self, username_suffix: str = None) -> Dict[str, Any]:
        """Create a test user and return user data."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suffix = username_suffix or timestamp
        
        user_data = {
            "username": f"testuser_{suffix}",
            "email": f"testuser_{suffix}@docsmait.com",
            "password": "TestPassword123!",
            "confirm_password": "TestPassword123!"
        }
        
        response = self.api_client.post(f"{self.backend_url}/auth/signup", json=user_data)
        
        if response.status_code == 200:
            return {
                "user_data": user_data,
                "response": response.json(),
                "token": response.json().get("access_token")
            }
        else:
            raise Exception(f"Failed to create test user: {response.status_code} - {response.text}")
    
    def create_test_project(self, authenticated_client: requests.Session, project_name: str = None) -> Dict[str, Any]:
        """Create a test project and return project data."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name = project_name or f"Test Project {timestamp}"
        
        project_data = {
            "name": name,
            "description": f"Test project created at {timestamp}"
        }
        
        response = authenticated_client.post(f"{self.backend_url}/projects", json=project_data)
        
        if response.status_code == 201:
            return {
                "project_data": project_data,
                "response": response.json(),
                "project_id": response.json().get("id")
            }
        else:
            raise Exception(f"Failed to create test project: {response.status_code} - {response.text}")
    
    def wait_for_service_ready(self, max_wait_seconds: int = 30) -> bool:
        """Wait for backend service to be ready."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = requests.get(f"{self.backend_url}/settings", timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            
            time.sleep(1)
        
        return False
    
    def cleanup_test_projects(self, authenticated_client: requests.Session) -> int:
        """Clean up test projects. Returns number of projects cleaned up."""
        try:
            # Get all projects
            response = authenticated_client.get(f"{self.backend_url}/projects")
            if response.status_code != 200:
                return 0
            
            projects = response.json()
            cleaned_count = 0
            
            # Delete test projects (those with "Test" or "Integration" in name)
            for project in projects:
                if any(keyword in project["name"] for keyword in ["Test", "Integration", "Concurrent"]):
                    delete_response = authenticated_client.delete(f"{self.backend_url}/projects/{project['id']}")
                    if delete_response.status_code in [200, 204]:
                        cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            print(f"Error cleaning up projects: {e}")
            return 0


class TestDataGenerator:
    """Generate test data for various scenarios."""
    
    @staticmethod
    def generate_user_data(unique_suffix: str = None) -> Dict[str, str]:
        """Generate test user data."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # Include milliseconds
        suffix = unique_suffix or timestamp
        
        return {
            "username": f"user_{suffix}",
            "email": f"user_{suffix}@docsmait.com",
            "password": f"Pass123!_{suffix}",
            "confirm_password": f"Pass123!_{suffix}"
        }
    
    @staticmethod
    def generate_project_data(unique_suffix: str = None) -> Dict[str, str]:
        """Generate test project data."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suffix = unique_suffix or timestamp
        
        return {
            "name": f"Test Project {suffix}",
            "description": f"Generated test project created at {timestamp}"
        }
    
    @staticmethod
    def generate_document_data(unique_suffix: str = None) -> Dict[str, str]:
        """Generate test document data."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suffix = unique_suffix or timestamp
        
        return {
            "name": f"Test Document {suffix}",
            "content": f"# Test Document\n\nThis is a test document generated at {timestamp}.",
            "document_type": "SOP",
            "status": "draft"
        }
    
    @staticmethod
    def generate_template_data(unique_suffix: str = None) -> Dict[str, Any]:
        """Generate test template data."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suffix = unique_suffix or timestamp
        
        return {
            "name": f"Test Template {suffix}",
            "description": f"Generated test template created at {timestamp}",
            "document_type": "SOP",
            "content": "# {{title}}\n\n{{content}}\n\nGenerated: {{timestamp}}",
            "tags": ["test", "generated", suffix]
        }


class TestAssertions:
    """Extended assertions for Docsmait testing."""
    
    @staticmethod
    def assert_valid_response_structure(response: requests.Response, expected_keys: List[str], optional_keys: List[str] = None):
        """Assert response has valid JSON structure with expected keys."""
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")
        
        # Check required keys
        for key in expected_keys:
            assert key in data, f"Required key '{key}' missing from response"
        
        # Check optional keys (don't fail if missing)
        if optional_keys:
            for key in optional_keys:
                if key not in data:
                    print(f"Optional key '{key}' not found in response")
    
    @staticmethod
    def assert_performance_acceptable(response_time: float, max_acceptable: float = 2.0):
        """Assert response time is acceptable."""
        assert response_time <= max_acceptable, f"Response time {response_time:.2f}s exceeds limit {max_acceptable}s"
    
    @staticmethod
    def assert_no_sensitive_data(data: Dict[str, Any], sensitive_fields: List[str] = None):
        """Assert response doesn't contain sensitive data."""
        if sensitive_fields is None:
            sensitive_fields = ["password", "password_hash", "secret", "private_key", "token"]
        
        def check_dict(d: Dict, path: str = ""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check if key is sensitive
                if key.lower() in [field.lower() for field in sensitive_fields]:
                    pytest.fail(f"Sensitive field '{key}' found at {current_path}")
                
                # Check if value contains sensitive patterns
                if isinstance(value, str) and len(value) > 10:
                    for sensitive_field in sensitive_fields:
                        if sensitive_field.lower() in value.lower():
                            pytest.fail(f"Sensitive data pattern '{sensitive_field}' found in {current_path}")
                
                # Recursively check nested dictionaries
                if isinstance(value, dict):
                    check_dict(value, current_path)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            check_dict(item, f"{current_path}[{i}]")
        
        if isinstance(data, dict):
            check_dict(data)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    check_dict(item, f"[{i}]")
    
    @staticmethod
    def assert_valid_timestamp(timestamp_str: str, tolerance_minutes: int = 5):
        """Assert timestamp is valid and recent."""
        try:
            # Try multiple timestamp formats
            timestamp_formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ", 
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S"
            ]
            
            parsed_time = None
            for fmt in timestamp_formats:
                try:
                    parsed_time = datetime.strptime(timestamp_str, fmt)
                    break
                except ValueError:
                    continue
            
            assert parsed_time is not None, f"Invalid timestamp format: {timestamp_str}"
            
            # Check if timestamp is reasonable (within tolerance)
            now = datetime.utcnow()
            time_diff = abs((now - parsed_time).total_seconds() / 60)
            
            assert time_diff <= tolerance_minutes, f"Timestamp {timestamp_str} is too far from current time"
            
        except Exception as e:
            pytest.fail(f"Timestamp validation failed for '{timestamp_str}': {e}")


class DatabaseTestHelper:
    """Helper for database-related testing."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    def get_table_count(self, table_name: str) -> int:
        """Get count of records in a table."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(self.database_url)
            
            with engine.connect() as connection:
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.fetchone()[0]
                
        except Exception as e:
            pytest.skip(f"Cannot count table {table_name}: {e}")
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            from sqlalchemy import create_engine, inspect
            engine = create_engine(self.database_url)
            inspector = inspect(engine)
            
            return table_name in inspector.get_table_names()
            
        except Exception:
            return False
    
    def create_test_data(self, table_name: str, data: Dict[str, Any]) -> Optional[int]:
        """Insert test data into a table. Returns inserted ID if applicable."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(self.database_url)
            
            columns = ", ".join(data.keys())
            placeholders = ", ".join(f":{key}" for key in data.keys())
            
            with engine.begin() as connection:
                result = connection.execute(
                    text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING id"),
                    data
                )
                return result.fetchone()[0]
                
        except Exception as e:
            print(f"Failed to create test data in {table_name}: {e}")
            return None
    
    def cleanup_test_data(self, table_name: str, conditions: Dict[str, Any]) -> int:
        """Clean up test data. Returns number of deleted records."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(self.database_url)
            
            where_clause = " AND ".join(f"{key} = :{key}" for key in conditions.keys())
            
            with engine.begin() as connection:
                result = connection.execute(
                    text(f"DELETE FROM {table_name} WHERE {where_clause}"),
                    conditions
                )
                return result.rowcount
                
        except Exception as e:
            print(f"Failed to cleanup test data in {table_name}: {e}")
            return 0


# Pytest fixtures using the helpers
@pytest.fixture
def test_helper(backend_url, api_client):
    """Provide test helper instance."""
    return DocsmaitTestHelper(backend_url, api_client)

@pytest.fixture
def data_generator():
    """Provide test data generator."""
    return TestDataGenerator()

@pytest.fixture
def test_assertions():
    """Provide extended test assertions."""
    return TestAssertions()

@pytest.fixture
def db_helper(test_config):
    """Provide database test helper."""
    return DatabaseTestHelper(test_config["database_url"])

@pytest.fixture(autouse=True)
def cleanup_after_test(test_helper, authenticated_client):
    """Automatically cleanup test data after each test."""
    yield
    
    # Cleanup after test
    try:
        cleaned_count = test_helper.cleanup_test_projects(authenticated_client)
        if cleaned_count > 0:
            print(f"Cleaned up {cleaned_count} test projects")
    except Exception as e:
        print(f"Cleanup warning: {e}")


# Test the helpers themselves
@pytest.mark.utils
class TestHelpers:
    """Test the helper functions."""
    
    def test_data_generator_user_data(self, data_generator):
        """Test user data generation."""
        user_data = data_generator.generate_user_data()
        
        required_fields = ["username", "email", "password", "confirm_password"]
        for field in required_fields:
            assert field in user_data
            assert len(user_data[field]) > 0
        
        # Password should match confirm_password
        assert user_data["password"] == user_data["confirm_password"]
        
        # Email should be valid format
        assert "@" in user_data["email"]
    
    def test_data_generator_project_data(self, data_generator):
        """Test project data generation."""
        project_data = data_generator.generate_project_data()
        
        required_fields = ["name", "description"]
        for field in required_fields:
            assert field in project_data
            assert len(project_data[field]) > 0
    
    def test_assertions_valid_response_structure(self, test_assertions, backend_url):
        """Test response structure assertions."""
        response = requests.get(f"{backend_url}/settings")
        
        if response.status_code == 200:
            # Should not raise assertion error
            test_assertions.assert_valid_response_structure(
                response, 
                ["general_llm", "embedding_model"]
            )
    
    def test_performance_assertion(self, test_assertions):
        """Test performance assertion."""
        # Should pass
        test_assertions.assert_performance_acceptable(0.5, 1.0)
        
        # Should fail
        with pytest.raises(AssertionError):
            test_assertions.assert_performance_acceptable(2.0, 1.0)
    
    def test_sensitive_data_assertion(self, test_assertions):
        """Test sensitive data detection."""
        # Should pass (no sensitive data)
        clean_data = {"name": "test", "description": "clean data"}
        test_assertions.assert_no_sensitive_data(clean_data)
        
        # Should fail (contains sensitive data)
        with pytest.raises(Exception):
            sensitive_data = {"name": "test", "password": "secret123"}
            test_assertions.assert_no_sensitive_data(sensitive_data)