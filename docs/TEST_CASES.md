# Docsmait - Test Cases and Test Scenarios

## 1. Test Strategy Overview

### 1.1 Testing Approach
The Docsmait testing strategy employs a comprehensive multi-layered approach covering:
- **Unit Testing**: Individual component and service testing
- **Integration Testing**: API endpoint and service integration testing  
- **System Testing**: End-to-end workflow testing
- **Security Testing**: Authentication, authorization, and data protection
- **Performance Testing**: Load testing and scalability validation
- **Compliance Testing**: Regulatory and audit requirement validation
- **User Acceptance Testing**: Business workflow and usability testing

### 1.2 Test Environment Configuration
- **Test Database**: PostgreSQL with isolated test schema
- **Vector Database**: Qdrant test instance with sample data
- **AI Service**: Ollama with test models (lightweight)
- **Email Service**: Mock SMTP service for notification testing
- **File Storage**: Temporary directory with cleanup automation

### 1.3 Test Data Strategy
- **User Test Data**: Predefined users with different roles and permissions
- **Project Test Data**: Sample projects with various configurations
- **Document Test Data**: Templates and documents covering all types
- **Knowledge Base Test Data**: Sample documents for semantic search testing
- **Audit Test Data**: Complete audit scenarios with findings and actions

## 2. Unit Test Cases

### 2.1 User Management Service Tests

#### Test Suite: UserService
```python
class TestUserService:
    
    def test_create_user_success(self):
        """Test successful user creation with valid data"""
        # Given
        user_data = {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "SecurePass123!"
        }
        
        # When
        result = user_service.create_user(**user_data)
        
        # Then
        assert result is not None
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.password_hash != user_data["password"]  # Password is hashed
        assert not result.is_admin  # Default role
    
    def test_create_user_duplicate_email(self):
        """Test user creation fails with duplicate email"""
        # Given
        existing_user = create_test_user("existing@example.com")
        
        # When/Then
        with pytest.raises(ValueError, match="Email already registered"):
            user_service.create_user(
                username="newuser",
                email="existing@example.com",
                password="Password123!"
            )
    
    def test_authenticate_user_valid_credentials(self):
        """Test successful user authentication"""
        # Given
        user = create_test_user("auth@example.com", password="TestPass123!")
        
        # When
        result = user_service.authenticate_user("auth@example.com", "TestPass123!")
        
        # Then
        assert result is not None
        assert result.email == "auth@example.com"
    
    def test_authenticate_user_invalid_credentials(self):
        """Test authentication fails with invalid credentials"""
        # Given
        user = create_test_user("auth@example.com", password="TestPass123!")
        
        # When
        result = user_service.authenticate_user("auth@example.com", "WrongPassword")
        
        # Then
        assert result is None
    
    def test_get_user_by_id_exists(self):
        """Test retrieving existing user by ID"""
        # Given
        user = create_test_user("find@example.com")
        
        # When
        result = user_service.get_user_by_id(user.id)
        
        # Then
        assert result is not None
        assert result.id == user.id
        assert result.email == "find@example.com"
    
    def test_get_user_by_id_not_exists(self):
        """Test retrieving non-existent user returns None"""
        # When
        result = user_service.get_user_by_id(99999)
        
        # Then
        assert result is None
    
    def test_update_user_admin_status(self):
        """Test updating user admin status"""
        # Given
        user = create_test_user("admin@example.com")
        admin = create_test_admin()
        
        # When
        result = user_service.update_user_admin_status(
            user_id=user.id,
            is_admin=True,
            updated_by_user_id=admin.id
        )
        
        # Then
        assert result is True
        updated_user = user_service.get_user_by_id(user.id)
        assert updated_user.is_admin is True
```

#### Test Suite: Authentication and JWT
```python
class TestAuthentication:
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        # Given
        user_data = {"sub": "123", "email": "test@example.com"}
        
        # When
        token = auth.create_access_token(data=user_data)
        
        # Then
        assert token is not None
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT format
    
    def test_verify_token_valid(self):
        """Test valid token verification"""
        # Given
        user = create_test_user("verify@example.com")
        token = auth.create_access_token(data={"sub": str(user.id)})
        
        # When
        result = auth.verify_token(token)
        
        # Then
        assert result == user.id
    
    def test_verify_token_expired(self):
        """Test expired token verification"""
        # Given
        expired_token = create_expired_token()
        
        # When/Then
        with pytest.raises(HTTPException) as exc_info:
            auth.verify_token(expired_token)
        assert exc_info.value.status_code == 401
    
    def test_verify_token_invalid(self):
        """Test invalid token verification"""
        # When/Then
        with pytest.raises(HTTPException) as exc_info:
            auth.verify_token("invalid.token.here")
        assert exc_info.value.status_code == 401
```

### 2.2 Project Management Service Tests

#### Test Suite: ProjectService
```python
class TestProjectService:
    
    def test_create_project_success(self):
        """Test successful project creation"""
        # Given
        user = create_test_user("creator@example.com")
        project_data = {
            "name": "Test Project",
            "description": "A test project",
            "created_by": user.id
        }
        
        # When
        result = projects_service.create_project(**project_data)
        
        # Then
        assert result["success"] is True
        assert "project_id" in result
        assert result["message"] == "Project created successfully"
        
        # Verify project exists in database
        project = get_project_by_id(result["project_id"])
        assert project.name == "Test Project"
        assert project.created_by == user.id
        
        # Verify creator is added as admin member
        membership = get_project_membership(result["project_id"], user.id)
        assert membership is not None
        assert membership.role == "admin"
    
    def test_create_project_duplicate_name(self):
        """Test project creation fails with duplicate name"""
        # Given
        user = create_test_user("creator@example.com")
        create_test_project("Existing Project", user.id)
        
        # When
        result = projects_service.create_project(
            name="Existing Project",
            description="Duplicate name",
            created_by=user.id
        )
        
        # Then
        assert result["success"] is False
        assert "already exists" in result["error"]
    
    def test_add_member_success(self):
        """Test successful member addition to project"""
        # Given
        creator = create_test_user("creator@example.com")
        member = create_test_user("member@example.com") 
        project = create_test_project("Test Project", creator.id)
        
        # When
        result = projects_service.add_member(
            project_id=project.id,
            user_id=creator.id,
            new_member_email="member@example.com",
            role="member"
        )
        
        # Then
        assert result["success"] is True
        assert "added to project" in result["message"]
        
        # Verify membership exists
        membership = get_project_membership(project.id, member.id)
        assert membership is not None
        assert membership.role == "member"
    
    def test_add_member_not_admin(self):
        """Test member addition fails when user is not admin"""
        # Given
        creator = create_test_user("creator@example.com")
        member = create_test_user("member@example.com")
        other_member = create_test_user("other@example.com")
        project = create_test_project("Test Project", creator.id)
        add_project_member(project.id, member.id, "member")
        
        # When
        result = projects_service.add_member(
            project_id=project.id,
            user_id=member.id,  # Non-admin user trying to add member
            new_member_email="other@example.com",
            role="member"
        )
        
        # Then
        assert result["success"] is False
        assert "Only project admins can add members" in result["error"]
    
    def test_get_user_projects(self):
        """Test retrieving user's projects"""
        # Given
        user = create_test_user("member@example.com")
        project1 = create_test_project("Project 1", user.id)
        project2 = create_test_project("Project 2", create_test_user("other@example.com").id)
        add_project_member(project2.id, user.id, "member")
        
        # When
        result = projects_service.get_user_projects(user.id)
        
        # Then
        assert len(result) == 2
        project_names = [p["name"] for p in result]
        assert "Project 1" in project_names
        assert "Project 2" in project_names
        
        # Check role information
        for project in result:
            if project["name"] == "Project 1":
                assert project["is_creator"] is True
            else:
                assert project["is_creator"] is False
```

### 2.3 Document Management Service Tests

#### Test Suite: DocumentService
```python
class TestDocumentService:
    
    def test_create_document_success(self):
        """Test successful document creation"""
        # Given
        user = create_test_user("author@example.com")
        project = create_test_project("Doc Project", user.id)
        
        # When
        result = documents_service.create_document(
            name="Test Document",
            document_type="process_documents",
            content="# Test Content\n\nThis is a test document.",
            project_id=project.id,
            user_id=user.id,
            status="draft"
        )
        
        # Then
        assert result["success"] is True
        assert "document_id" in result
        
        # Verify document in database
        document = get_document_by_id(result["document_id"])
        assert document.name == "Test Document"
        assert document.status == "draft"
        assert document.current_revision == 1
    
    def test_create_document_duplicate_name(self):
        """Test document creation fails with duplicate name in project"""
        # Given
        user = create_test_user("author@example.com")
        project = create_test_project("Doc Project", user.id)
        create_test_document("Existing Doc", project.id, user.id)
        
        # When
        result = documents_service.create_document(
            name="Existing Doc",
            document_type="process_documents",
            content="Content",
            project_id=project.id,
            user_id=user.id
        )
        
        # Then
        assert result["success"] is False
        assert "already exists" in result["error"]
    
    def test_update_document_status_workflow(self):
        """Test document status workflow transitions"""
        # Given
        user = create_test_user("author@example.com")
        reviewer = create_test_user("reviewer@example.com")
        project = create_test_project("Doc Project", user.id)
        add_project_member(project.id, reviewer.id, "member")
        
        document = create_test_document("Workflow Doc", project.id, user.id, status="draft")
        
        # When: Transition to review
        result = documents_service.update_document(
            document_id=document.id,
            user_id=user.id,
            status="request_review",
            reviewers=[reviewer.id]
        )
        
        # Then
        assert result["success"] is True
        updated_doc = get_document_by_id(document.id)
        assert updated_doc.status == "request_review"
        
        # Verify reviewer assignment
        reviewers = get_document_reviewers(document.id)
        assert len(reviewers) == 1
        assert reviewers[0].reviewer_id == reviewer.id
    
    def test_submit_document_review(self):
        """Test document review submission"""
        # Given
        author = create_test_user("author@example.com")
        reviewer = create_test_user("reviewer@example.com")
        project = create_test_project("Review Project", author.id)
        add_project_member(project.id, reviewer.id, "member")
        
        document = create_test_document("Review Doc", project.id, author.id)
        revision = create_document_revision(document.id, status="request_review")
        assign_document_reviewer(document.id, revision.id, reviewer.id)
        
        # When
        result = documents_service.submit_document_review(
            document_id=document.id,
            revision_id=revision.id,
            reviewer_id=reviewer.id,
            approved=True,
            comments="Looks good to me!"
        )
        
        # Then
        assert result["success"] is True
        
        # Verify review exists
        review = get_document_review(document.id, reviewer.id)
        assert review is not None
        assert review.approved is True
        assert review.comments == "Looks good to me!"
    
    def test_get_document_revisions(self):
        """Test retrieving document revision history"""
        # Given
        user = create_test_user("author@example.com")
        project = create_test_project("Version Project", user.id)
        document = create_test_document("Versioned Doc", project.id, user.id)
        
        # Create multiple revisions
        rev1 = create_document_revision(document.id, content="Version 1", revision_number=1)
        rev2 = create_document_revision(document.id, content="Version 2", revision_number=2)
        rev3 = create_document_revision(document.id, content="Version 3", revision_number=3)
        
        # When
        result = documents_service.get_document_revisions(document.id, user.id)
        
        # Then
        assert len(result) == 3
        assert result[0]["revision_number"] == 3  # Most recent first
        assert result[1]["revision_number"] == 2
        assert result[2]["revision_number"] == 1
```

### 2.4 Knowledge Base Service Tests

#### Test Suite: KnowledgeBaseService
```python
class TestKnowledgeBaseService:
    
    def test_create_collection_success(self):
        """Test successful knowledge base collection creation"""
        # Given
        user = create_test_user("kb_user@example.com")
        
        # When
        result = kb_service.create_collection(
            name="test_collection",
            description="Test collection for unit tests",
            created_by=user.username,
            tags=["test", "unit"]
        )
        
        # Then
        assert result["success"] is True
        assert "collection_id" in result
        
        # Verify collection exists in database
        collection = get_kb_collection_by_name("test_collection")
        assert collection is not None
        assert collection.description == "Test collection for unit tests"
        assert "test" in collection.tags
    
    def test_add_document_to_collection(self):
        """Test adding document to knowledge base collection"""
        # Given
        collection = create_test_kb_collection("test_docs")
        document_content = "This is a test document for knowledge base indexing."
        
        # When
        result = kb_service.add_text_to_collection(
            collection_name="test_docs",
            text_content=document_content,
            filename="test_doc.txt",
            metadata={"source": "unit_test"}
        )
        
        # Then
        assert result["success"] is True
        
        # Verify document in database
        documents = get_kb_documents_by_collection("test_docs")
        assert len(documents) == 1
        assert documents[0].filename == "test_doc.txt"
        assert "unit_test" in documents[0].metadata
    
    def test_semantic_search(self):
        """Test semantic search functionality"""
        # Given
        collection = create_test_kb_collection("search_test")
        
        # Add test documents
        test_docs = [
            "Software development best practices and methodologies",
            "Quality assurance testing procedures and protocols", 
            "Project management and team collaboration tools",
            "Database design patterns and optimization techniques"
        ]
        
        for i, doc in enumerate(test_docs):
            kb_service.add_text_to_collection(
                collection_name="search_test",
                text_content=doc,
                filename=f"doc_{i}.txt"
            )
        
        # When
        result = kb_service.query_knowledge_base(
            message="Tell me about software development",
            collection_name="search_test"
        )
        
        # Then
        assert result["success"] is True
        assert "response" in result
        assert len(result["sources"]) > 0
        
        # Verify most relevant document is returned
        top_source = result["sources"][0]
        assert "software development" in top_source["content"].lower()
    
    def test_generate_assessment_questions(self):
        """Test assessment question generation from KB content"""
        # Given
        collection = create_test_kb_collection("assessment_test")
        kb_service.add_text_to_collection(
            collection_name="assessment_test",
            text_content="""
            Quality Management Systems must implement document control procedures.
            All controlled documents must be reviewed and approved before use.
            Changes to documents require authorization from designated personnel.
            Training records must be maintained for all personnel.
            """,
            filename="qms_procedures.txt"
        )
        
        # When
        result = kb_service.generate_assessment_questions(
            topic="assessment_test",
            num_questions=5
        )
        
        # Then
        assert result["success"] is True
        assert "questions" in result
        assert len(result["questions"]) == 5
        
        for question in result["questions"]:
            assert "id" in question
            assert "question" in question
            assert "correct_answer" in question
            assert isinstance(question["correct_answer"], bool)
```

### 2.5 AI Service Tests

#### Test Suite: AIService
```python
class TestAIService:
    
    @pytest.mark.asyncio
    async def test_generate_document_assistance(self):
        """Test AI-powered document assistance"""
        # Given
        user = create_test_user("ai_user@example.com")
        document_content = "# Risk Management Plan\n\nThis document outlines..."
        user_input = "Help me add a section about risk assessment procedures"
        
        # When
        success, response, metadata = await ai_service.generate_document_assistance(
            user_id=user.id,
            document_type="risk_management",
            document_content=document_content,
            user_input=user_input,
            model="llama3.2:1b"
        )
        
        # Then
        assert success is True
        assert response is not None
        assert len(response) > 0
        assert "risk assessment" in response.lower()
        assert metadata["processing_time"] > 0
    
    def test_get_document_prompt(self):
        """Test retrieving document-specific AI prompts"""
        # When
        prompt = ai_config.get_document_prompt("risk_management", "generation")
        
        # Then
        assert prompt is not None
        assert "risk" in prompt.lower()
        assert "management" in prompt.lower()
    
    def test_update_document_prompt(self):
        """Test updating AI prompts for document types"""
        # Given
        new_prompt = "Custom prompt for test document generation with specific requirements."
        
        # When
        result = ai_config.update_document_prompt(
            document_type="test_type",
            prompt=new_prompt,
            category="generation"
        )
        
        # Then
        assert result is True
        
        # Verify prompt was saved
        saved_prompt = ai_config.get_document_prompt("test_type", "generation")
        assert saved_prompt == new_prompt
    
    @pytest.mark.asyncio
    async def test_list_available_models(self):
        """Test listing available AI models"""
        # When
        success, models, error = await ai_service.list_available_models()
        
        # Then
        if success:
            assert models is not None
            assert isinstance(models, list)
            assert len(models) > 0
        else:
            # Fallback to configured models if Ollama unavailable
            assert error is not None
    
    @pytest.mark.asyncio
    async def test_check_ollama_health(self):
        """Test AI service health check"""
        # When
        is_healthy = await ai_service.check_ollama_health()
        
        # Then
        assert isinstance(is_healthy, bool)
```

## 3. Integration Test Cases

### 3.1 API Endpoint Tests

#### Test Suite: Authentication API
```python
class TestAuthenticationAPI:
    
    def test_signup_endpoint(self, test_client):
        """Test user registration API endpoint"""
        # Given
        signup_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }
        
        # When
        response = test_client.post("/auth/signup", json=signup_data)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify user was created
        user = get_user_by_email("newuser@example.com")
        assert user is not None
        assert user.username == "newuser"
    
    def test_signup_password_mismatch(self, test_client):
        """Test signup fails when passwords don't match"""
        # Given
        signup_data = {
            "username": "baduser",
            "email": "bad@example.com", 
            "password": "Password123!",
            "confirm_password": "DifferentPassword123!"
        }
        
        # When
        response = test_client.post("/auth/signup", json=signup_data)
        
        # Then
        assert response.status_code == 400
        assert "Passwords do not match" in response.json()["detail"]
    
    def test_login_endpoint(self, test_client):
        """Test user login API endpoint"""
        # Given
        user = create_test_user("login@example.com", password="LoginPass123!")
        login_data = {
            "email": "login@example.com",
            "password": "LoginPass123!"
        }
        
        # When
        response = test_client.post("/auth/login", json=login_data)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, test_client):
        """Test login fails with invalid credentials"""
        # Given
        user = create_test_user("login@example.com", password="CorrectPass123!")
        login_data = {
            "email": "login@example.com",
            "password": "WrongPassword"
        }
        
        # When
        response = test_client.post("/auth/login", json=login_data)
        
        # Then
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_get_current_user(self, test_client, auth_headers):
        """Test retrieving current user information"""
        # When
        response = test_client.get("/auth/me", headers=auth_headers)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "is_admin" in data
```

#### Test Suite: Project Management API
```python
class TestProjectManagementAPI:
    
    def test_create_project_endpoint(self, test_client, auth_headers):
        """Test project creation API endpoint"""
        # Given
        project_data = {
            "name": "API Test Project",
            "description": "Project created via API test"
        }
        
        # When
        response = test_client.post("/projects", json=project_data, headers=auth_headers)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "project_id" in data
        
        # Verify project exists
        project = get_project_by_id(data["project_id"])
        assert project.name == "API Test Project"
    
    def test_list_user_projects(self, test_client, auth_headers):
        """Test listing user projects API endpoint"""
        # Given
        user_id = get_user_id_from_headers(auth_headers)
        project = create_test_project("List Test Project", user_id)
        
        # When
        response = test_client.get("/projects", headers=auth_headers)
        
        # Then
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) >= 1
        
        project_names = [p["name"] for p in projects]
        assert "List Test Project" in project_names
    
    def test_add_project_member(self, test_client, admin_headers):
        """Test adding project member via API"""
        # Given
        admin_id = get_user_id_from_headers(admin_headers)
        new_member = create_test_user("newmember@example.com")
        project = create_test_project("Member Test Project", admin_id)
        
        member_data = {
            "email": "newmember@example.com",
            "role": "member"
        }
        
        # When
        response = test_client.post(
            f"/projects/{project.id}/members/by-email",
            json=member_data,
            headers=admin_headers
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify membership
        membership = get_project_membership(project.id, new_member.id)
        assert membership is not None
        assert membership.role == "member"
    
    def test_unauthorized_project_access(self, test_client, auth_headers):
        """Test that users cannot access projects they're not members of"""
        # Given
        other_user = create_test_user("other@example.com")
        project = create_test_project("Private Project", other_user.id)
        
        # When
        response = test_client.get(f"/projects/{project.id}", headers=auth_headers)
        
        # Then
        assert response.status_code == 404  # Project not found for this user
```

#### Test Suite: Document Management API
```python
class TestDocumentManagementAPI:
    
    def test_create_document_endpoint(self, test_client, auth_headers):
        """Test document creation API endpoint"""
        # Given
        user_id = get_user_id_from_headers(auth_headers)
        project = create_test_project("Doc API Project", user_id)
        
        document_data = {
            "name": "API Test Document",
            "document_type": "process_documents",
            "content": "# API Test\n\nThis document was created via API.",
            "status": "draft"
        }
        
        # When
        response = test_client.post(
            f"/projects/{project.id}/documents",
            json=document_data,
            headers=auth_headers
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data
    
    def test_update_document_status(self, test_client, auth_headers):
        """Test document status update via API"""
        # Given
        user_id = get_user_id_from_headers(auth_headers)
        reviewer = create_test_user("reviewer@example.com")
        project = create_test_project("Status Project", user_id)
        add_project_member(project.id, reviewer.id, "member")
        
        document = create_test_document("Status Doc", project.id, user_id)
        
        update_data = {
            "status": "request_review",
            "reviewers": [reviewer.id],
            "comment": "Ready for review"
        }
        
        # When
        response = test_client.put(
            f"/documents/{document.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify status change
        updated_doc = get_document_by_id(document.id)
        assert updated_doc.status == "request_review"
    
    def test_submit_document_review_endpoint(self, test_client, reviewer_headers):
        """Test document review submission via API"""
        # Given
        author = create_test_user("author@example.com")
        reviewer_id = get_user_id_from_headers(reviewer_headers)
        project = create_test_project("Review Project", author.id)
        add_project_member(project.id, reviewer_id, "member")
        
        document = create_test_document("Review Doc", project.id, author.id)
        revision = create_document_revision(document.id, status="request_review")
        assign_document_reviewer(document.id, revision.id, reviewer_id)
        
        review_data = {
            "revision_id": revision.id,
            "approved": True,
            "comments": "Document looks good, approved!"
        }
        
        # When
        response = test_client.post(
            f"/documents/{document.id}/reviews",
            json=review_data,
            headers=reviewer_headers
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify review exists
        review = get_document_review(document.id, reviewer_id)
        assert review.approved is True
```

### 3.2 Service Integration Tests

#### Test Suite: Email Notification Integration
```python
class TestEmailNotificationIntegration:
    
    def test_project_member_welcome_email(self, mock_smtp):
        """Test welcome email sent when adding project member"""
        # Given
        admin = create_test_user("admin@example.com")
        new_member = create_test_user("member@example.com")
        project = create_test_project("Email Test Project", admin.id)
        
        # When
        result = projects_service.add_member(
            project_id=project.id,
            user_id=admin.id,
            new_member_email="member@example.com",
            role="member"
        )
        
        # Then
        assert result["success"] is True
        
        # Verify email was sent
        assert mock_smtp.send_email_called
        sent_emails = mock_smtp.get_sent_emails()
        assert len(sent_emails) == 1
        
        email = sent_emails[0]
        assert "member@example.com" in email["to"]
        assert "Welcome" in email["subject"]
        assert "Email Test Project" in email["body"]
    
    def test_document_review_notification_email(self, mock_smtp):
        """Test email notification sent for document review assignment"""
        # Given
        author = create_test_user("author@example.com")
        reviewer = create_test_user("reviewer@example.com")
        project = create_test_project("Review Email Project", author.id)
        add_project_member(project.id, reviewer.id, "member")
        
        # When
        result = documents_service.create_document(
            name="Email Review Doc",
            document_type="process_documents",
            content="Content for review",
            project_id=project.id,
            user_id=author.id,
            status="request_review",
            reviewers=[reviewer.id]
        )
        
        # Then
        assert result["success"] is True
        
        # Verify review notification email
        sent_emails = mock_smtp.get_sent_emails()
        review_emails = [e for e in sent_emails if "review" in e["subject"].lower()]
        assert len(review_emails) >= 1
        
        review_email = review_emails[0]
        assert "reviewer@example.com" in review_email["to"]
        assert "Email Review Doc" in review_email["body"]
    
    def test_audit_schedule_notification(self, mock_smtp):
        """Test email notification for audit scheduling"""
        # Given
        auditor = create_test_user("auditor@example.com")
        team_member = create_test_user("team@example.com")
        project_creator = create_test_user("creator@example.com")
        project = create_test_project("Audit Project", project_creator.id)
        add_project_member(project.id, auditor.id, "member")
        add_project_member(project.id, team_member.id, "member")
        
        # When
        with get_db_session() as db:
            audit_service = AuditService(db)
            result = audit_service.create_audit(
                audit_data=AuditCreate(
                    title="Test Audit",
                    audit_type="internal", 
                    scope="Testing audit notifications",
                    planned_start_date="2024-02-01",
                    planned_end_date="2024-02-15",
                    lead_auditor=auditor.id,
                    audit_team=[team_member.id],
                    auditee_department="Quality",
                    project_id=project.id
                ),
                current_user_id=project_creator.id
            )
        
        # Then
        assert result is not None
        
        # Verify audit notification emails sent
        sent_emails = mock_smtp.get_sent_emails()
        audit_emails = [e for e in sent_emails if "audit" in e["subject"].lower()]
        assert len(audit_emails) >= 1
        
        # Check that stakeholders received notifications
        recipients = set()
        for email in audit_emails:
            recipients.update(email["to"])
        
        assert "auditor@example.com" in recipients
        assert "team@example.com" in recipients
        assert "creator@example.com" in recipients
```

#### Test Suite: AI Service Integration
```python
class TestAIServiceIntegration:
    
    @pytest.mark.asyncio
    async def test_ai_document_generation_workflow(self):
        """Test complete AI document generation workflow"""
        # Given
        user = create_test_user("ai_user@example.com")
        project = create_test_project("AI Project", user.id)
        
        # When: Create document with AI assistance
        ai_request = {
            "document_type": "risk_management",
            "document_content": "# Risk Management\n\nInitial content...",
            "user_input": "Add comprehensive risk assessment procedures",
            "model": "llama3.2:1b"
        }
        
        success, ai_response, metadata = await ai_service.generate_document_assistance(
            user_id=user.id,
            **ai_request
        )
        
        # Then
        assert success is True
        assert len(ai_response) > 100  # Substantial response
        assert metadata["processing_time"] > 0
        
        # Create document with AI-generated content
        document_result = documents_service.create_document(
            name="AI Generated Risk Management",
            document_type="process_documents",
            content=ai_response,
            project_id=project.id,
            user_id=user.id
        )
        
        assert document_result["success"] is True
        
        # Verify document contains AI-generated content
        document = get_document_by_id(document_result["document_id"])
        assert "risk" in document.content.lower()
        assert len(document.content) > len(ai_request["document_content"])
    
    @pytest.mark.asyncio
    async def test_knowledge_base_ai_query_integration(self):
        """Test AI-powered knowledge base querying"""
        # Given
        collection = create_test_kb_collection("ai_test")
        
        # Add comprehensive test content
        test_content = """
        Software Development Life Cycle (SDLC) Overview:
        
        1. Requirements Analysis: Gathering and documenting functional and non-functional requirements
        2. Design: Creating system architecture and detailed design specifications  
        3. Implementation: Coding and unit testing of software components
        4. Testing: Integration testing, system testing, and user acceptance testing
        5. Deployment: Release management and production deployment
        6. Maintenance: Ongoing support, bug fixes, and enhancements
        
        Quality Assurance best practices include code reviews, automated testing,
        continuous integration, and adherence to coding standards.
        """
        
        kb_service.add_text_to_collection(
            collection_name="ai_test",
            text_content=test_content,
            filename="sdlc_guide.txt"
        )
        
        # When: Query with AI-powered search
        result = kb_service.query_knowledge_base(
            message="What are the phases of software development lifecycle?",
            collection_name="ai_test"
        )
        
        # Then
        assert result["success"] is True
        assert "response" in result
        assert "sources" in result
        
        response = result["response"]
        assert "requirements" in response.lower()
        assert "design" in response.lower()
        assert "testing" in response.lower()
        
        # Verify source attribution
        assert len(result["sources"]) > 0
        assert "sdlc_guide.txt" in result["sources"][0]["filename"]
```

## 4. System Test Cases

### 4.1 End-to-End Workflow Tests

#### Test Suite: Complete Document Lifecycle
```python
class TestDocumentLifecycleWorkflow:
    
    def test_complete_document_approval_workflow(self):
        """Test complete document creation, review, and approval workflow"""
        # Given: Project setup with multiple users
        project_admin = create_test_user("admin@company.com")
        document_author = create_test_user("author@company.com")  
        reviewer1 = create_test_user("reviewer1@company.com")
        reviewer2 = create_test_user("reviewer2@company.com")
        
        project = create_test_project("Workflow Test Project", project_admin.id)
        add_project_member(project.id, document_author.id, "member")
        add_project_member(project.id, reviewer1.id, "member")
        add_project_member(project.id, reviewer2.id, "member")
        
        # Step 1: Document Creation
        document_result = documents_service.create_document(
            name="Quality Management Procedure",
            document_type="process_documents",
            content="# Quality Management Procedure\n\n## 1. Purpose\n\nThis procedure defines...",
            project_id=project.id,
            user_id=document_author.id,
            status="draft"
        )
        
        assert document_result["success"] is True
        document_id = document_result["document_id"]
        
        # Step 2: Author submits for review
        update_result = documents_service.update_document(
            document_id=document_id,
            user_id=document_author.id,
            status="request_review",
            reviewers=[reviewer1.id, reviewer2.id],
            comment="Ready for initial review"
        )
        
        assert update_result["success"] is True
        
        # Verify document status and reviewers
        document = get_document_by_id(document_id)
        assert document.status == "request_review"
        
        reviewers = get_document_reviewers(document_id)
        assert len(reviewers) == 2
        reviewer_ids = [r.reviewer_id for r in reviewers]
        assert reviewer1.id in reviewer_ids
        assert reviewer2.id in reviewer_ids
        
        # Step 3: First reviewer approves
        current_revision = get_latest_document_revision(document_id)
        review1_result = documents_service.submit_document_review(
            document_id=document_id,
            revision_id=current_revision.id,
            reviewer_id=reviewer1.id,
            approved=True,
            comments="Content looks good, formatting needs minor adjustment"
        )
        
        assert review1_result["success"] is True
        
        # Step 4: Second reviewer requests changes
        review2_result = documents_service.submit_document_review(
            document_id=document_id,
            revision_id=current_revision.id,
            reviewer_id=reviewer2.id,
            approved=False,
            comments="Please add risk assessment section before approval"
        )
        
        assert review2_result["success"] is True
        
        # Verify reviews exist
        reviews = get_document_reviews(document_id)
        assert len(reviews) == 2
        
        approved_review = [r for r in reviews if r.reviewer_id == reviewer1.id][0]
        rejected_review = [r for r in reviews if r.reviewer_id == reviewer2.id][0]
        assert approved_review.approved is True
        assert rejected_review.approved is False
        
        # Step 5: Author addresses feedback and resubmits
        revision_result = documents_service.update_document(
            document_id=document_id,
            user_id=document_author.id,
            content=document.content + "\n\n## 5. Risk Assessment\n\nRisk assessment procedures...",
            comment="Added risk assessment section as requested",
            status="request_review",
            reviewers=[reviewer2.id]  # Only reviewer who rejected needs to re-review
        )
        
        assert revision_result["success"] is True
        
        # Verify new revision created
        revisions = get_document_revisions(document_id)
        assert len(revisions) >= 2
        latest_revision = revisions[0]  # Most recent first
        assert "Risk Assessment" in latest_revision.content
        
        # Step 6: Second reviewer approves revised version
        final_review_result = documents_service.submit_document_review(
            document_id=document_id,
            revision_id=latest_revision.id,
            reviewer_id=reviewer2.id,
            approved=True,
            comments="Risk assessment section added, approved for publication"
        )
        
        assert final_review_result["success"] is True
        
        # Step 7: Document approved and published
        approval_result = documents_service.update_document(
            document_id=document_id,
            user_id=project_admin.id,  # Admin approves final document
            status="approved",
            comment="Document approved for publication"
        )
        
        assert approval_result["success"] is True
        
        # Final verification
        final_document = get_document_by_id(document_id)
        assert final_document.status == "approved"
        assert final_document.current_revision >= 2
        
        # Verify complete audit trail
        all_revisions = get_document_revisions(document_id)
        all_reviews = get_document_reviews(document_id)
        
        assert len(all_revisions) >= 2
        assert len(all_reviews) >= 3  # 2 initial + 1 final
        
        print(f"✅ Complete document workflow test passed:")
        print(f"   - Document created: {document_id}")
        print(f"   - Revisions: {len(all_revisions)}")
        print(f"   - Reviews: {len(all_reviews)}")
        print(f"   - Final status: {final_document.status}")
```

#### Test Suite: Audit Management Workflow
```python
class TestAuditManagementWorkflow:
    
    def test_complete_audit_lifecycle(self):
        """Test complete audit planning, execution, and closure workflow"""
        # Given: Audit setup
        quality_manager = create_test_user("qm@company.com", is_admin=True)
        lead_auditor = create_test_user("auditor@company.com")
        audit_team_member = create_test_user("team@company.com")
        auditee = create_test_user("auditee@company.com")
        
        project = create_test_project("Quality Audit Project", quality_manager.id)
        add_project_member(project.id, lead_auditor.id, "member")
        add_project_member(project.id, audit_team_member.id, "member")
        add_project_member(project.id, auditee.id, "member")
        
        # Step 1: Plan audit
        with get_db_session() as db:
            audit_service = AuditService(db)
            
            audit_result = audit_service.create_audit(
                audit_data=AuditCreate(
                    title="ISO 13485 Internal Audit - Q1 2024",
                    audit_type="internal",
                    scope="Document control procedures and training records",
                    planned_start_date="2024-03-01",
                    planned_end_date="2024-03-07",
                    lead_auditor=lead_auditor.id,
                    audit_team=[audit_team_member.id],
                    auditee_department="Quality Assurance",
                    project_id=project.id
                ),
                current_user_id=quality_manager.id
            )
            
            assert audit_result is not None
            audit_id = audit_result.id
            
            # Step 2: Start audit execution
            update_result = audit_service.update_audit(
                audit_id=audit_id,
                audit_data=AuditUpdate(
                    status="in_progress",
                    actual_start_date="2024-03-01"
                )
            )
            
            assert update_result is not None
            
            # Step 3: Record findings during audit
            finding1_result = audit_service.create_finding(
                finding_data=FindingCreate(
                    audit_id=audit_id,
                    title="Document Control Procedure Missing Approval Signatures",
                    description="Several controlled documents lack required approval signatures",
                    severity="major",
                    category="Document Control",
                    clause_reference="ISO 13485:2016 - 4.2.3",
                    evidence="Documents QP-001, QP-003, QP-007 reviewed during audit",
                    identified_date="2024-03-02",
                    due_date="2024-04-02"
                ),
                current_user_id=lead_auditor.id
            )
            
            assert finding1_result is not None
            finding1_id = finding1_result.id
            
            finding2_result = audit_service.create_finding(
                finding_data=FindingCreate(
                    audit_id=audit_id,
                    title="Training Records Incomplete",
                    description="Training records for 3 employees missing completion dates",
                    severity="minor", 
                    category="Training",
                    clause_reference="ISO 13485:2016 - 6.2.2",
                    evidence="Training database review - employees ID 101, 105, 108",
                    identified_date="2024-03-03",
                    due_date="2024-03-17"
                ),
                current_user_id=audit_team_member.id
            )
            
            assert finding2_result is not None
            finding2_id = finding2_result.id
            
            # Step 4: Create corrective actions
            capa1_result = audit_service.create_corrective_action(
                action_data=CorrectiveActionCreate(
                    finding_id=finding1_id,
                    description="Review and obtain missing approval signatures for all controlled documents",
                    responsible_person=auditee.id,
                    target_date="2024-03-25",
                    priority="high",
                    resources_required="Document owners, Quality Manager approval",
                    success_criteria="All controlled documents have required signatures"
                ),
                current_user_id=quality_manager.id
            )
            
            assert capa1_result is not None
            
            capa2_result = audit_service.create_corrective_action(
                action_data=CorrectiveActionCreate(
                    finding_id=finding2_id,
                    description="Update training records with completion dates and certificates",
                    responsible_person=auditee.id,
                    target_date="2024-03-15",
                    priority="medium",
                    resources_required="HR department, Training certificates",
                    success_criteria="All employee training records complete and up-to-date"
                ),
                current_user_id=quality_manager.id
            )
            
            assert capa2_result is not None
            capa2_id = capa2_result.id
            
            # Step 5: Complete corrective action
            capa2_completion = audit_service.update_corrective_action(
                action_id=capa2_id,
                action_data=CorrectiveActionUpdate(
                    status="completed",
                    actual_completion_date="2024-03-12",
                    effectiveness_check="All training records updated and verified complete",
                    effectiveness_verified_by=lead_auditor.id,
                    effectiveness_verified_date="2024-03-14"
                )
            )
            
            assert capa2_completion is not None
            
            # Step 6: Close finding when corrective action is effective
            finding2_closure = audit_service.update_finding(
                finding_id=finding2_id,
                finding_data=FindingUpdate(
                    status="closed",
                    closed_date="2024-03-14",
                    verified_by=lead_auditor.id,
                    verified_date="2024-03-14"
                )
            )
            
            assert finding2_closure is not None
            
            # Step 7: Complete audit
            audit_completion = audit_service.update_audit(
                audit_id=audit_id,
                audit_data=AuditUpdate(
                    status="completed",
                    actual_end_date="2024-03-07",
                    overall_rating="minor_nc"
                )
            )
            
            assert audit_completion is not None
            
        # Final verification
        with get_db_session() as db:
            audit_service = AuditService(db)
            
            final_audit = audit_service.get_audit(audit_id)
            assert final_audit.status == "completed"
            assert final_audit.overall_rating == "minor_nc"
            
            findings = audit_service.get_findings(audit_id=audit_id)
            assert len(findings) == 2
            
            closed_findings = [f for f in findings if f.status == "closed"]
            open_findings = [f for f in findings if f.status == "open"]
            assert len(closed_findings) == 1
            assert len(open_findings) == 1
            
            actions = audit_service.get_corrective_actions()
            audit_actions = [a for a in actions if a.finding_id in [finding1_id, finding2_id]]
            assert len(audit_actions) == 2
            
            completed_actions = [a for a in audit_actions if a.status == "completed"]
            assert len(completed_actions) == 1
            
        print(f"✅ Complete audit lifecycle test passed:")
        print(f"   - Audit completed: {audit_id}")
        print(f"   - Findings recorded: 2")
        print(f"   - Corrective actions: 2")
        print(f"   - Actions completed: 1")
        print(f"   - Final rating: minor_nc")
```

### 4.2 Performance Test Cases

#### Test Suite: Load Testing
```python
class TestPerformanceAndLoad:
    
    @pytest.mark.performance
    def test_concurrent_user_document_creation(self):
        """Test system performance with multiple concurrent users creating documents"""
        # Given
        num_concurrent_users = 20
        documents_per_user = 5
        
        users = []
        projects = []
        
        # Setup test users and projects
        for i in range(num_concurrent_users):
            user = create_test_user(f"perfuser{i}@example.com")
            project = create_test_project(f"Performance Project {i}", user.id)
            users.append(user)
            projects.append(project)
        
        # When: Simulate concurrent document creation
        import threading
        import time
        
        results = []
        start_time = time.time()
        
        def create_documents_for_user(user_index):
            user = users[user_index]
            project = projects[user_index]
            
            user_results = []
            for doc_index in range(documents_per_user):
                doc_start = time.time()
                
                result = documents_service.create_document(
                    name=f"Performance Document {doc_index}",
                    document_type="process_documents",
                    content=f"# Performance Test Document {doc_index}\n\nContent for load testing.",
                    project_id=project.id,
                    user_id=user.id
                )
                
                doc_end = time.time()
                user_results.append({
                    'success': result.get('success', False),
                    'response_time': doc_end - doc_start
                })
            
            results.append(user_results)
        
        # Execute concurrent operations
        threads = []
        for i in range(num_concurrent_users):
            thread = threading.Thread(target=create_documents_for_user, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Then: Analyze performance results
        flat_results = [item for sublist in results for item in sublist]
        successful_operations = [r for r in flat_results if r['success']]
        response_times = [r['response_time'] for r in successful_operations]
        
        total_operations = num_concurrent_users * documents_per_user
        success_rate = len(successful_operations) / total_operations
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # Performance assertions
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95% threshold"
        assert avg_response_time <= 2.0, f"Average response time {avg_response_time:.2f}s exceeds 2s limit"
        assert max_response_time <= 5.0, f"Max response time {max_response_time:.2f}s exceeds 5s limit"
        
        print(f"✅ Load test results:")
        print(f"   - Total operations: {total_operations}")
        print(f"   - Success rate: {success_rate:.2%}")
        print(f"   - Average response time: {avg_response_time:.3f}s")
        print(f"   - Min/Max response time: {min_response_time:.3f}s / {max_response_time:.3f}s")
        print(f"   - Total execution time: {total_time:.2f}s")
    
    @pytest.mark.performance
    def test_knowledge_base_search_performance(self):
        """Test knowledge base search performance with large dataset"""
        # Given: Large knowledge base collection
        collection = create_test_kb_collection("performance_test")
        
        # Add substantial content
        large_documents = []
        for i in range(100):  # 100 documents
            content = f"""
            Document {i} - Performance Testing Content
            
            This is a comprehensive document for performance testing purposes.
            It contains substantial text content to simulate realistic search scenarios.
            
            Key topics covered:
            - Software development methodologies
            - Quality assurance procedures  
            - Risk management practices
            - Compliance requirements
            - Training protocols
            - Audit procedures
            
            Section 1: Technical Implementation
            The technical implementation involves multiple components working together
            to provide seamless functionality and optimal performance characteristics.
            
            Section 2: Quality Standards
            Quality standards must be maintained throughout the development lifecycle
            to ensure compliance with regulatory requirements and industry best practices.
            
            Section 3: Risk Assessment
            Risk assessment procedures are critical for identifying potential issues
            and implementing appropriate mitigation strategies.
            
            This document contains approximately 500+ words to provide realistic
            content volume for performance testing scenarios.
            """
            
            large_documents.append(content)
            kb_service.add_text_to_collection(
                collection_name="performance_test",
                text_content=content,
                filename=f"perf_doc_{i:03d}.txt",
                metadata={"category": f"category_{i % 5}"}
            )
        
        # When: Perform multiple search operations
        search_queries = [
            "software development methodologies",
            "quality assurance procedures",
            "risk management practices", 
            "compliance requirements",
            "training protocols",
            "audit procedures",
            "technical implementation",
            "performance characteristics",
            "regulatory requirements",
            "mitigation strategies"
        ]
        
        search_results = []
        for query in search_queries:
            start_time = time.time()
            
            result = kb_service.query_knowledge_base(
                message=query,
                collection_name="performance_test"
            )
            
            end_time = time.time()
            
            search_results.append({
                'query': query,
                'success': result.get('success', False),
                'response_time': end_time - start_time,
                'results_count': len(result.get('sources', [])),
                'relevance_score': result.get('sources', [{}])[0].get('score', 0) if result.get('sources') else 0
            })
        
        # Then: Analyze search performance
        successful_searches = [r for r in search_results if r['success']]
        response_times = [r['response_time'] for r in successful_searches]
        
        success_rate = len(successful_searches) / len(search_queries)
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        avg_results_count = sum(r['results_count'] for r in successful_searches) / len(successful_searches)
        
        # Performance assertions
        assert success_rate >= 0.95, f"Search success rate {success_rate:.2%} below 95%"
        assert avg_response_time <= 3.0, f"Average search time {avg_response_time:.2f}s exceeds 3s"
        assert avg_results_count >= 1, f"Average results count {avg_results_count:.1f} too low"
        
        print(f"✅ Knowledge base performance test results:")
        print(f"   - Documents in collection: 100")
        print(f"   - Search queries tested: {len(search_queries)}")
        print(f"   - Success rate: {success_rate:.2%}")
        print(f"   - Average response time: {avg_response_time:.3f}s")
        print(f"   - Min/Max response time: {min_response_time:.3f}s / {max_response_time:.3f}s")
        print(f"   - Average results per query: {avg_results_count:.1f}")
```

### 4.3 Security Test Cases

#### Test Suite: Authentication Security
```python
class TestSecurityAuthentication:
    
    def test_password_security_requirements(self):
        """Test password complexity and security requirements"""
        # Test weak passwords are rejected
        weak_passwords = [
            "123456",
            "password",
            "abc123", 
            "12345678",  # Too simple
            "Pass123",   # Too short
        ]
        
        for weak_password in weak_passwords:
            with pytest.raises(ValueError, match="Password does not meet security requirements"):
                user_service.create_user(
                    username="weakuser",
                    email="weak@example.com",
                    password=weak_password
                )
        
        # Test strong password is accepted
        strong_password = "SecurePassword123!@#"
        user = user_service.create_user(
            username="stronguser",
            email="strong@example.com", 
            password=strong_password
        )
        
        assert user is not None
        assert user.password_hash != strong_password  # Verify hashing
        
        # Test password hashing is consistent but unique
        user2 = user_service.create_user(
            username="stronguser2",
            email="strong2@example.com",
            password=strong_password
        )
        
        assert user.password_hash != user2.password_hash  # Different salts
    
    def test_jwt_token_security(self):
        """Test JWT token security features"""
        # Test token expiration
        user = create_test_user("tokenuser@example.com")
        
        # Create short-lived token
        short_token = auth.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should be valid immediately
        user_id = auth.verify_token(short_token)
        assert user_id == user.id
        
        # Wait for expiration
        time.sleep(2)
        
        # Token should be expired
        with pytest.raises(HTTPException) as exc_info:
            auth.verify_token(short_token)
        assert exc_info.value.status_code == 401
    
    def test_sql_injection_protection(self, test_client):
        """Test protection against SQL injection attacks"""
        # Test login endpoint with SQL injection attempts
        injection_attempts = [
            "admin'--",
            "admin' OR '1'='1",
            "admin'; DROP TABLE users; --",
            "admin' UNION SELECT * FROM users --"
        ]
        
        for injection in injection_attempts:
            response = test_client.post("/auth/login", json={
                "email": injection,
                "password": "anypassword"
            })
            
            # Should return 401, not 500 (which would indicate SQL error)
            assert response.status_code == 401
            assert "Incorrect email or password" in response.json()["detail"]
    
    def test_authorization_enforcement(self, test_client):
        """Test that authorization is properly enforced"""
        # Create users with different roles
        regular_user = create_test_user("regular@example.com")
        admin_user = create_test_user("admin@example.com", is_admin=True)
        super_admin = create_test_user("super@example.com", is_super_admin=True)
        
        # Test regular user cannot access admin endpoints
        regular_headers = get_auth_headers(regular_user.id)
        
        response = test_client.get("/admin/users", headers=regular_headers)
        assert response.status_code == 403
        
        # Test admin cannot access super admin endpoints
        admin_headers = get_auth_headers(admin_user.id)
        
        response = test_client.post("/settings/smtp", headers=admin_headers, json={
            "server_name": "smtp.example.com",
            "port": 587,
            "username": "test@example.com",
            "password": "password",
            "auth_method": "normal_password",
            "connection_security": "STARTTLS",
            "enabled": True
        })
        assert response.status_code == 403
        
        # Test super admin can access all endpoints
        super_headers = get_auth_headers(super_admin.id)
        
        response = test_client.get("/admin/users", headers=super_headers)
        assert response.status_code == 200
        
        response = test_client.get("/settings/smtp", headers=super_headers)
        assert response.status_code == 200
```

#### Test Suite: Data Protection
```python
class TestDataProtection:
    
    def test_sensitive_data_handling(self):
        """Test that sensitive data is properly protected"""
        # Create user with sensitive data
        user = user_service.create_user(
            username="sensitive",
            email="sensitive@example.com",
            password="SensitivePassword123!"
        )
        
        # Verify password is hashed, not stored in plaintext
        db_user = get_user_by_id(user.id)
        assert db_user.password_hash != "SensitivePassword123!"
        assert len(db_user.password_hash) > 50  # bcrypt hash length
        
        # Verify sensitive data not exposed in API responses
        response_user = user_service.get_user_by_id(user.id)
        user_dict = response_user.__dict__
        assert "password" not in user_dict
        assert "password_hash" not in user_dict
    
    def test_project_access_isolation(self):
        """Test that users can only access their authorized projects"""
        # Create separate users and projects
        user1 = create_test_user("user1@example.com")
        user2 = create_test_user("user2@example.com")
        
        project1 = create_test_project("User1 Private Project", user1.id)
        project2 = create_test_project("User2 Private Project", user2.id)
        
        # User1 should not see User2's project
        user1_projects = projects_service.get_user_projects(user1.id)
        project_ids = [p["id"] for p in user1_projects]
        assert project1.id in project_ids
        assert project2.id not in project_ids
        
        # User1 should not access User2's project directly
        project_access = projects_service.get_project(project2.id, user1.id)
        assert project_access is None  # No access
    
    def test_document_access_control(self):
        """Test document access is restricted to project members"""
        # Create users and projects
        project_owner = create_test_user("owner@example.com")
        project_member = create_test_user("member@example.com")
        external_user = create_test_user("external@example.com")
        
        project = create_test_project("Access Control Project", project_owner.id)
        add_project_member(project.id, project_member.id, "member")
        
        # Create document in project
        document = create_test_document("Confidential Document", project.id, project_owner.id)
        
        # Project members should have access
        owner_access = documents_service.get_document(document.id, project_owner.id)
        member_access = documents_service.get_document(document.id, project_member.id)
        
        assert owner_access is not None
        assert member_access is not None
        
        # External user should not have access
        external_access = documents_service.get_document(document.id, external_user.id)
        assert external_access is None
```

## 5. Test Scenarios and Use Cases

### 5.1 Business Process Test Scenarios

#### Scenario: Regulatory Compliance Workflow
```python
def test_regulatory_compliance_workflow():
    """
    Scenario: A medical device company needs to maintain ISO 13485 compliance
    
    Given: A quality management system with document control requirements
    When: Documents are created, reviewed, and approved according to procedures
    Then: Complete audit trail is maintained for regulatory inspection
    """
    
    # Setup: Regulatory environment
    quality_manager = create_test_user("qm@meddevice.com", is_admin=True)
    regulatory_specialist = create_test_user("regulatory@meddevice.com")
    design_engineer = create_test_user("engineer@meddevice.com")
    
    compliance_project = create_test_project("ISO 13485 Compliance", quality_manager.id)
    add_project_member(compliance_project.id, regulatory_specialist.id, "admin")
    add_project_member(compliance_project.id, design_engineer.id, "member")
    
    # Scenario execution
    # 1. Create controlled document template
    template_result = templates_service.create_template(
        name="Design Control Procedure Template",
        description="Template for design control procedures per ISO 13485",
        document_type="process_documents",
        content="# Design Control Procedure\n\n## 7.3.1 Design and Development Planning\n...",
        tags=["ISO13485", "design_control", "template"],
        created_by=quality_manager.id
    )
    
    assert template_result["success"] is True
    template_id = template_result["template_id"]
    
    # 2. Request template approval
    approval_result = templates_service.request_approval(
        template_id=template_id,
        user_id=quality_manager.id,
        approver_ids=[regulatory_specialist.id],
        message="Please review design control template for regulatory compliance"
    )
    
    assert approval_result["success"] is True
    
    # 3. Approve template
    template_approval = templates_service.respond_to_approval(
        template_id=template_id,
        user_id=regulatory_specialist.id,
        approved=True,
        comments="Template meets ISO 13485 requirements, approved for use"
    )
    
    assert template_approval["success"] is True
    
    # 4. Create document from approved template
    document_result = documents_service.create_document(
        name="Design Control Procedure - Software v2.1",
        document_type="process_documents",
        content="# Design Control Procedure - Software v2.1\n\nBased on approved template...",
        project_id=compliance_project.id,
        user_id=design_engineer.id,
        template_id=template_id,
        status="draft"
    )
    
    assert document_result["success"] is True
    document_id = document_result["document_id"]
    
    # 5. Complete review workflow with full audit trail
    review_result = documents_service.update_document(
        document_id=document_id,
        user_id=design_engineer.id,
        status="request_review", 
        reviewers=[regulatory_specialist.id, quality_manager.id],
        comment="Ready for regulatory review and QM approval"
    )
    
    assert review_result["success"] is True
    
    # 6. Regulatory review
    current_revision = get_latest_document_revision(document_id)
    regulatory_review = documents_service.submit_document_review(
        document_id=document_id,
        revision_id=current_revision.id,
        reviewer_id=regulatory_specialist.id,
        approved=True,
        comments="Document complies with ISO 13485:2016 section 7.3 requirements"
    )
    
    assert regulatory_review["success"] is True
    
    # 7. Quality Manager final approval
    qm_review = documents_service.submit_document_review(
        document_id=document_id,
        revision_id=current_revision.id,
        reviewer_id=quality_manager.id,
        approved=True,
        comments="Approved for implementation in QMS"
    )
    
    assert qm_review["success"] is True
    
    # 8. Document approval and knowledge base integration
    final_approval = documents_service.update_document(
        document_id=document_id,
        user_id=quality_manager.id,
        status="approved",
        comment="Document approved and effective immediately"
    )
    
    assert final_approval["success"] is True
    
    # Verification: Complete audit trail exists
    document = get_document_by_id(document_id)
    revisions = get_document_revisions(document_id)
    reviews = get_document_reviews(document_id)
    
    assert document.status == "approved"
    assert len(revisions) >= 1
    assert len(reviews) == 2  # Regulatory + QM reviews
    
    # Verify template lineage
    assert document.template_id == template_id
    
    print("✅ Regulatory compliance workflow completed:")
    print(f"   - Template created and approved: {template_id}")
    print(f"   - Document approved: {document_id}")
    print(f"   - Reviews completed: {len(reviews)}")
    print(f"   - Audit trail complete: {len(revisions)} revisions")
```

#### Scenario: Multi-Project Audit Campaign
```python
def test_multi_project_audit_campaign():
    """
    Scenario: Organization conducts quarterly internal audit across multiple projects
    
    Given: Multiple projects with different audit scopes
    When: Audits are planned, executed, and findings managed
    Then: Consolidated audit results and CAPA tracking
    """
    
    # Setup: Multi-project environment
    audit_manager = create_test_user("audit_manager@company.com", is_admin=True)
    lead_auditor = create_test_user("lead_auditor@company.com")
    auditor1 = create_test_user("auditor1@company.com")
    auditor2 = create_test_user("auditor2@company.com")
    
    # Create multiple projects
    projects = []
    project_managers = []
    
    for i in range(3):
        pm = create_test_user(f"pm{i}@company.com")
        project = create_test_project(f"Product Line {i+1}", pm.id)
        
        # Add audit team to all projects
        add_project_member(project.id, lead_auditor.id, "member")
        add_project_member(project.id, auditor1.id, "member")
        add_project_member(project.id, auditor2.id, "member")
        
        projects.append(project)
        project_managers.append(pm)
    
    # Scenario execution
    audit_results = []
    
    for i, (project, pm) in enumerate(zip(projects, project_managers)):
        # 1. Plan project-specific audit
        with get_db_session() as db:
            audit_service = AuditService(db)
            
            audit_scopes = [
                "Document control and records management",
                "Risk management and design controls", 
                "Supplier management and purchasing controls"
            ]
            
            audit = audit_service.create_audit(
                audit_data=AuditCreate(
                    title=f"Q1 Internal Audit - {project.name}",
                    audit_type="internal",
                    scope=audit_scopes[i],
                    planned_start_date=f"2024-0{i+1}-15",
                    planned_end_date=f"2024-0{i+1}-17", 
                    lead_auditor=lead_auditor.id,
                    audit_team=[auditor1.id if i % 2 == 0 else auditor2.id],
                    auditee_department=f"Product Line {i+1} Team",
                    project_id=project.id
                ),
                current_user_id=audit_manager.id
            )
            
            # 2. Execute audit with findings
            audit_service.update_audit(
                audit_id=audit.id,
                audit_data=AuditUpdate(status="in_progress", actual_start_date=f"2024-0{i+1}-15")
            )
            
            # Create findings based on audit scope
            findings = []
            if i == 0:  # Document control findings
                finding = audit_service.create_finding(
                    finding_data=FindingCreate(
                        audit_id=audit.id,
                        title="Obsolete documents not properly controlled",
                        description="Found 5 obsolete procedures still accessible in work areas",
                        severity="minor",
                        category="Document Control",
                        clause_reference="ISO 13485:2016 - 4.2.3",
                        identified_date=f"2024-0{i+1}-15",
                        due_date=f"2024-0{i+2}-15"
                    ),
                    current_user_id=lead_auditor.id
                )
                findings.append(finding)
            
            elif i == 1:  # Risk management findings
                finding = audit_service.create_finding(
                    finding_data=FindingCreate(
                        audit_id=audit.id,
                        title="Risk analysis not updated for design changes",
                        description="Design changes made without updating risk analysis documentation", 
                        severity="major",
                        category="Risk Management",
                        clause_reference="ISO 14971:2019 - 4.3",
                        identified_date=f"2024-0{i+1}-16",
                        due_date=f"2024-0{i+2}-01"
                    ),
                    current_user_id=auditor1.id
                )
                findings.append(finding)
            
            else:  # Supplier management findings
                finding = audit_service.create_finding(
                    finding_data=FindingCreate(
                        audit_id=audit.id,
                        title="Supplier evaluation records incomplete",
                        description="2 suppliers missing annual evaluation documentation",
                        severity="minor", 
                        category="Supplier Management",
                        clause_reference="ISO 13485:2016 - 7.4.1",
                        identified_date=f"2024-0{i+1}-17",
                        due_date=f"2024-0{i+3}-01"
                    ),
                    current_user_id=auditor2.id
                )
                findings.append(finding)
            
            # 3. Create corrective actions
            for finding in findings:
                action = audit_service.create_corrective_action(
                    action_data=CorrectiveActionCreate(
                        finding_id=finding.id,
                        description=f"Address {finding.title.lower()}",
                        responsible_person=pm.id,
                        target_date=finding.due_date,
                        priority="high" if finding.severity == "major" else "medium"
                    ),
                    current_user_id=audit_manager.id
                )
            
            # 4. Complete audit
            overall_ratings = ["compliant", "minor_nc", "minor_nc"]
            audit_service.update_audit(
                audit_id=audit.id,
                audit_data=AuditUpdate(
                    status="completed",
                    actual_end_date=f"2024-0{i+1}-17",
                    overall_rating=overall_ratings[i]
                )
            )
            
            audit_results.append({
                'audit_id': audit.id,
                'project': project.name,
                'findings_count': len(findings),
                'rating': overall_ratings[i]
            })
    
    # Verification: Campaign results
    with get_db_session() as db:
        audit_service = AuditService(db)
        
        # Verify all audits completed
        all_audits = audit_service.get_audits(status="completed")
        campaign_audits = [a for a in all_audits if "Q1 Internal Audit" in a.title]
        assert len(campaign_audits) == 3
        
        # Verify findings distribution
        all_findings = audit_service.get_findings()
        campaign_findings = [f for a in campaign_audits for f in audit_service.get_findings(audit_id=a.id)]
        assert len(campaign_findings) == 3
        
        # Verify severity distribution
        major_findings = [f for f in campaign_findings if f.severity == "major"]
        minor_findings = [f for f in campaign_findings if f.severity == "minor"]
        assert len(major_findings) == 1  # Risk management
        assert len(minor_findings) == 2  # Document control + Supplier
        
        # Verify corrective actions created
        all_actions = audit_service.get_corrective_actions()
        campaign_actions = [a for f in campaign_findings for a in audit_service.get_corrective_actions(finding_id=f.id)]
        assert len(campaign_actions) == 3
        
    print("✅ Multi-project audit campaign completed:")
    print(f"   - Projects audited: {len(projects)}")
    print(f"   - Audits completed: {len(campaign_audits)}")
    print(f"   - Findings identified: {len(campaign_findings)}")
    print(f"   - Corrective actions: {len(campaign_actions)}")
    for result in audit_results:
        print(f"   - {result['project']}: {result['findings_count']} findings, {result['rating']}")
```

### 5.2 Error Handling and Edge Case Scenarios

#### Scenario: System Recovery and Data Integrity
```python
def test_system_recovery_scenarios():
    """Test system behavior during various failure conditions"""
    
    def test_database_connection_failure():
        """Test graceful handling of database connection issues"""
        # Simulate database connection failure
        with patch('backend.app.database_config.get_db') as mock_get_db:
            mock_get_db.side_effect = ConnectionError("Database connection failed")
            
            # API calls should return proper error responses, not crash
            user = create_test_user("test@example.com")
            with pytest.raises(HTTPException) as exc_info:
                projects_service.create_project("Test Project", "Description", user.id)
            
            assert exc_info.value.status_code == 500
            assert "database" in exc_info.value.detail.lower()
    
    def test_ai_service_unavailable():
        """Test system behavior when AI service is unavailable"""
        # Simulate AI service failure
        with patch('ollama.Client') as mock_client:
            mock_client.side_effect = ConnectionError("Ollama service unavailable")
            
            # Knowledge base operations should degrade gracefully
            result = kb_service.query_knowledge_base(
                message="Test query",
                collection_name="test_collection"
            )
            
            assert result["success"] is False
            assert "AI service" in result["error"]
    
    def test_email_service_failure():
        """Test notification handling when email service fails"""
        # Create project setup
        admin = create_test_user("admin@example.com")
        member = create_test_user("member@example.com") 
        project = create_test_project("Email Test Project", admin.id)
        
        # Simulate email service failure
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = ConnectionError("SMTP server unavailable")
            
            # Member addition should succeed despite email failure
            result = projects_service.add_member(
                project_id=project.id,
                user_id=admin.id,
                new_member_email="member@example.com",
                role="member"
            )
            
            # Core functionality should work
            assert result["success"] is True
            
            # Member should be added to project
            membership = get_project_membership(project.id, member.id)
            assert membership is not None
    
    # Execute all recovery tests
    test_database_connection_failure()
    test_ai_service_unavailable() 
    test_email_service_failure()
    
    print("✅ System recovery scenarios tested successfully")
```

## 6. Test Execution and Reporting

### 6.1 Test Automation Framework
```python
# conftest.py - Test configuration and fixtures
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database_config import get_db, Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "postgresql://test_user:test_pass@localhost/test_docsmait"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup test database before all tests"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Provide database session for tests"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def test_client():
    """Provide test client for API testing"""
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client

@pytest.fixture
def auth_headers(test_client):
    """Provide authentication headers for tests"""
    user = create_test_user("auth_test@example.com")
    login_response = test_client.post("/auth/login", json={
        "email": "auth_test@example.com",
        "password": "TestPassword123!"
    })
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Test execution configuration
pytest.main([
    "--verbose",
    "--tb=short", 
    "--cov=backend/app",
    "--cov-report=html:htmlcov",
    "--cov-report=term-missing",
    "--junit-xml=test-results.xml",
    "tests/"
])
```

### 6.2 Performance Testing Configuration
```python
# pytest.ini - Test configuration
[tool:pytest]
minversion = 6.0
addopts = 
    -ra 
    -q 
    --strict-markers
    --strict-config
    --cov=backend/app
    --cov-branch
    --cov-report=term-missing:skip-covered
    --cov-report=html:htmlcov
    --cov-report=xml
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    security: marks tests as security tests
    unit: marks tests as unit tests
```

### 6.3 Continuous Integration Pipeline
```yaml
# .github/workflows/test.yml
name: Docsmait Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_USER: test_user
          POSTGRES_DB: test_docsmait
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - 6333:6333
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=backend/app --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
        
    - name: Run security tests  
      run: |
        pytest tests/security/ -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        
  performance-tests:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run performance tests
      run: |
        pytest tests/performance/ -v --tb=short
        
    - name: Generate performance report
      run: |
        python scripts/generate_performance_report.py
```

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Test Coverage Target**: 90%+  
**Next Review**: 2024-04-15