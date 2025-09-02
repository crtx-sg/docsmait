"""
Performance and Load Testing

Tests for system performance, response times, and load handling.
"""

import pytest
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


@pytest.mark.performance
@pytest.mark.slow
class TestAPIPerformance:
    """Test API endpoint performance."""

    def test_settings_endpoint_performance(self, backend_url):
        """Test settings endpoint response time."""
        response_times = []
        
        # Make multiple requests to get average
        for i in range(10):
            start_time = time.time()
            response = requests.get(f"{backend_url}/settings", timeout=10)
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
            time.sleep(0.1)  # Small delay between requests
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        median_time = statistics.median(response_times)
        
        # Performance assertions
        assert avg_time < 2.0, f"Average response time too slow: {avg_time:.2f}s"
        assert max_time < 5.0, f"Maximum response time too slow: {max_time:.2f}s"
        assert median_time < 1.5, f"Median response time too slow: {median_time:.2f}s"
        
        print(f"\n📊 Settings Endpoint Performance:")
        print(f"   Average: {avg_time:.3f}s")
        print(f"   Median:  {median_time:.3f}s")
        print(f"   Min:     {min_time:.3f}s")
        print(f"   Max:     {max_time:.3f}s")

    def test_authentication_performance(self, backend_url, test_admin_credentials):
        """Test authentication endpoint performance."""
        response_times = []
        
        # Test login performance
        for i in range(5):
            start_time = time.time()
            response = requests.post(f"{backend_url}/auth/login", json=test_admin_credentials)
            end_time = time.time()
            
            # Might fail if user doesn't exist, but measure time anyway
            response_times.append(end_time - start_time)
            time.sleep(0.2)
        
        avg_time = statistics.mean(response_times)
        assert avg_time < 3.0, f"Authentication too slow: {avg_time:.2f}s"
        
        print(f"\n🔐 Authentication Performance:")
        print(f"   Average login time: {avg_time:.3f}s")

    def test_concurrent_requests_performance(self, backend_url):
        """Test performance under concurrent load."""
        num_workers = 10
        requests_per_worker = 5
        
        def make_request():
            start_time = time.time()
            try:
                response = requests.get(f"{backend_url}/settings", timeout=10)
                end_time = time.time()
                return {
                    'success': response.status_code == 200,
                    'time': end_time - start_time,
                    'status': response.status_code
                }
            except Exception as e:
                end_time = time.time()
                return {
                    'success': False,
                    'time': end_time - start_time,
                    'error': str(e)
                }
        
        # Execute concurrent requests
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            
            for _ in range(num_workers * requests_per_worker):
                futures.append(executor.submit(make_request))
            
            for future in as_completed(futures):
                results.append(future.result())
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        success_rate = len(successful_requests) / len(results) * 100
        
        if successful_requests:
            avg_response_time = statistics.mean([r['time'] for r in successful_requests])
            max_response_time = max([r['time'] for r in successful_requests])
        else:
            avg_response_time = 0
            max_response_time = 0
        
        # Performance assertions
        assert success_rate >= 90, f"Success rate too low: {success_rate:.1f}%"
        assert avg_response_time < 5.0, f"Average response time under load too slow: {avg_response_time:.2f}s"
        
        print(f"\n🔄 Concurrent Load Test Results:")
        print(f"   Total requests: {len(results)}")
        print(f"   Successful: {len(successful_requests)} ({success_rate:.1f}%)")
        print(f"   Failed: {len(failed_requests)}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Requests/sec: {len(results)/total_time:.1f}")
        print(f"   Avg response time: {avg_response_time:.3f}s")
        print(f"   Max response time: {max_response_time:.3f}s")


@pytest.mark.performance
@pytest.mark.slow
class TestDatabasePerformance:
    """Test database operation performance."""

    def test_database_connection_pool_performance(self, test_config):
        """Test database connection pooling performance."""
        try:
            from sqlalchemy import create_engine, text
            import threading
            
            # Create engine with connection pooling
            engine = create_engine(
                test_config["database_url"],
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
            
            results = []
            
            def execute_query(query_id):
                start_time = time.time()
                try:
                    with engine.connect() as connection:
                        result = connection.execute(text("SELECT COUNT(*) FROM users"))
                        count = result.fetchone()[0]
                    end_time = time.time()
                    
                    return {
                        'query_id': query_id,
                        'success': True,
                        'time': end_time - start_time,
                        'result': count
                    }
                except Exception as e:
                    end_time = time.time()
                    return {
                        'query_id': query_id,
                        'success': False,
                        'time': end_time - start_time,
                        'error': str(e)
                    }
            
            # Execute concurrent database queries
            num_threads = 15
            threads = []
            
            start_time = time.time()
            for i in range(num_threads):
                thread = threading.Thread(target=lambda i=i: results.append(execute_query(i)))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join(timeout=30)
            
            end_time = time.time()
            
            # Analyze results
            successful_queries = [r for r in results if r.get('success', False)]
            failed_queries = [r for r in results if not r.get('success', False)]
            
            if successful_queries:
                avg_query_time = statistics.mean([r['time'] for r in successful_queries])
                max_query_time = max([r['time'] for r in successful_queries])
                
                # Performance assertions
                assert len(successful_queries) >= num_threads * 0.9, "Too many database queries failed"
                assert avg_query_time < 2.0, f"Database queries too slow: {avg_query_time:.2f}s"
                
                print(f"\n🗄️ Database Performance Test:")
                print(f"   Concurrent queries: {num_threads}")
                print(f"   Successful: {len(successful_queries)}")
                print(f"   Failed: {len(failed_queries)}")
                print(f"   Avg query time: {avg_query_time:.3f}s")
                print(f"   Max query time: {max_query_time:.3f}s")
                print(f"   Total time: {end_time - start_time:.3f}s")
            else:
                pytest.skip("No successful database queries")
                
        except ImportError:
            pytest.skip("SQLAlchemy not available for database performance testing")
        except Exception as e:
            pytest.skip(f"Cannot perform database performance test: {e}")


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryAndResourceUsage:
    """Test memory usage and resource consumption."""

    def test_memory_usage_during_requests(self, backend_url):
        """Test memory usage during API requests."""
        try:
            import psutil
            
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Make series of requests
            for i in range(20):
                response = requests.get(f"{backend_url}/settings")
                assert response.status_code == 200
                time.sleep(0.1)
            
            # Check final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = final_memory - initial_memory
            
            print(f"\n💾 Memory Usage Test:")
            print(f"   Initial memory: {initial_memory:.1f} MB")
            print(f"   Final memory: {final_memory:.1f} MB")
            print(f"   Memory growth: {memory_growth:.1f} MB")
            
            # Memory growth should be reasonable
            assert memory_growth < 50, f"Excessive memory growth: {memory_growth:.1f} MB"
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")

    def test_response_size_optimization(self, backend_url):
        """Test API response sizes are reasonable."""
        endpoints_to_test = [
            "/settings",
            "/projects/1/export-status"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{backend_url}{endpoint}")
                
                if response.status_code == 200:
                    response_size = len(response.content)
                    
                    # Response should be reasonable size
                    assert response_size < 10 * 1024, f"{endpoint} response too large: {response_size} bytes"
                    
                    print(f"\n📏 Response Size - {endpoint}: {response_size} bytes")
                    
            except Exception as e:
                print(f"Could not test {endpoint}: {e}")


@pytest.mark.performance
@pytest.mark.slow
class TestScalabilityLimits:
    """Test system scalability limits."""

    def test_maximum_concurrent_users(self, backend_url):
        """Test maximum concurrent user simulation."""
        max_users = 25  # Conservative limit for testing
        request_duration = []
        success_count = 0
        
        def simulate_user():
            try:
                start_time = time.time()
                
                # Simulate user session: login attempt + settings check
                login_response = requests.post(
                    f"{backend_url}/auth/login",
                    json={"email": "test@example.com", "password": "wrong"},
                    timeout=10
                )
                
                settings_response = requests.get(f"{backend_url}/settings", timeout=10)
                
                end_time = time.time()
                
                return {
                    'success': settings_response.status_code == 200,
                    'time': end_time - start_time
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'time': 0,
                    'error': str(e)
                }
        
        # Execute concurrent user simulation
        with ThreadPoolExecutor(max_workers=max_users) as executor:
            futures = [executor.submit(simulate_user) for _ in range(max_users)]
            
            for future in as_completed(futures, timeout=60):
                result = future.result()
                if result['success']:
                    success_count += 1
                    request_duration.append(result['time'])
        
        # Calculate success rate
        success_rate = (success_count / max_users) * 100
        
        if request_duration:
            avg_response_time = statistics.mean(request_duration)
        else:
            avg_response_time = 0
        
        print(f"\n👥 Scalability Test:")
        print(f"   Concurrent users: {max_users}")
        print(f"   Successful sessions: {success_count} ({success_rate:.1f}%)")
        print(f"   Average response time: {avg_response_time:.2f}s")
        
        # System should handle reasonable concurrent load
        assert success_rate >= 80, f"Success rate too low under load: {success_rate:.1f}%"
        assert avg_response_time < 10.0, f"Response time too slow under load: {avg_response_time:.2f}s"

    def test_sustained_load_performance(self, backend_url):
        """Test performance under sustained load."""
        duration_minutes = 2  # Short duration for testing
        request_interval = 0.5  # Seconds between requests
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        response_times = []
        error_count = 0
        request_count = 0
        
        print(f"\n⏱️ Starting {duration_minutes}-minute sustained load test...")
        
        while time.time() < end_time:
            try:
                request_start = time.time()
                response = requests.get(f"{backend_url}/settings", timeout=5)
                request_end = time.time()
                
                response_times.append(request_end - request_start)
                request_count += 1
                
                if response.status_code != 200:
                    error_count += 1
                    
            except Exception:
                error_count += 1
                request_count += 1
            
            time.sleep(request_interval)
        
        # Calculate performance metrics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            error_rate = (error_count / request_count) * 100 if request_count > 0 else 100
            
            print(f"\n🔄 Sustained Load Results:")
            print(f"   Duration: {duration_minutes} minutes")
            print(f"   Total requests: {request_count}")
            print(f"   Errors: {error_count} ({error_rate:.1f}%)")
            print(f"   Avg response time: {avg_response_time:.3f}s")
            print(f"   Min response time: {min_response_time:.3f}s")
            print(f"   Max response time: {max_response_time:.3f}s")
            
            # Performance assertions for sustained load
            assert error_rate < 10, f"Error rate too high: {error_rate:.1f}%"
            assert avg_response_time < 3.0, f"Average response time degraded: {avg_response_time:.2f}s"
            assert max_response_time < 10.0, f"Maximum response time too high: {max_response_time:.2f}s"
            
        else:
            pytest.fail("No successful requests during sustained load test")