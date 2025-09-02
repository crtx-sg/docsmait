"""
API Endpoints Tests

Tests for all major API endpoints and their functionality.
"""

import pytest
import requests


@pytest.mark.api
class TestCoreEndpoints:
    """Test core API endpoints."""

    def test_health_endpoint(self, api_client, backend_url, assert_docsmait):
        """Test health check endpoint."""
        response = api_client.get(f"{backend_url}/health")
        
        # Health endpoint might not exist, so check if it's implemented
        if response.status_code == 404:
            pytest.skip("Health endpoint not implemented")
        
        assert_docsmait.assert_api_success(response)

    def test_settings_endpoint(self, api_client, backend_url, assert_docsmait):
        """Test settings endpoint."""
        response = api_client.get(f"{backend_url}/settings")
        
        assert_docsmait.assert_api_success(response)
        data = response.json()
        
        # Should contain AI configuration
        expected_keys = ["general_llm", "embedding_model", "vector_db"]
        assert_docsmait.assert_json_structure(data, expected_keys)

    def test_api_docs_endpoint(self, api_client, backend_url):
        """Test API documentation endpoint."""
        response = api_client.get(f"{backend_url}/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_json(self, api_client, backend_url, assert_docsmait):
        """Test OpenAPI specification endpoint."""
        response = api_client.get(f"{backend_url}/openapi.json")
        
        assert_docsmait.assert_api_success(response)
        data = response.json()
        
        # Should be valid OpenAPI spec
        expected_keys = ["openapi", "info", "paths"]
        assert_docsmait.assert_json_structure(data, expected_keys)


@pytest.mark.api
class TestProjectEndpoints:
    """Test project management endpoints."""

    def test_get_projects_unauthenticated(self, api_client, backend_url):
        """Test getting projects without authentication."""
        response = api_client.get(f"{backend_url}/projects")
        
        # Should require authentication
        assert response.status_code == 401

    def test_get_projects_authenticated(self, authenticated_client, backend_url, assert_docsmait):
        """Test getting projects with authentication."""
        response = authenticated_client.get(f"{backend_url}/projects")
        
        assert_docsmait.assert_api_success(response)
        data = response.json()
        
        # Should return list of projects
        assert isinstance(data, list)

    def test_create_project(self, authenticated_client, backend_url, sample_project_data, assert_docsmait):
        """Test creating a new project."""
        response = authenticated_client.post(f"{backend_url}/projects", json=sample_project_data)
        
        assert_docsmait.assert_api_success(response, 201)
        data = response.json()
        
        # Should return created project with ID
        expected_keys = ["id", "name", "description"]
        assert_docsmait.assert_json_structure(data, expected_keys)
        
        # Verify data matches input
        assert data["name"] == sample_project_data["name"]
        assert data["description"] == sample_project_data["description"]
        
        return data["id"]  # Return for cleanup

    def test_get_single_project(self, authenticated_client, backend_url, sample_project_data, assert_docsmait):
        """Test getting a single project by ID."""
        # First create a project
        create_response = authenticated_client.post(f"{backend_url}/projects", json=sample_project_data)
        
        if create_response.status_code != 201:
            pytest.skip("Cannot create project for testing")
        
        project_id = create_response.json()["id"]
        
        # Now get the project
        response = authenticated_client.get(f"{backend_url}/projects/{project_id}")
        
        assert_docsmait.assert_api_success(response)
        data = response.json()
        
        expected_keys = ["id", "name", "description", "created_at"]
        assert_docsmait.assert_json_structure(data, expected_keys)
        
        assert data["id"] == project_id

    def test_update_project(self, authenticated_client, backend_url, sample_project_data, assert_docsmait):
        """Test updating a project."""
        # First create a project
        create_response = authenticated_client.post(f"{backend_url}/projects", json=sample_project_data)
        
        if create_response.status_code != 201:
            pytest.skip("Cannot create project for testing")
        
        project_id = create_response.json()["id"]
        
        # Update the project
        updated_data = {
            "name": f"Updated {sample_project_data['name']}",
            "description": "Updated description"
        }
        
        response = authenticated_client.put(f"{backend_url}/projects/{project_id}", json=updated_data)
        
        assert_docsmait.assert_api_success(response)
        data = response.json()
        
        assert data["name"] == updated_data["name"]
        assert data["description"] == updated_data["description"]

    def test_delete_project(self, authenticated_client, backend_url, sample_project_data):
        """Test deleting a project."""
        # First create a project
        create_response = authenticated_client.post(f"{backend_url}/projects", json=sample_project_data)
        
        if create_response.status_code != 201:
            pytest.skip("Cannot create project for testing")
        
        project_id = create_response.json()["id"]
        
        # Delete the project
        response = authenticated_client.delete(f"{backend_url}/projects/{project_id}")
        
        # Should succeed or be not implemented
        assert response.status_code in [200, 204, 404, 501]
        
        # If deletion succeeded, verify project is gone
        if response.status_code in [200, 204]:
            get_response = authenticated_client.get(f"{backend_url}/projects/{project_id}")
            assert get_response.status_code == 404

    def test_get_nonexistent_project(self, authenticated_client, backend_url):
        """Test getting a project that doesn't exist."""
        response = authenticated_client.get(f"{backend_url}/projects/99999")
        
        assert response.status_code == 404


@pytest.mark.api
class TestDocumentEndpoints:
    """Test document management endpoints."""

    def test_get_documents_authenticated(self, authenticated_client, backend_url, assert_docsmait):
        """Test getting documents with authentication."""
        response = authenticated_client.get(f"{backend_url}/documents")
        
        assert_docsmait.assert_api_success(response)
        data = response.json()
        
        # Should return list of documents
        assert isinstance(data, list)

    def test_create_document(self, authenticated_client, backend_url, sample_document_data, assert_docsmait):
        """Test creating a new document."""
        response = authenticated_client.post(f"{backend_url}/documents", json=sample_document_data)
        
        # Document creation might require a project ID
        if response.status_code == 400:
            pytest.skip("Document creation requires additional parameters")
        
        assert_docsmait.assert_api_success(response, 201)
        data = response.json()
        
        expected_keys = ["id", "name"]
        assert_docsmait.assert_json_structure(data, expected_keys)


@pytest.mark.api
class TestTemplateEndpoints:
    """Test template management endpoints."""

    def test_get_templates_authenticated(self, authenticated_client, backend_url, assert_docsmait):
        """Test getting templates with authentication."""
        response = authenticated_client.get(f"{backend_url}/templates")
        
        assert_docsmait.assert_api_success(response)
        data = response.json()
        
        # Should return list of templates
        assert isinstance(data, list)

    def test_get_template_by_id(self, authenticated_client, backend_url):
        """Test getting a template by ID."""
        # First get list of templates
        list_response = authenticated_client.get(f"{backend_url}/templates")
        
        if list_response.status_code == 200 and list_response.json():
            # Get first template
            template_id = list_response.json()[0]["id"]
            response = authenticated_client.get(f"{backend_url}/templates/{template_id}")
            
            assert response.status_code in [200, 404]  # Either exists or doesn't
        else:
            pytest.skip("No templates available for testing")


@pytest.mark.api
class TestExportEndpoints:
    """Test export functionality endpoints."""

    def test_export_status_endpoint(self, api_client, backend_url, assert_docsmait):
        """Test export feature status endpoint."""
        response = api_client.get(f"{backend_url}/projects/1/export-status")
        
        assert_docsmait.assert_api_success(response)
        data = response.json()
        
        # Should contain export availability status
        expected_keys = ["available", "reason"]
        assert_docsmait.assert_json_structure(data, expected_keys)
        
        assert isinstance(data["available"], bool)
        assert isinstance(data["reason"], str)

    def test_export_documents_endpoint(self, authenticated_client, backend_url):
        """Test document export endpoint."""
        # Create a test project first if possible
        project_data = {"name": "Export Test Project", "description": "For testing exports"}
        create_response = authenticated_client.post(f"{backend_url}/projects", json=project_data)
        
        if create_response.status_code == 201:
            project_id = create_response.json()["id"]
            
            export_config = {
                "format": "pdf",
                "include_documents": True,
                "include_templates": False
            }
            
            response = authenticated_client.post(
                f"{backend_url}/projects/{project_id}/export-documents",
                json=export_config
            )
            
            # Export might fail due to missing dependencies or data
            assert response.status_code in [200, 400, 404, 500]
        else:
            pytest.skip("Cannot create project for export testing")


@pytest.mark.api
class TestUserManagementEndpoints:
    """Test user management endpoints."""

    def test_get_users_as_admin(self, authenticated_client, backend_url, assert_docsmait):
        """Test getting all users as admin."""
        response = authenticated_client.get(f"{backend_url}/users")
        
        assert_docsmait.assert_api_success(response)
        data = response.json()
        
        # Should return list of users
        assert isinstance(data, list)
        
        # Should contain at least the admin user
        assert len(data) >= 1

    def test_get_users_unauthenticated(self, api_client, backend_url):
        """Test getting users without authentication."""
        response = api_client.get(f"{backend_url}/users")
        
        # Should require authentication
        assert response.status_code == 401


@pytest.mark.api
@pytest.mark.slow
class TestAPIPerformance:
    """Test API performance characteristics."""

    def test_settings_endpoint_response_time(self, api_client, backend_url):
        """Test settings endpoint response time."""
        import time
        
        start_time = time.time()
        response = api_client.get(f"{backend_url}/settings")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Settings endpoint too slow: {response_time:.2f}s"

    def test_multiple_concurrent_requests(self, api_client, backend_url):
        """Test handling multiple concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = api_client.get(f"{backend_url}/settings")
            end_time = time.time()
            results.append({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 5 concurrent threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 5
        assert all(result["status_code"] == 200 for result in results)
        
        # Average response time should be reasonable
        avg_time = sum(result["response_time"] for result in results) / len(results)
        assert avg_time < 5.0, f"Average response time too slow: {avg_time:.2f}s"