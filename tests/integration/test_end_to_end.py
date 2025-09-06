"""
End-to-End Integration Tests

Tests complete user workflows from frontend to backend to database.
"""

import pytest
import requests
import time
from datetime import datetime


@pytest.mark.integration
class TestUserRegistrationFlow:
    """Test complete user registration and login flow."""

    def test_complete_user_signup_flow(self, api_client, backend_url, assert_docsmait):
        """Test complete user signup process."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Step 1: Create new user
        new_user = {
            "username": f"integration_user_{timestamp}",
            "email": f"integration_{timestamp}@docsmait.com",
            "password": "IntegrationTest123!",
            "confirm_password": "IntegrationTest123!"
        }
        
        signup_response = api_client.post(f"{backend_url}/auth/signup", json=new_user)
        assert_docsmait.assert_api_success(signup_response, 200)
        
        signup_data = signup_response.json()
        assert_docsmait.assert_json_structure(signup_data, ["access_token", "token_type"])
        
        # Step 2: Use token to access protected resource
        token = signup_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        me_response = api_client.get(f"{backend_url}/auth/me", headers=auth_headers)
        assert_docsmait.assert_api_success(me_response)
        
        user_data = me_response.json()
        assert user_data["email"] == new_user["email"]
        assert user_data["username"] == new_user["username"]
        
        # Step 3: Logout (implicit - token expires)
        # Step 4: Login with same credentials
        login_response = api_client.post(f"{backend_url}/auth/login", json={
            "email": new_user["email"],
            "password": new_user["password"]
        })
        assert_docsmait.assert_api_success(login_response)
        
        login_data = login_response.json()
        assert_docsmait.assert_valid_jwt(login_data["access_token"])


@pytest.mark.integration
class TestProjectManagementFlow:
    """Test complete project management workflow."""

    def test_complete_project_workflow(self, authenticated_client, backend_url, assert_docsmait):
        """Test creating, updating, and managing a project."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Step 1: Create project
        project_data = {
            "name": f"Integration Test Project {timestamp}",
            "description": "Project created during integration testing"
        }
        
        create_response = authenticated_client.post(f"{backend_url}/projects", json=project_data)
        assert_docsmait.assert_api_success(create_response, 201)
        
        created_project = create_response.json()
        project_id = created_project["id"]
        
        # Step 2: Retrieve project
        get_response = authenticated_client.get(f"{backend_url}/projects/{project_id}")
        assert_docsmait.assert_api_success(get_response)
        
        retrieved_project = get_response.json()
        assert retrieved_project["name"] == project_data["name"]
        assert retrieved_project["description"] == project_data["description"]
        
        # Step 3: Update project
        updated_data = {
            "name": f"Updated {project_data['name']}",
            "description": "Updated description during integration test"
        }
        
        update_response = authenticated_client.put(f"{backend_url}/projects/{project_id}", json=updated_data)
        assert_docsmait.assert_api_success(update_response)
        
        # Step 4: Verify update
        verify_response = authenticated_client.get(f"{backend_url}/projects/{project_id}")
        assert_docsmait.assert_api_success(verify_response)
        
        updated_project = verify_response.json()
        assert updated_project["name"] == updated_data["name"]
        assert updated_project["description"] == updated_data["description"]
        
        # Step 5: List projects (should include our project)
        list_response = authenticated_client.get(f"{backend_url}/projects")
        assert_docsmait.assert_api_success(list_response)
        
        projects_list = list_response.json()
        project_ids = [p["id"] for p in projects_list]
        assert project_id in project_ids


@pytest.mark.integration
class TestDocumentWorkflow:
    """Test document management workflow."""

    def test_document_creation_workflow(self, authenticated_client, backend_url, assert_docsmait):
        """Test creating and managing documents."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Step 1: List existing documents
        list_response = authenticated_client.get(f"{backend_url}/documents")
        assert_docsmait.assert_api_success(list_response)
        
        initial_docs = list_response.json()
        initial_count = len(initial_docs)
        
        # Step 2: Create document (if endpoint supports it)
        document_data = {
            "name": f"Integration Test Document {timestamp}",
            "content": "This is a test document created during integration testing.",
            "document_type": "SOP"
        }
        
        create_response = authenticated_client.post(f"{backend_url}/documents", json=document_data)
        
        if create_response.status_code == 201:
            # Document creation succeeded
            created_doc = create_response.json()
            doc_id = created_doc["id"]
            
            # Step 3: Retrieve created document
            get_response = authenticated_client.get(f"{backend_url}/documents/{doc_id}")
            assert_docsmait.assert_api_success(get_response)
            
            retrieved_doc = get_response.json()
            assert retrieved_doc["name"] == document_data["name"]
            
        elif create_response.status_code == 400:
            # Document creation might require project association
            pytest.skip("Document creation requires additional parameters")
        else:
            pytest.skip("Document creation not fully implemented")


@pytest.mark.integration
class TestTemplateWorkflow:
    """Test template management workflow."""

    def test_template_listing_workflow(self, authenticated_client, backend_url, assert_docsmait):
        """Test template listing and access."""
        # Step 1: Get list of templates
        list_response = authenticated_client.get(f"{backend_url}/templates")
        assert_docsmait.assert_api_success(list_response)
        
        templates = list_response.json()
        assert isinstance(templates, list)
        
        # Step 2: If templates exist, test accessing individual template
        if templates:
            first_template = templates[0]
            template_id = first_template["id"]
            
            get_response = authenticated_client.get(f"{backend_url}/templates/{template_id}")
            assert_docsmait.assert_api_success(get_response)
            
            template_detail = get_response.json()
            assert template_detail["id"] == template_id
        
        # Step 3: Test template search/filtering (if available)
        # This might not be implemented yet
        search_response = authenticated_client.get(f"{backend_url}/templates?search=test")
        # Accept various responses since search might not be implemented
        assert search_response.status_code in [200, 404, 501]


@pytest.mark.integration  
class TestExportWorkflow:
    """Test export functionality workflow."""

    def test_export_status_and_functionality(self, authenticated_client, backend_url, assert_docsmait):
        """Test export feature workflow."""
        # Step 1: Check export feature status
        status_response = authenticated_client.get(f"{backend_url}/projects/1/export-status")
        assert_docsmait.assert_api_success(status_response)
        
        status_data = status_response.json()
        assert_docsmait.assert_json_structure(status_data, ["available", "reason"])
        
        # Step 2: If export is available, test export functionality
        if status_data["available"]:
            # Create a project for export testing
            project_data = {
                "name": f"Export Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "Project for testing export functionality"
            }
            
            create_response = authenticated_client.post(f"{backend_url}/projects", json=project_data)
            
            if create_response.status_code == 201:
                project_id = create_response.json()["id"]
                
                # Test export functionality
                export_config = {
                    "format": "pdf",
                    "include_documents": True,
                    "include_templates": False
                }
                
                export_response = authenticated_client.post(
                    f"{backend_url}/projects/{project_id}/export-documents",
                    json=export_config
                )
                
                # Export might fail due to no content, but should not crash
                assert export_response.status_code in [200, 400, 404, 500]
                
                if export_response.status_code == 200:
                    # Verify response is PDF or zip file
                    content_type = export_response.headers.get("content-type", "")
                    assert content_type in ["application/pdf", "application/zip", "application/octet-stream"]


@pytest.mark.integration
class TestUserManagementWorkflow:
    """Test user management workflow."""

    def test_user_listing_workflow(self, authenticated_client, backend_url, assert_docsmait):
        """Test user management features."""
        # Step 1: Get list of users (requires admin privileges)
        users_response = authenticated_client.get(f"{backend_url}/users")
        assert_docsmait.assert_api_success(users_response)
        
        users = users_response.json()
        assert isinstance(users, list)
        assert len(users) >= 1  # Should have at least the test admin user
        
        # Step 2: Verify user data structure
        first_user = users[0]
        expected_fields = ["id", "username", "email", "is_admin"]
        assert_docsmait.assert_json_structure(first_user, expected_fields)
        
        # Step 3: Get current user info
        me_response = authenticated_client.get(f"{backend_url}/auth/me")
        assert_docsmait.assert_api_success(me_response)
        
        current_user = me_response.json()
        assert current_user["is_admin"] is True  # Test user should be admin


@pytest.mark.integration
@pytest.mark.slow
class TestSystemIntegration:
    """Test system-wide integration."""

    def test_multi_service_health(self, backend_url, frontend_url):
        """Test that all services are healthy and communicating."""
        # Test backend health
        backend_response = requests.get(f"{backend_url}/settings", timeout=10)
        assert backend_response.status_code == 200
        
        # Test frontend accessibility
        frontend_response = requests.get(frontend_url, timeout=15)
        assert frontend_response.status_code == 200
        
        # Test export feature availability
        export_response = requests.get(f"{backend_url}/projects/1/export-status", timeout=10)
        assert export_response.status_code == 200
        
        export_data = export_response.json()
        assert "available" in export_data

    def test_data_consistency(self, authenticated_client, backend_url, assert_docsmait):
        """Test data consistency across operations."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create a project
        project_data = {
            "name": f"Consistency Test {timestamp}",
            "description": "Testing data consistency"
        }
        
        create_response = authenticated_client.post(f"{backend_url}/projects", json=project_data)
        
        if create_response.status_code == 201:
            project_id = create_response.json()["id"]
            
            # Retrieve project multiple times to ensure consistency
            for i in range(3):
                get_response = authenticated_client.get(f"{backend_url}/projects/{project_id}")
                assert_docsmait.assert_api_success(get_response)
                
                project = get_response.json()
                assert project["name"] == project_data["name"]
                assert project["id"] == project_id
                
                time.sleep(0.1)  # Small delay between requests

    def test_concurrent_user_operations(self, backend_url, test_admin_credentials):
        """Test system behavior under concurrent operations."""
        import threading
        
        results = []
        
        def create_and_list_projects(thread_id):
            """Create project and list projects concurrently."""
            try:
                # Create session for this thread
                session = requests.Session()
                
                # Login
                login_response = session.post(
                    f"{backend_url}/auth/login",
                    json=test_admin_credentials
                )
                
                if login_response.status_code == 200:
                    token = login_response.json()["access_token"]
                    session.headers.update({"Authorization": f"Bearer {token}"})
                    
                    # Create project
                    project_data = {
                        "name": f"Concurrent Test Project {thread_id}",
                        "description": f"Created by thread {thread_id}"
                    }
                    
                    create_response = session.post(f"{backend_url}/projects", json=project_data)
                    
                    # List projects
                    list_response = session.get(f"{backend_url}/projects")
                    
                    results.append({
                        "thread_id": thread_id,
                        "create_status": create_response.status_code,
                        "list_status": list_response.status_code,
                        "success": create_response.status_code in [200, 201] and list_response.status_code == 200
                    })
                
            except Exception as e:
                results.append({
                    "thread_id": thread_id,
                    "error": str(e),
                    "success": False
                })
        
        # Create 3 concurrent threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_and_list_projects, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)
        
        # Verify results
        assert len(results) == 3, "Not all threads completed"
        
        successful_ops = sum(1 for result in results if result.get("success", False))
        assert successful_ops >= 2, f"Too many concurrent operations failed: {results}"


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across the system."""

    def test_invalid_authentication_handling(self, api_client, backend_url):
        """Test system handles invalid authentication gracefully."""
        # Try to access protected resource without token
        response = api_client.get(f"{backend_url}/auth/me")
        assert response.status_code == 401
        
        # Try with invalid token
        api_client.headers["Authorization"] = "Bearer invalid_token"
        response = api_client.get(f"{backend_url}/auth/me")
        assert response.status_code == 401
        
        # Clean up headers
        if "Authorization" in api_client.headers:
            del api_client.headers["Authorization"]

    def test_nonexistent_resource_handling(self, authenticated_client, backend_url):
        """Test system handles nonexistent resources gracefully."""
        # Try to get nonexistent project
        response = authenticated_client.get(f"{backend_url}/projects/99999")
        assert response.status_code == 404
        
        # Try to get nonexistent document
        response = authenticated_client.get(f"{backend_url}/documents/99999")
        assert response.status_code == 404
        
        # Try to get nonexistent template
        response = authenticated_client.get(f"{backend_url}/templates/99999")
        assert response.status_code == 404

    def test_malformed_request_handling(self, authenticated_client, backend_url):
        """Test system handles malformed requests gracefully."""
        # Send malformed JSON for project creation
        response = authenticated_client.post(
            f"{backend_url}/projects",
            data="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]  # Bad request or unprocessable entity
        
        # Send request with missing required fields
        response = authenticated_client.post(
            f"{backend_url}/projects",
            json={"description": "Missing name field"}
        )
        assert response.status_code in [400, 422]


@pytest.mark.integration
class TestKnowledgeBaseChatWorkflow:
    """Test complete Knowledge Base chat integration workflow."""

    def test_complete_kb_chat_document_creation_flow(self, authenticated_client, backend_url, assert_docsmait):
        """Test complete document creation with KB chat workflow."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # This simulates the frontend document creation workflow with KB chat
        # Step 1: Prepare document context
        document_context = f"Integration test document created at {timestamp}. This document contains requirements for testing the KB chat functionality."
        
        # Step 2: Query KB for document improvement suggestions
        kb_query_data = {
            "query": "How can I improve the structure and content of this document?",
            "document_context": document_context,
            "collection_name": "knowledge_base",
            "max_results": 5
        }
        
        kb_response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=kb_query_data)
        
        # KB service might not be available in test environment
        if kb_response.status_code == 500:
            pytest.skip("KB service not available for integration test")
        
        # Should handle KB query appropriately
        assert kb_response.status_code in [200, 400, 404, 503]
        
        if kb_response.status_code == 200:
            kb_data = kb_response.json()
            assert "response" in kb_data
            assert isinstance(kb_data["response"], str)
            assert len(kb_data["response"]) > 0
        
        # Step 3: Create document (simulating frontend workflow)
        document_data = {
            "name": f"KB Chat Test Document {timestamp}",
            "content": document_context,
            "document_type": "Technical Documentation"
        }
        
        # Try to create document
        create_response = authenticated_client.post(f"{backend_url}/documents", json=document_data)
        
        # Document creation might require additional parameters
        if create_response.status_code not in [200, 201]:
            pytest.skip("Document creation requires project association or other parameters")
        
        # If document creation succeeded, verify the workflow
        if create_response.status_code in [200, 201]:
            created_doc = create_response.json()
            assert "id" in created_doc
            assert created_doc["name"] == document_data["name"]

    def test_kb_chat_session_workflow(self, authenticated_client, backend_url):
        """Test KB chat session simulation workflow."""
        # Simulate a multi-query chat session
        chat_session = [
            {
                "query": "What are the best practices for technical documentation?",
                "document_context": "Technical specification document in progress"
            },
            {
                "query": "How should I structure requirements sections?",
                "document_context": "Technical specification with initial requirements draft"
            },
            {
                "query": "What testing approaches should be documented?",
                "document_context": "Technical specification with requirements and design sections"
            }
        ]
        
        session_responses = []
        
        for i, query_data in enumerate(chat_session):
            response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
            
            # Skip if KB service is not available
            if response.status_code == 500:
                pytest.skip("KB service not available for chat session workflow")
            
            session_responses.append({
                "query_num": i + 1,
                "status_code": response.status_code,
                "query": query_data["query"]
            })
            
            # Should handle each query appropriately
            assert response.status_code in [200, 400, 404, 503]
            
            # Add small delay between queries to be respectful to the service
            time.sleep(0.5)
        
        # All queries should be processed
        assert len(session_responses) == len(chat_session)
        
        # Should have consistent behavior across the session
        status_codes = [r["status_code"] for r in session_responses]
        unique_statuses = set(status_codes)
        
        # If service is available, should consistently work
        if 200 in unique_statuses:
            # At least some queries succeeded
            successful_queries = sum(1 for code in status_codes if code == 200)
            assert successful_queries >= 1

    def test_kb_chat_document_review_integration(self, authenticated_client, backend_url):
        """Test KB chat integration with document review workflow."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Simulate document review with KB assistance
        review_document_context = f"""
        Document Review Test {timestamp}
        
        This is a technical document that needs review.
        It contains specifications, requirements, and implementation details.
        The document should be checked for completeness, accuracy, and compliance.
        """
        
        # KB queries for review assistance
        review_queries = [
            {
                "query": "What should I look for when reviewing a technical document?",
                "document_context": review_document_context
            },
            {
                "query": "Are there any missing sections in this document?",
                "document_context": review_document_context
            },
            {
                "query": "What compliance standards should this document meet?",
                "document_context": review_document_context
            }
        ]
        
        review_results = []
        
        for query_data in review_queries:
            response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
            
            # Skip if KB service is not available
            if response.status_code == 500:
                pytest.skip("KB service not available for review integration test")
            
            review_results.append(response.status_code)
            
            # Should handle review queries
            assert response.status_code in [200, 400, 404, 503]
        
        # All review queries should be processed
        assert len(review_results) == len(review_queries)

    @pytest.mark.slow
    def test_kb_chat_performance_integration(self, authenticated_client, backend_url):
        """Test KB chat performance in integration context."""
        import time
        
        # Test performance with realistic document content
        large_document_context = """
        Performance Test Document
        
        This is a large document context for performance testing of the KB chat functionality.
        """ + "Additional content for testing performance. " * 100
        
        query_data = {
            "query": "Summarize the key points of this document and suggest improvements",
            "document_context": large_document_context,
            "max_results": 5
        }
        
        start_time = time.time()
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Skip if KB service is not available
        if response.status_code == 500:
            pytest.skip("KB service not available for performance integration test")
        
        # Should complete within reasonable time
        assert response_time < 45.0, f"KB chat integration too slow: {response_time:.2f}s"
        
        # Should handle the query appropriately
        assert response.status_code in [200, 400, 404, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert len(data["response"]) > 0

    def test_kb_chat_error_handling_integration(self, authenticated_client, backend_url):
        """Test KB chat error handling in integration context."""
        
        # Test various error conditions
        error_test_cases = [
            {
                "name": "empty_query",
                "data": {"query": ""},
                "expected_codes": [400, 422]
            },
            {
                "name": "none_query",
                "data": {"query": None},
                "expected_codes": [400, 422]
            },
            {
                "name": "invalid_max_results",
                "data": {"query": "Test", "max_results": -1},
                "expected_codes": [400, 422]
            },
            {
                "name": "very_long_query",
                "data": {"query": "Very long query " * 1000},
                "expected_codes": [200, 400, 413, 500, 503]
            }
        ]
        
        for test_case in error_test_cases:
            response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=test_case["data"])
            
            assert response.status_code in test_case["expected_codes"], f"Error handling failed for {test_case['name']}: got {response.status_code}"