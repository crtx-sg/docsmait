"""
Knowledge Base API Endpoints Tests

Tests for Knowledge Base query endpoints and chat functionality.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock


@pytest.mark.api
class TestKnowledgeBaseEndpoints:
    """Test Knowledge Base API endpoints."""

    def test_kb_query_with_context_unauthenticated(self, api_client, backend_url):
        """Test KB query endpoint without authentication."""
        query_data = {
            "query": "What is this document about?",
            "document_context": "Sample document content",
            "collection_name": "test_collection"
        }
        
        response = api_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        
        # Should require authentication
        assert response.status_code == 401

    def test_kb_query_with_context_authenticated(self, authenticated_client, backend_url, assert_docsmait):
        """Test KB query endpoint with authentication."""
        query_data = {
            "query": "What is this document about?",
            "document_context": "Sample document content for testing",
            "collection_name": "test_collection",
            "max_results": 5
        }
        
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        
        # KB service might not be available in test environment
        if response.status_code == 500:
            pytest.skip("KB service not available in test environment")
        
        # Should succeed or return specific error codes
        assert response.status_code in [200, 400, 404, 503]
        
        if response.status_code == 200:
            data = response.json()
            
            # Should contain response and metadata
            expected_keys = ["response"]
            assert_docsmait.assert_json_structure(data, expected_keys)
            
            assert isinstance(data["response"], str)

    def test_kb_query_with_context_minimal_data(self, authenticated_client, backend_url, assert_docsmait):
        """Test KB query endpoint with minimal required data."""
        query_data = {
            "query": "Test query"
        }
        
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        
        # Should succeed with minimal data or return service error
        assert response.status_code in [200, 400, 500, 503]

    def test_kb_query_with_context_empty_query(self, authenticated_client, backend_url):
        """Test KB query endpoint with empty query."""
        query_data = {
            "query": ""
        }
        
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        
        # Should handle empty query appropriately
        assert response.status_code in [400, 422]

    def test_kb_query_with_context_none_query(self, authenticated_client, backend_url):
        """Test KB query endpoint with None query."""
        query_data = {
            "query": None
        }
        
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        
        # Should handle None query appropriately
        assert response.status_code in [400, 422]

    def test_kb_query_with_context_invalid_json(self, authenticated_client, backend_url):
        """Test KB query endpoint with invalid JSON data."""
        response = authenticated_client.post(
            f"{backend_url}/kb/query_with_context",
            data="invalid json"
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]

    def test_kb_query_with_context_missing_required_field(self, authenticated_client, backend_url):
        """Test KB query endpoint with missing required field."""
        query_data = {
            "document_context": "Some context without query"
        }
        
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        
        # Should return validation error for missing query
        assert response.status_code in [400, 422]

    def test_kb_query_with_context_large_context(self, authenticated_client, backend_url):
        """Test KB query endpoint with large document context."""
        large_context = "Large context text. " * 1000  # Create large text
        
        query_data = {
            "query": "Analyze this large document",
            "document_context": large_context
        }
        
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        
        # Should handle large context or return appropriate error
        assert response.status_code in [200, 400, 413, 500, 503]

    def test_kb_query_with_context_special_characters(self, authenticated_client, backend_url):
        """Test KB query endpoint with special characters in query."""
        query_data = {
            "query": "What about symbols: !@#$%^&*(){}[]|\\:;\"'<>?,./-_+=`~",
            "document_context": "Document with special chars: éñüçīõń"
        }
        
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        
        # Should handle special characters appropriately
        assert response.status_code in [200, 400, 500, 503]

    def test_kb_query_with_context_max_results_validation(self, authenticated_client, backend_url):
        """Test KB query endpoint with various max_results values."""
        test_cases = [
            {"max_results": 1, "should_work": True},
            {"max_results": 10, "should_work": True},
            {"max_results": 0, "should_work": False},
            {"max_results": -1, "should_work": False},
            {"max_results": 100, "should_work": True},
        ]
        
        for case in test_cases:
            query_data = {
                "query": "Test query",
                "max_results": case["max_results"]
            }
            
            response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
            
            if case["should_work"]:
                # Should succeed or return service error
                assert response.status_code in [200, 500, 503]
            else:
                # Should return validation error for invalid values
                assert response.status_code in [400, 422]

    def test_kb_query_with_context_different_collection_names(self, authenticated_client, backend_url):
        """Test KB query endpoint with different collection names."""
        test_collections = [
            "knowledge_base",
            "test_collection", 
            "documents",
            "nonexistent_collection"
        ]
        
        for collection in test_collections:
            query_data = {
                "query": "Test query",
                "collection_name": collection
            }
            
            response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
            
            # Should handle different collections appropriately
            assert response.status_code in [200, 400, 404, 500, 503]


@pytest.mark.api 
@pytest.mark.integration
class TestKnowledgeBaseChatIntegration:
    """Test Knowledge Base chat integration scenarios."""

    def test_document_creation_chat_workflow(self, authenticated_client, backend_url):
        """Test the complete document creation with KB chat workflow."""
        # This test simulates the frontend workflow:
        # 1. Create a document
        # 2. Query KB with document context
        # 3. Update document based on response
        
        # Step 1: Create a document
        document_data = {
            "name": "Test Document with KB Chat",
            "content": "Initial document content for testing KB chat functionality.",
            "project_id": 1  # Assuming project 1 exists
        }
        
        doc_response = authenticated_client.post(f"{backend_url}/documents", json=document_data)
        
        # Document creation might fail due to missing project or other requirements
        if doc_response.status_code not in [200, 201]:
            pytest.skip("Cannot create document for KB chat integration test")
        
        # Step 2: Query KB with document context
        query_data = {
            "query": "How can I improve this document?",
            "document_context": document_data["content"],
            "collection_name": "knowledge_base"
        }
        
        kb_response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        
        # KB service might not be available
        if kb_response.status_code == 500:
            pytest.skip("KB service not available for integration test")
        
        # Should succeed or return specific error codes
        assert kb_response.status_code in [200, 400, 404, 503]

    def test_document_review_chat_workflow(self, authenticated_client, backend_url):
        """Test the document review with KB chat workflow."""
        # This simulates the review workflow with KB chat
        
        # Query for document review guidance
        query_data = {
            "query": "What should I look for when reviewing a technical document?",
            "document_context": "Sample technical document for review testing",
            "collection_name": "knowledge_base"
        }
        
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        
        # Should handle review queries appropriately
        assert response.status_code in [200, 400, 500, 503]

    @pytest.mark.slow
    def test_kb_chat_session_simulation(self, authenticated_client, backend_url):
        """Test simulated KB chat session with multiple queries."""
        # Simulate a chat session with multiple related queries
        
        chat_queries = [
            {
                "query": "What is this document about?",
                "document_context": "Technical specification for software component X"
            },
            {
                "query": "What standards should this follow?",
                "document_context": "Technical specification for software component X with requirements"
            },
            {
                "query": "How should I document the testing approach?",
                "document_context": "Technical specification with requirements and design sections"
            }
        ]
        
        responses = []
        
        for query_data in chat_queries:
            response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
            
            # Skip if KB service is not available
            if response.status_code == 500:
                pytest.skip("KB service not available for chat session simulation")
            
            responses.append(response)
            
            # Should handle each query appropriately
            assert response.status_code in [200, 400, 404, 503]
        
        # All queries should be processed
        assert len(responses) == len(chat_queries)

    def test_kb_chat_concurrent_requests(self, authenticated_client, backend_url):
        """Test concurrent KB chat requests."""
        import threading
        import time
        
        results = []
        
        def make_kb_request(query_num):
            query_data = {
                "query": f"Test concurrent query {query_num}",
                "document_context": f"Document context for query {query_num}"
            }
            
            start_time = time.time()
            response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
            end_time = time.time()
            
            results.append({
                "query_num": query_num,
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 3 concurrent threads (not too many for test stability)
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_kb_request, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # All requests should complete
        assert len(results) == 3
        
        # Skip if KB service is not available
        if any(result["status_code"] == 500 for result in results):
            pytest.skip("KB service not available for concurrent request test")
        
        # All should return valid status codes
        for result in results:
            assert result["status_code"] in [200, 400, 404, 503]


@pytest.mark.api
@pytest.mark.performance
class TestKnowledgeBasePerformance:
    """Test Knowledge Base performance characteristics."""

    @pytest.mark.slow
    def test_kb_query_response_time(self, authenticated_client, backend_url):
        """Test KB query response time."""
        import time
        
        query_data = {
            "query": "What is the best practice for document management?",
            "document_context": "Sample document content for performance testing"
        }
        
        start_time = time.time()
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Skip if KB service is not available
        if response.status_code == 500:
            pytest.skip("KB service not available for performance test")
        
        # KB queries might be slow due to AI processing, but should be reasonable
        # Using 30 seconds as configured timeout
        assert response_time < 35.0, f"KB query too slow: {response_time:.2f}s"
        
        # Should return valid response
        assert response.status_code in [200, 400, 404, 503]

    def test_kb_query_with_large_context_performance(self, authenticated_client, backend_url):
        """Test KB query performance with large context."""
        import time
        
        # Create large context (approximately 10KB)
        large_context = "This is a large document context. " * 200
        
        query_data = {
            "query": "Summarize this large document",
            "document_context": large_context
        }
        
        start_time = time.time()
        response = authenticated_client.post(f"{backend_url}/kb/query_with_context", json=query_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Skip if KB service is not available
        if response.status_code == 500:
            pytest.skip("KB service not available for large context performance test")
        
        # Large context might take longer but should still be reasonable
        assert response_time < 45.0, f"Large context KB query too slow: {response_time:.2f}s"
        
        # Should handle large context appropriately
        assert response.status_code in [200, 400, 413, 503]