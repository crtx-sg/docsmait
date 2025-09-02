#!/usr/bin/env python3
"""
Performance Test Script for Knowledge Base RAG Pipeline
"""

import requests
import time
import json
import os

# Use environment variables for configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
TEST_USERNAME = os.getenv("TEST_USERNAME", "admin")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "admin123")
DEFAULT_COLLECTION = os.getenv("DEFAULT_COLLECTION_NAME", "knowledge_base")

def get_auth_token():
    """Get authentication token"""
    response = requests.post(f"{BACKEND_URL}/auth/login", json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Authentication failed: {response.status_code}")
        return None

def test_performance():
    """Test RAG pipeline performance"""
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test queries with different complexity
    test_queries = [
        "What is this collection about?",
        "Explain the main topics covered in the documents",
        "What are the key requirements mentioned?",
        "Summarize the important points from the uploaded files"
    ]
    
    print("🚀 Testing RAG Pipeline Performance")
    print("=" * 50)
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}/4: {query}")
        
        # Measure total request time
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/kb/chat",
                json={
                    "message": query,
                    "collection_name": DEFAULT_COLLECTION
                },
                headers=headers,
                timeout=60
            )
            
            request_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract performance metrics
                perf = data.get("performance", {})
                
                result = {
                    "query": query,
                    "total_request_time_ms": request_time,
                    "embedding_time_ms": perf.get("query_embedding_time_ms", 0),
                    "retrieval_time_ms": perf.get("retrieval_time_ms", 0),
                    "llm_time_ms": perf.get("llm_response_time_ms", 0),
                    "backend_total_ms": perf.get("total_time_ms", 0),
                    "chunks_retrieved": perf.get("chunks_retrieved", 0),
                    "model_used": perf.get("model_used", "unknown"),
                    "response_length": len(data.get("response", "")),
                    "sources_count": len(data.get("sources", []))
                }
                
                results.append(result)
                
                # Display results
                print(f"   ⏱️  Total Request: {request_time}ms")
                print(f"   🔍 Embedding: {result['embedding_time_ms']}ms")
                print(f"   📚 Retrieval: {result['retrieval_time_ms']}ms ({result['chunks_retrieved']} chunks)")
                print(f"   🤖 LLM ({result['model_used']}): {result['llm_time_ms']}ms")
                print(f"   📝 Response: {result['response_length']} chars, {result['sources_count']} sources")
                
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    # Calculate averages
    if results:
        print("\n📊 Performance Summary")
        print("=" * 50)
        
        avg_total = sum(r["total_request_time_ms"] for r in results) / len(results)
        avg_embedding = sum(r["embedding_time_ms"] for r in results) / len(results)
        avg_retrieval = sum(r["retrieval_time_ms"] for r in results) / len(results)
        avg_llm = sum(r["llm_time_ms"] for r in results) / len(results)
        
        print(f"Average Total Request Time: {avg_total:.1f}ms")
        print(f"Average Embedding Time: {avg_embedding:.1f}ms ({avg_embedding/avg_total*100:.1f}%)")
        print(f"Average Retrieval Time: {avg_retrieval:.1f}ms ({avg_retrieval/avg_total*100:.1f}%)")
        print(f"Average LLM Time: {avg_llm:.1f}ms ({avg_llm/avg_total*100:.1f}%)")
        print(f"Average Chunks Retrieved: {sum(r['chunks_retrieved'] for r in results) / len(results):.1f}")
        print(f"Model Used: {results[0]['model_used']}")
        
        # Performance categorization
        if avg_total < 2000:
            print("🚀 Excellent performance (< 2 seconds)")
        elif avg_total < 5000:
            print("✅ Good performance (2-5 seconds)")
        elif avg_total < 10000:
            print("⚠️  Moderate performance (5-10 seconds)")
        else:
            print("❌ Slow performance (> 10 seconds)")
    
    return results

if __name__ == "__main__":
    test_performance()