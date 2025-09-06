#!/usr/bin/env python3
"""
Test script to verify knowledge base collection fallback functionality
"""
import sys
import os

# Add the backend app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))

def test_kb_fallback():
    """Test knowledge base fallback functionality"""
    try:
        from kb_service_pg import kb_service
        from config import config
        
        print("🧪 Testing Knowledge Base Collection Fallback Logic")
        print("=" * 60)
        
        # Test 1: Store data in non-existent collection
        print("\n1️⃣ Testing: Store data in non-existent collection")
        non_existent_collection = "test_nonexistent_collection"
        
        result = kb_service.add_text_to_collection(
            collection_name=non_existent_collection,
            text_content="This is test content for fallback testing. It should be stored in the default collection if the specified collection doesn't exist.",
            filename="test_fallback_document.txt",
            metadata={"test": True, "fallback_test": "store_operation"}
        )
        
        print(f"   Result: {result.get('success', False)}")
        print(f"   Message: {result.get('message', result.get('error', 'No message'))}")
        
        # Test 2: Query from non-existent collection
        print("\n2️⃣ Testing: Query from non-existent collection")
        non_existent_query_collection = "test_query_nonexistent"
        
        query_result = kb_service.search_collection(
            collection_name=non_existent_query_collection,
            query="test content fallback",
            limit=3
        )
        
        print(f"   Found {len(query_result)} results")
        if query_result:
            print(f"   First result collection: {query_result[0].get('filename', 'Unknown')}")
        
        # Test 3: RAG query from non-existent collection
        print("\n3️⃣ Testing: RAG query from non-existent collection")
        rag_result = kb_service.query_knowledge_base(
            message="What is the test content about?",
            collection_name="another_nonexistent_collection"
        )
        
        print(f"   RAG Response length: {len(rag_result.get('response', ''))}")
        print(f"   Sources found: {len(rag_result.get('sources', []))}")
        
        # Test 4: Check default collection creation
        print("\n4️⃣ Testing: Check default collection creation")
        collections = kb_service.list_collections()
        default_collection = config.DEFAULT_COLLECTION_NAME
        
        has_default = any(c['name'] == default_collection for c in collections)
        print(f"   Default collection '{default_collection}' exists: {has_default}")
        
        if has_default:
            default_info = next(c for c in collections if c['name'] == default_collection)
            print(f"   Default collection has {default_info['document_count']} documents")
        
        # Test 5: Check fallback helper method
        print("\n5️⃣ Testing: Internal fallback helper method")
        test_collection = "test_helper_method_collection"
        actual_collection = kb_service._ensure_collection_exists_or_get_default(test_collection)
        print(f"   Requested: '{test_collection}'")
        print(f"   Actual: '{actual_collection}'")
        print(f"   Fallback occurred: {test_collection != actual_collection}")
        
        print("\n" + "=" * 60)
        print("✅ Knowledge Base Fallback Testing Complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_kb_fallback()
    sys.exit(0 if success else 1)