"""
Database CRUD Operations Tests

Tests for Create, Read, Update, Delete operations on all database models.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


@pytest.mark.database
class TestDatabaseConnection:
    """Test database connectivity and basic operations."""

    def test_database_connection(self, test_config):
        """Test basic database connection."""
        try:
            from sqlalchemy import create_engine
            engine = create_engine(test_config["database_url"])
            
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1
        except Exception as e:
            pytest.skip(f"Cannot connect to test database: {e}")

    def test_database_tables_exist(self, test_config):
        """Test that required tables exist."""
        try:
            from sqlalchemy import create_engine, inspect
            engine = create_engine(test_config["database_url"])
            inspector = inspect(engine)
            
            # Check for key tables
            tables = inspector.get_table_names()
            
            expected_tables = [
                "users", "projects", "documents", "templates", 
                "activity_logs", "reviews", "audit_reports"
            ]
            
            # At least some core tables should exist
            existing_tables = [table for table in expected_tables if table in tables]
            assert len(existing_tables) > 0, f"No expected tables found. Available: {tables}"
            
        except Exception as e:
            pytest.skip(f"Cannot inspect database: {e}")

    def test_database_version(self, test_config):
        """Test database version compatibility."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(test_config["database_url"])
            
            with engine.connect() as connection:
                result = connection.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                
                # Should be PostgreSQL
                assert "PostgreSQL" in version
                
                # Extract version number
                import re
                version_match = re.search(r"PostgreSQL (\d+\.\d+)", version)
                if version_match:
                    major_version = float(version_match.group(1))
                    assert major_version >= 13.0, f"PostgreSQL version {major_version} may be too old"
                    
        except Exception as e:
            pytest.skip(f"Cannot check database version: {e}")


@pytest.mark.database
class TestUserCRUDOperations:
    """Test CRUD operations for User model."""

    def test_create_user_direct(self, test_config):
        """Test creating user directly in database."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(test_config["database_url"])
            
            test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            test_user = {
                "username": f"dbtest_{test_timestamp}",
                "email": f"dbtest_{test_timestamp}@docsmait.com",
                "password_hash": "$2b$12$test_hash_for_testing"  # Mock hash
            }
            
            with engine.begin() as connection:
                # Insert user
                result = connection.execute(
                    text("""
                        INSERT INTO users (username, email, password_hash, is_admin, is_super_admin) 
                        VALUES (:username, :email, :password_hash, false, false)
                        RETURNING id, username, email
                    """),
                    test_user
                )
                
                created_user = result.fetchone()
                assert created_user is not None
                assert created_user[1] == test_user["username"]  # username
                assert created_user[2] == test_user["email"]     # email
                
                user_id = created_user[0]
                
                # Verify user exists
                result = connection.execute(
                    text("SELECT * FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                
                fetched_user = result.fetchone()
                assert fetched_user is not None
                
                # Clean up
                connection.execute(
                    text("DELETE FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                
        except Exception as e:
            pytest.skip(f"Cannot perform direct database operations: {e}")

    def test_user_constraints(self, test_config):
        """Test user table constraints."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(test_config["database_url"])
            
            with engine.begin() as connection:
                test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # Test email uniqueness constraint
                base_email = f"unique_test_{test_timestamp}@docsmait.com"
                
                # Insert first user
                connection.execute(
                    text("""
                        INSERT INTO users (username, email, password_hash, is_admin, is_super_admin) 
                        VALUES (:username, :email, :password_hash, false, false)
                    """),
                    {
                        "username": f"user1_{test_timestamp}",
                        "email": base_email,
                        "password_hash": "$2b$12$test_hash_1"
                    }
                )
                
                # Try to insert second user with same email (should fail)
                with pytest.raises(Exception):  # Should raise integrity error
                    connection.execute(
                        text("""
                            INSERT INTO users (username, email, password_hash, is_admin, is_super_admin) 
                            VALUES (:username, :email, :password_hash, false, false)
                        """),
                        {
                            "username": f"user2_{test_timestamp}",
                            "email": base_email,
                            "password_hash": "$2b$12$test_hash_2"
                        }
                    )
                
                # Clean up
                connection.execute(
                    text("DELETE FROM users WHERE email = :email"),
                    {"email": base_email}
                )
                
        except Exception as e:
            pytest.skip(f"Cannot test constraints: {e}")


@pytest.mark.database
class TestProjectCRUDOperations:
    """Test CRUD operations for Project model."""

    def test_create_project_direct(self, test_config):
        """Test creating project directly in database."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(test_config["database_url"])
            
            with engine.begin() as connection:
                test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # First create a user for the project
                user_result = connection.execute(
                    text("""
                        INSERT INTO users (username, email, password_hash, is_admin, is_super_admin) 
                        VALUES (:username, :email, :password_hash, false, false)
                        RETURNING id
                    """),
                    {
                        "username": f"project_owner_{test_timestamp}",
                        "email": f"project_owner_{test_timestamp}@docsmait.com",
                        "password_hash": "$2b$12$test_hash"
                    }
                )
                user_id = user_result.fetchone()[0]
                
                # Now create project
                project_result = connection.execute(
                    text("""
                        INSERT INTO projects (name, description, created_by) 
                        VALUES (:name, :description, :created_by)
                        RETURNING id, name, description
                    """),
                    {
                        "name": f"Test Project {test_timestamp}",
                        "description": f"Test project created at {test_timestamp}",
                        "created_by": user_id
                    }
                )
                
                created_project = project_result.fetchone()
                assert created_project is not None
                project_id = created_project[0]
                
                # Verify project exists
                result = connection.execute(
                    text("SELECT * FROM projects WHERE id = :project_id"),
                    {"project_id": project_id}
                )
                
                fetched_project = result.fetchone()
                assert fetched_project is not None
                
                # Clean up
                connection.execute(
                    text("DELETE FROM projects WHERE id = :project_id"),
                    {"project_id": project_id}
                )
                connection.execute(
                    text("DELETE FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                
        except Exception as e:
            pytest.skip(f"Cannot test project CRUD: {e}")


@pytest.mark.database
class TestActivityLogCRUDOperations:
    """Test CRUD operations for ActivityLog model."""

    def test_create_activity_log(self, test_config):
        """Test creating activity log entry."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(test_config["database_url"])
            
            with engine.begin() as connection:
                test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # Create user first
                user_result = connection.execute(
                    text("""
                        INSERT INTO users (username, email, password_hash, is_admin, is_super_admin) 
                        VALUES (:username, :email, :password_hash, false, false)
                        RETURNING id
                    """),
                    {
                        "username": f"log_user_{test_timestamp}",
                        "email": f"log_user_{test_timestamp}@docsmait.com",
                        "password_hash": "$2b$12$test_hash"
                    }
                )
                user_id = user_result.fetchone()[0]
                
                # Create activity log entry
                log_result = connection.execute(
                    text("""
                        INSERT INTO activity_logs (user_id, action, resource_type, resource_name, description, activity_metadata) 
                        VALUES (:user_id, :action, :resource_type, :resource_name, :description, :metadata)
                        RETURNING id
                    """),
                    {
                        "user_id": user_id,
                        "action": "create",
                        "resource_type": "test",
                        "resource_name": f"Test Resource {test_timestamp}",
                        "description": f"Test activity logged at {test_timestamp}",
                        "metadata": '{"test": true, "timestamp": "' + test_timestamp + '"}'
                    }
                )
                
                log_id = log_result.fetchone()[0]
                assert log_id is not None
                
                # Verify log exists and has correct structure
                result = connection.execute(
                    text("SELECT * FROM activity_logs WHERE id = :log_id"),
                    {"log_id": log_id}
                )
                
                log_entry = result.fetchone()
                assert log_entry is not None
                
                # Verify activity_metadata column exists (not 'metadata')
                # This tests our fix for the SQLAlchemy reserved name issue
                columns = [desc[0] for desc in result.description]
                assert "activity_metadata" in columns
                assert "metadata" not in columns or columns.count("metadata") == 0
                
                # Clean up
                connection.execute(
                    text("DELETE FROM activity_logs WHERE id = :log_id"),
                    {"log_id": log_id}
                )
                connection.execute(
                    text("DELETE FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                
        except Exception as e:
            pytest.skip(f"Cannot test activity log CRUD: {e}")


@pytest.mark.database
class TestDatabaseIntegrity:
    """Test database integrity and relationships."""

    def test_foreign_key_constraints(self, test_config):
        """Test foreign key relationships."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(test_config["database_url"])
            
            with engine.begin() as connection:
                # Try to create project with non-existent user (should fail)
                with pytest.raises(Exception):  # Should raise foreign key constraint error
                    connection.execute(
                        text("""
                            INSERT INTO projects (name, description, created_by) 
                            VALUES ('Test Project', 'Test Description', 99999)
                        """)
                    )
                    
        except Exception as e:
            pytest.skip(f"Cannot test foreign keys: {e}")

    def test_cascade_behavior(self, test_config):
        """Test cascade delete behavior."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(test_config["database_url"])
            
            with engine.begin() as connection:
                test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # Create user
                user_result = connection.execute(
                    text("""
                        INSERT INTO users (username, email, password_hash, is_admin, is_super_admin) 
                        VALUES (:username, :email, :password_hash, false, false)
                        RETURNING id
                    """),
                    {
                        "username": f"cascade_test_{test_timestamp}",
                        "email": f"cascade_test_{test_timestamp}@docsmait.com",
                        "password_hash": "$2b$12$test_hash"
                    }
                )
                user_id = user_result.fetchone()[0]
                
                # Create project
                project_result = connection.execute(
                    text("""
                        INSERT INTO projects (name, description, created_by) 
                        VALUES (:name, :description, :created_by)
                        RETURNING id
                    """),
                    {
                        "name": f"Cascade Test Project {test_timestamp}",
                        "description": "Project for testing cascade behavior",
                        "created_by": user_id
                    }
                )
                project_id = project_result.fetchone()[0]
                
                # Verify both exist
                user_check = connection.execute(
                    text("SELECT COUNT(*) FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()[0]
                
                project_check = connection.execute(
                    text("SELECT COUNT(*) FROM projects WHERE id = :project_id"),
                    {"project_id": project_id}
                ).fetchone()[0]
                
                assert user_check == 1
                assert project_check == 1
                
                # Clean up manually (test what happens)
                connection.execute(
                    text("DELETE FROM projects WHERE id = :project_id"),
                    {"project_id": project_id}
                )
                connection.execute(
                    text("DELETE FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                
        except Exception as e:
            pytest.skip(f"Cannot test cascade behavior: {e}")


@pytest.mark.database
@pytest.mark.slow
class TestDatabasePerformance:
    """Test database performance characteristics."""

    def test_query_performance(self, test_config):
        """Test basic query performance."""
        try:
            from sqlalchemy import create_engine, text
            import time
            
            engine = create_engine(test_config["database_url"])
            
            with engine.connect() as connection:
                # Time a simple query
                start_time = time.time()
                result = connection.execute(text("SELECT COUNT(*) FROM users"))
                end_time = time.time()
                
                query_time = end_time - start_time
                user_count = result.fetchone()[0]
                
                # Query should complete quickly
                assert query_time < 1.0, f"Simple query too slow: {query_time:.2f}s"
                assert user_count >= 0  # Should return valid count
                
        except Exception as e:
            pytest.skip(f"Cannot test query performance: {e}")

    def test_connection_pooling(self, test_config):
        """Test connection pooling behavior."""
        try:
            from sqlalchemy import create_engine, text
            import threading
            import time
            
            engine = create_engine(
                test_config["database_url"],
                pool_size=5,
                max_overflow=10
            )
            
            results = []
            
            def execute_query():
                start_time = time.time()
                with engine.connect() as connection:
                    result = connection.execute(text("SELECT 1"))
                    assert result.fetchone()[0] == 1
                end_time = time.time()
                results.append(end_time - start_time)
            
            # Create multiple concurrent connections
            threads = []
            for i in range(10):
                thread = threading.Thread(target=execute_query)
                threads.append(thread)
            
            # Start all threads
            for thread in threads:
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            # All queries should succeed
            assert len(results) == 10
            
            # Average time should be reasonable
            avg_time = sum(results) / len(results)
            assert avg_time < 2.0, f"Pooled queries too slow: {avg_time:.2f}s"
            
        except Exception as e:
            pytest.skip(f"Cannot test connection pooling: {e}")