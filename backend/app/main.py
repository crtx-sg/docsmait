# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload
from . import models, services, auth
from .user_service import user_service
from .config import config
from .kb_service_pg import kb_service
from .projects_service_pg import projects_service
from .templates_service_pg import templates_service
from .documents_service import documents_service
from .documents_service_v2 import documents_service_v2
from .ai_service import ai_service
from .ai_config import ai_config
from .audit_service import AuditService
from .code_review_service import CodeReviewService
from .project_export_service import project_export_service
from .activity_log_service import activity_log_service
from .records_service import records_service
from .database_config import get_db
from .database_service import db_service
from .init_db import init_database
from datetime import timedelta
from typing import List, Optional

app = FastAPI(title="Docsmait API")

# Initialize services
# projects_service imported from projects_service_pg module
# templates_service imported from templates_service_pg module
# documents_service imported from documents_service module

@app.on_event("startup")
async def startup_event():
    # Initialize PostgreSQL database
    print("🚀 Starting Docsmait API server...")
    if not init_database():
        print("❌ Error: PostgreSQL database initialization failed")
        print("⚠️  This may be normal on first startup. Run setup script if needed.")
    else:
        print("✅ Database initialized successfully")

@app.get("/health")
def health_check():
    """Health check endpoint to verify system status"""
    try:
        from .database_config import engine
        from .db_models import User
        from sqlalchemy import text
        
        # Check database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Check if admin user exists
        db = next(get_db())
        try:
            admin_count = db.query(User).filter(User.is_admin == True).count()
            has_admin = admin_count > 0
        finally:
            db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "admin_users": admin_count,
            "setup_required": not has_admin,
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "setup_required": True
        }

@app.get("/settings")
def get_settings():
    return {
        "general_llm": config.GENERAL_PURPOSE_LLM,
        "embedding_model": config.EMBEDDING_MODEL,
        "vector_db": config.VECTOR_DB,
    }


@app.post("/kb/add_document")
def add_document(doc: models.KBDocumentUpload):
    return services.add_document_to_kb(doc)

@app.post("/kb/query")
def query_kb(query: models.KnowledgeBaseQuery):
    return {"response": services.query_knowledge_base(query)}

@app.post("/auth/signup", response_model=models.Token)
def signup(user_data: models.UserSignup):
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    if user_service.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Username uniqueness is handled in user_service.create_user
    
    # First user automatically becomes admin (handled in user_service.create_user)
    user = user_service.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        is_admin=False  # First user logic handled in user_service
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=models.Token)
def login(user_data: models.UserLogin):
    user = user_service.authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Log login activity
    activity_log_service.log_user_login(
        user_id=user.id
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=models.User)
def get_current_user(user_id: int = Depends(auth.verify_token)):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# Knowledge Base Endpoints
@app.post("/kb/config")
def update_kb_config(config: models.KBConfig, user_id: int = Depends(auth.verify_token)):
    """Update Knowledge Base configuration"""
    kb_service.update_config("chunk_size", str(config.chunk_size))
    kb_service.update_config("default_collection", config.collection_name)
    return {"message": "Configuration updated successfully", "config": config}

@app.get("/kb/config")
def get_kb_config(user_id: int = Depends(auth.verify_token)):
    """Get Knowledge Base configuration"""
    chunk_size = int(kb_service.get_config("chunk_size", "1000"))
    collection_name = kb_service.get_config("default_collection", config.DEFAULT_COLLECTION_NAME)
    return {"chunk_size": chunk_size, "collection_name": collection_name}

@app.post("/kb/upload")
def upload_document(
    collection_name: str = Form(config.DEFAULT_COLLECTION_NAME),
    file: UploadFile = File(...),
    user_id: int = Depends(auth.verify_token)
):
    """Upload and process a document"""
    result = kb_service.process_document(file, collection_name)
    return result

@app.post("/kb/add_text")
def add_text_to_kb(
    collection_name: str,
    text_content: str,
    filename: str,
    metadata: dict = None,
    user_id: int = Depends(auth.verify_token)
):
    """Add text content directly to knowledge base"""
    result = kb_service.add_text_to_collection(collection_name, text_content, filename, metadata)
    return result

@app.post("/kb/chat", response_model=models.ChatResponse)
def chat_with_kb(message: models.ChatMessage, user_id: int = Depends(auth.verify_token)):
    """Chat with Knowledge Base using RAG"""
    result = kb_service.query_knowledge_base(message.message, message.collection_name)
    return result

@app.get("/kb/stats", response_model=models.KBStats)
def get_kb_statistics(user_id: int = Depends(auth.verify_token)):
    """Get Knowledge Base statistics"""
    return kb_service.get_statistics()

@app.post("/kb/reset")
def reset_knowledge_base(
    collection_name: str = config.DEFAULT_COLLECTION_NAME, 
    user_id: int = Depends(auth.verify_token)
):
    """Reset Knowledge Base (admin only)"""
    user = user_service.get_user_by_id(user_id)
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    success = kb_service.reset_knowledge_base(collection_name)
    return {"message": "Knowledge Base reset successfully", "success": success}

# ========== Collection Management Endpoints ==========

@app.post("/kb/collections", response_model=dict)
def create_collection(
    collection: models.CollectionCreate, 
    user_id: int = Depends(auth.verify_token)
):
    """Create a new collection"""
    user = user_service.get_user_by_id(user_id)
    return kb_service.create_collection(
        name=collection.name,
        description=collection.description,
        tags=collection.tags,
        created_by=user.username if user else None
    )

@app.get("/kb/collections", response_model=List[dict])
def list_collections(user_id: int = Depends(auth.verify_token)):
    """List all collections"""
    return kb_service.list_collections()

@app.get("/kb/collections/{collection_name}", response_model=dict)
def get_collection(collection_name: str, user_id: int = Depends(auth.verify_token)):
    """Get collection details with documents"""
    return kb_service.get_collection(collection_name)

@app.post("/kb/collections/{collection_name}/set-default")
def set_default_collection(collection_name: str, user_id: int = Depends(auth.verify_token)):
    """Set a collection as the default collection"""
    return kb_service.set_default_collection(collection_name)

@app.put("/kb/collections/{collection_name}", response_model=dict)
def update_collection(
    collection_name: str,
    collection: models.CollectionUpdate,
    user_id: int = Depends(auth.verify_token)
):
    """Update collection metadata"""
    return kb_service.update_collection(
        collection_name=collection_name,
        description=collection.description,
        tags=collection.tags
    )

@app.delete("/kb/collections/{collection_name}")
def delete_collection(
    collection_name: str,
    force: bool = False,
    user_id: int = Depends(auth.verify_token)
):
    """Delete a collection"""
    user = user_service.get_user_by_id(user_id)
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to delete collections"
        )
    
    return kb_service.delete_collection(collection_name, force)

# ========== Document Management Endpoints ==========

@app.get("/kb/documents/{document_id}", response_model=dict)
def get_kb_document(document_id: str, user_id: int = Depends(auth.verify_token)):
    """Get KB document details"""
    return kb_service.get_document_details(document_id)

@app.delete("/kb/documents/{document_id}")
def delete_document(document_id: str, user_id: int = Depends(auth.verify_token)):
    """Delete a document"""
    return kb_service.delete_document(document_id)

# ========== Training Endpoints ==========

@app.get("/training/test")
def test_training_endpoints():
    """Test endpoint to verify training routes are working"""
    return {"success": True, "message": "Training endpoints are active"}

@app.post("/training/learning")
def generate_learning_content(request: models.TrainingLearningRequest, user_id: int = Depends(auth.verify_token)):
    """Generate comprehensive learning content from multiple KB collections"""
    try:
        print(f"Training learning request received: topics={request.topics}")
        
        # Check if multi-topic method exists, otherwise fallback to single topic
        if hasattr(kb_service, 'generate_learning_content_multi_topics'):
            result = kb_service.generate_learning_content_multi_topics(request.topics)
        else:
            # Fallback: use first topic only
            if request.topics:
                result = kb_service.generate_learning_content(request.topics[0])
            else:
                result = {"success": False, "error": "No topics provided"}
        
        print(f"Training learning result: success={result.get('success')}")
        return result
    except Exception as e:
        print(f"Training learning error: {e}")
        return {"success": False, "error": f"Internal error: {str(e)}"}

@app.post("/training/assessment")
def generate_assessment_questions(request: models.TrainingAssessmentRequest, user_id: int = Depends(auth.verify_token)):
    """Generate True/False questions from multiple KB collections"""
    try:
        print(f"Training assessment request received: topics={request.topics}, num_questions={request.num_questions}")
        
        # Check if multi-topic method exists, otherwise fallback to single topic
        if hasattr(kb_service, 'generate_assessment_questions_multi_topics'):
            result = kb_service.generate_assessment_questions_multi_topics(request.topics, request.num_questions)
        else:
            # Fallback: use first topic only
            if request.topics:
                result = kb_service.generate_assessment_questions(request.topics[0], request.num_questions)
            else:
                result = {"success": False, "error": "No topics provided"}
        
        print(f"Training assessment result: success={result.get('success')}")
        return result
    except Exception as e:
        print(f"Training assessment error: {e}")
        return {"success": False, "error": f"Internal error: {str(e)}"}

@app.post("/training/assessment/submit")
def submit_assessment(request: models.AssessmentSubmissionRequest, user_id: int = Depends(auth.verify_token)):
    """Submit assessment answers and get evaluation"""
    return kb_service.evaluate_assessment(request.question_ids, request.answers, user_id)

@app.get("/training/results")
def get_training_results(user_id: int = Depends(auth.verify_token)):
    """Get training results for authenticated user"""
    try:
        
        result = kb_service.get_user_training_results(user_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ========== Projects Management Endpoints ==========

@app.post("/projects", response_model=dict)
def create_project(project: models.ProjectCreate, user_id: int = Depends(auth.verify_token)):
    """Create a new project"""
    return projects_service.create_project(project.name, project.description, user_id)

@app.get("/projects/stats")
def get_projects_statistics(user_id: int = Depends(auth.verify_token)):
    """Get projects statistics for user"""
    return projects_service.get_project_stats(user_id)

@app.get("/projects", response_model=List[models.ProjectResponse])
def list_user_projects(user_id: int = Depends(auth.verify_token)):
    """Get all projects where user is a member"""
    projects = projects_service.get_user_projects(user_id)
    
    # Convert to response model format
    response_projects = []
    for project in projects:
        response_projects.append(models.ProjectResponse(
            id=project["id"],
            name=project["name"],
            description=project["description"],
            created_by=project["created_by"],
            created_by_username=project["created_by_username"],
            created_at=project["created_at"],
            updated_at=project["updated_at"],
            member_count=project["member_count"],
            is_member=project["is_member"],
            is_creator=project["is_creator"]
        ))
    
    return response_projects

@app.get("/projects/{project_id}", response_model=dict)
def get_project_details(project_id: str, user_id: int = Depends(auth.verify_token)):
    """Get detailed project information"""
    project = projects_service.get_project(project_id, user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    return project

@app.put("/projects/{project_id}", response_model=dict)
def update_project(
    project_id: str,
    project_update: models.ProjectUpdate,
    user_id: int = Depends(auth.verify_token)
):
    """Update project (creator only)"""
    result = projects_service.update_project(
        project_id, user_id, project_update.name, project_update.description
    )
    if not result["success"]:
        if "creator" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "already exists" in result["error"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result

@app.delete("/projects/{project_id}")
def delete_project(project_id: str, user_id: int = Depends(auth.verify_token)):
    """Delete project (creator only)"""
    result = projects_service.delete_project(project_id, user_id)
    if not result["success"]:
        if "creator" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result

@app.post("/projects/{project_id}/members")
def add_project_member(
    project_id: str,
    member: models.ProjectMemberAdd,
    user_id: int = Depends(auth.verify_token)
):
    """Add member to project (creator/admin only)"""
    result = projects_service.add_project_member(project_id, user_id, member.user_id, member.role)
    if not result["success"]:
        if "permission" in result["error"] or "admin" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "already a member" in result["error"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result

@app.post("/projects/{project_id}/members/by-email")
def add_project_member_by_email(
    project_id: str,
    member: models.ProjectMemberAddByEmail,
    user_id: int = Depends(auth.verify_token)
):
    """Add member to project by email (creator/admin only)"""
    result = projects_service.add_member(project_id, user_id, member.email, member.role)
    if not result["success"]:
        if "permission" in result["error"] or "admin" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        if "already a member" in result["error"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result

@app.delete("/projects/{project_id}/members/{target_user_id}")
def remove_project_member(
    project_id: str,
    target_user_id: int,
    user_id: int = Depends(auth.verify_token)
):
    """Remove member from project (creator/admin only)"""
    result = projects_service.remove_project_member(project_id, user_id, target_user_id)
    if not result["success"]:
        if "permission" in result["error"] or "admin" in result["error"] or "creator" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result

@app.post("/projects/{project_id}/resources")
def add_project_resource(
    project_id: str,
    resource: models.ProjectResourceCreate,
    user_id: int = Depends(auth.verify_token)
):
    """Add resource to project"""
    result = projects_service.add_project_resource(
        project_id, user_id, resource.name, resource.resource_type, resource.content
    )
    if not result["success"]:
        if "not a member" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result

@app.put("/projects/{project_id}/resources/{resource_id}")
def update_project_resource(
    project_id: str,
    resource_id: str,
    resource: models.ProjectResourceCreate,
    user_id: int = Depends(auth.verify_token)
):
    """Update project resource"""
    result = projects_service.update_project_resource(
        resource_id, user_id, resource.name, resource.content, resource.resource_type
    )
    if not result["success"]:
        if "uploader" in result["error"] or "creator" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result

@app.delete("/projects/{project_id}/resources/{resource_id}")
def delete_project_resource(
    project_id: str,
    resource_id: str,
    user_id: int = Depends(auth.verify_token)
):
    """Delete project resource"""
    result = projects_service.delete_project_resource(resource_id, user_id)
    if not result["success"]:
        if "uploader" in result["error"] or "creator" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result

@app.post("/projects/{project_id}/export-documents")
def export_project_documents(
    project_id: str,
    export_config: dict,
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Export comprehensive project documentation package"""
    from fastapi.responses import Response
    
    try:
        
        # Call the export service
        result = project_export_service.export_project_documents(
            project_id=project_id,
            export_config=export_config,
            user_id=user_id,
            db=db
        )
        
        
        if not result.get("success", False):
            error_msg = result.get("error", "Export failed")
            if "access denied" in error_msg or "not found" in error_msg:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)
        
        # Return file as download response
        archive_content = result.get("archive_content")
        filename = result.get("filename", "project_export.zip")
        mime_type = result.get("mime_type", "application/zip")
        
        if archive_content:
            return Response(
                content=archive_content,
                media_type=mime_type,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(archive_content))
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to generate archive content"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@app.get("/projects/{project_id}/export-status")
def get_export_status():
    """Get export feature status"""
    return {"available": True, "reason": "Export feature is now available"}

@app.get("/users")
def get_all_users(user_id: int = Depends(auth.verify_token)):
    """Get all users for member selection"""
    from .user_service import user_service
    users = user_service.get_all_users()
    return users

# ========== Template Management Endpoints ==========

@app.post("/templates", response_model=dict)
def create_template(template: models.TemplateCreate, user_id: int = Depends(auth.verify_token)):
    """Create a new template"""
    return templates_service.create_template(
        name=template.name,
        description=template.description,
        document_type=template.document_type,
        content=template.content,
        tags=template.tags,
        created_by=user_id
    )

@app.get("/templates", response_model=List[models.TemplateResponse])
def list_templates(
    status: Optional[str] = None,
    document_type: Optional[str] = None,
    created_by: Optional[int] = None,
    user_id: int = Depends(auth.verify_token)
):
    """List templates with optional filtering"""
    templates = templates_service.list_templates(status, document_type, created_by)
    
    # Convert to response model format
    response_templates = []
    for template in templates:
        response_templates.append(models.TemplateResponse(
            id=template["id"],
            name=template["name"],
            description=template["description"],
            document_type=template["document_type"],
            content=template["content"],
            tags=template["tags"],
            version=template["version"],
            status=template["status"],
            created_by=template["created_by"],
            created_by_username=template["created_by_username"],
            created_at=template["created_at"],
            updated_at=template["updated_at"],
            approved_by=template["approved_by"],
            approved_by_username=template["approved_by_username"],
            approved_at=template["approved_at"]
        ))
    
    return response_templates

@app.get("/templates/{template_id}", response_model=models.TemplateResponse)
def get_template(template_id: str, user_id: int = Depends(auth.verify_token)):
    """Get template details"""
    template = templates_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return models.TemplateResponse(
        id=template["id"],
        name=template["name"],
        description=template["description"],
        document_type=template["document_type"],
        content=template["content"],
        tags=template["tags"],
        version=template["version"],
        status=template["status"],
        created_by=template["created_by"],
        created_by_username=template["created_by_username"],
        created_at=template["created_at"],
        updated_at=template["updated_at"],
        approved_by=template["approved_by"],
        approved_by_username=template["approved_by_username"],
        approved_at=template["approved_at"]
    )

@app.put("/templates/{template_id}", response_model=dict)
def update_template(
    template_id: str,
    template_update: models.TemplateUpdate,
    user_id: int = Depends(auth.verify_token)
):
    """Update template (creator only)"""
    result = templates_service.update_template(
        template_id=template_id,
        user_id=user_id,
        name=template_update.name,
        description=template_update.description,
        document_type=template_update.document_type,
        content=template_update.content,
        tags=template_update.tags,
        status=template_update.status
    )
    
    if not result["success"]:
        if "creator" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result

@app.delete("/templates/{template_id}")
def delete_template(template_id: str, user_id: int = Depends(auth.verify_token)):
    """Delete template (creator only)"""
    result = templates_service.delete_template(template_id, user_id)
    
    if not result["success"]:
        if "creator" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result

@app.post("/templates/{template_id}/request-approval")
def request_template_approval(
    template_id: str,
    approval_request: models.TemplateApprovalRequest,
    user_id: int = Depends(auth.verify_token)
):
    """Request template approval from specified users"""
    result = templates_service.request_approval(
        template_id=template_id,
        user_id=user_id,
        approver_ids=approval_request.approver_ids,
        message=approval_request.message or ""
    )
    
    if not result["success"]:
        if "creator" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result

@app.post("/templates/{template_id}/approve")
def respond_to_template_approval(
    template_id: str,
    approval_response: models.TemplateApprovalResponse,
    user_id: int = Depends(auth.verify_token)
):
    """Respond to template approval request"""
    result = templates_service.respond_to_approval(
        template_id=template_id,
        user_id=user_id,
        approved=approval_response.approved,
        comments=approval_response.comments or ""
    )
    
    if not result["success"]:
        if "No pending approval" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result

@app.get("/templates/approvals/pending")
def get_pending_approvals(user_id: int = Depends(auth.verify_token)):
    """Get templates pending approval for current user"""
    return templates_service.get_pending_approvals(user_id)

@app.get("/templates/document-types")
def get_document_types(user_id: int = Depends(auth.verify_token)):
    """Get available ISO 29845 document types"""
    return templates_service.get_document_types()

@app.post("/templates/{template_id}/export")
def export_template(
    template_id: str,
    export_request: models.TemplateExportRequest,
    user_id: int = Depends(auth.verify_token)
):
    """Export template to specified format"""
    if export_request.format == "pdf":
        result = templates_service.export_to_pdf(template_id, export_request.include_metadata)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format"
        )
    
    if not result["success"]:
        if "not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result

# ========== Document Management Endpoints ==========

@app.post("/projects/{project_id}/documents", response_model=dict)
def create_document(
    project_id: str,
    document: models.DocumentCreate,
    user_id: int = Depends(auth.verify_token)
):
    """Create a new document in a project"""
    result = documents_service.create_document(
        name=document.name,
        document_type=document.document_type,
        content=document.content,
        project_id=project_id,
        user_id=user_id,
        status=document.status,
        template_id=document.template_id,
        comment=document.comment,
        reviewers=document.reviewers or []
    )
    
    if not result.get("success", True):
        if "not a member" in result.get("error", ""):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "already exists" in result.get("error", ""):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result

@app.get("/projects/{project_id}/documents", response_model=List[models.DocumentResponse])
def list_project_documents(
    project_id: str,
    status: Optional[str] = None,
    document_type: Optional[str] = None,
    created_by: Optional[int] = None,
    user_id: int = Depends(auth.verify_token)
):
    """List all documents in a project with optional filtering"""
    documents = documents_service.get_project_documents(
        project_id=project_id,
        user_id=user_id,
        status=status,
        document_type=document_type,
        created_by=created_by
    )
    
    # Convert to response model format
    response_documents = []
    for doc in documents:
        response_documents.append(models.DocumentResponse(
            id=doc["id"],
            name=doc["name"],
            document_type=doc["document_type"],
            content=doc.get("content", ""),  # Dont include full content in list
            project_id=doc["project_id"],
            status=doc["status"],
            template_id=doc["template_id"],
            created_by=doc["created_by"],
            created_by_username=doc["created_by_username"],
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            current_revision=doc["current_revision"],
            reviewers=doc["reviewers"],
            reviewed_at=doc["reviewed_at"],
            reviewed_by=doc["reviewed_by"],
            reviewed_by_username=doc.get("reviewed_by_username")
        ))
    
    return response_documents

@app.get("/documents/{document_id}", response_model=models.DocumentResponse)
def get_document(document_id: str, user_id: int = Depends(auth.verify_token)):
    """Get document details"""
    document = documents_service.get_document(document_id, user_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    
    return models.DocumentResponse(
        id=document["id"],
        name=document["name"],
        document_type=document["document_type"],
        content=document["content"],
        project_id=document["project_id"],
        status=document["status"],
        template_id=document["template_id"],
        created_by=document["created_by"],
        created_by_username=document["created_by_username"],
        created_at=document["created_at"],
        updated_at=document["updated_at"],
        current_revision=document["current_revision"],
        reviewers=document["reviewers"],
        reviewed_at=document["reviewed_at"],
        reviewed_by=document["reviewed_by"],
        reviewed_by_username=document["reviewed_by_username"]
    )

@app.put("/documents/{document_id}", response_model=dict)
def update_document(
    document_id: str,
    document_update: models.DocumentUpdate,
    user_id: int = Depends(auth.verify_token)
):
    """Update document (creator only)"""
    result = documents_service.update_document(
        document_id=document_id,
        user_id=user_id,
        name=document_update.name,
        document_type=document_update.document_type,
        content=document_update.content,
        status=document_update.status,
        comment=document_update.comment,
        reviewers=document_update.reviewers
    )
    
    if not result["success"]:
        if "creator" in result["error"] or "edit" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result

@app.delete("/documents/{document_id}")
def delete_document(document_id: str, user_id: int = Depends(auth.verify_token)):
    """Delete document (creator only)"""
    result = documents_service.delete_document(document_id, user_id)
    
    if not result["success"]:
        if "creator" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        if "not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result

@app.get("/documents/{document_id}/revisions", response_model=List[models.DocumentRevisionResponse])
def get_document_revisions(document_id: str, user_id: int = Depends(auth.verify_token)):
    """Get document revision history"""
    revisions = documents_service.get_document_revisions(document_id, user_id)
    
    # Convert to response model format
    response_revisions = []
    for rev in revisions:
        response_revisions.append(models.DocumentRevisionResponse(
            id=rev["id"],
            document_id=document_id,
            revision_number=rev["revision_number"],
            content=rev["content"],
            status=rev["status"],
            comment=rev["comment"],
            created_by=rev["created_by"],
            created_by_username=rev["created_by_username"],
            created_at=rev["created_at"],
            reviewers=rev["reviewers"]
        ))
    
    return response_revisions

# Removed duplicate endpoint - correct one is at line 1186

@app.post("/documents/{document_id}/export")
def export_document(
    document_id: str,
    export_request: models.DocumentExportRequest,
    user_id: int = Depends(auth.verify_token)
):
    """Export document to specified format"""
    if export_request.format == "pdf":
        result = documents_service.export_document_pdf(document_id, user_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format"
        )
    
    if not result["success"]:
        if "not found" in result["error"] or "access denied" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result

# ========== AI Assistant Endpoints ==========

@app.post("/ai/assist", response_model=models.AIAssistResponse)
async def ai_assist_document(
    request: models.AIAssistRequest,
    user_id: int = Depends(auth.verify_token)
):
    """AI-assisted document editing"""
    try:
        success, response, metadata = await ai_service.generate_document_assistance(
            user_id=user_id,
            document_type=request.document_type,
            document_content=request.document_content,
            user_input=request.user_input,
            custom_prompt=request.custom_prompt,
            model=request.model,
            debug_mode=request.debug_mode
        )
        
        return models.AIAssistResponse(
            success=success,
            response=response if success else "",
            error_message=response if not success else None,
            metadata=metadata
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI assistance failed: {str(e)}"
        )

@app.get("/ai/config/prompts")
def get_ai_prompts(user_id: int = Depends(auth.verify_token)):
    """Get all AI prompts configuration"""
    return ai_config.config.get("document_prompts", {})

@app.get("/ai/config/prompts/{document_type}")
def get_document_prompt(
    document_type: str,
    category: Optional[str] = None,
    user_id: int = Depends(auth.verify_token)
):
    """Get prompt for specific document type"""
    prompt = ai_config.get_document_prompt(document_type, category)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt not found for document type: {document_type}"
        )
    return {"document_type": document_type, "category": category, "prompt": prompt}

@app.put("/ai/config/prompts")
def update_document_prompt(
    update: models.AIConfigUpdate,
    user_id: int = Depends(auth.verify_token)
):
    """Update prompt for specific document type"""
    success = ai_config.update_document_prompt(
        document_type=update.document_type,
        prompt=update.prompt,
        category=update.category
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update prompt configuration"
        )
    
    return {"success": True, "message": "Prompt updated successfully"}

@app.get("/ai/config/settings")
def get_ai_settings(user_id: int = Depends(auth.verify_token)):
    """Get AI service settings"""
    settings = ai_config.get_ai_settings()
    # Don't expose sensitive internal URLs to frontend
    safe_settings = {k: v for k, v in settings.items() if k != "ollama_base_url"}
    return safe_settings

@app.put("/ai/config/settings")
def update_ai_settings(
    settings: models.AISettingsUpdate,
    user_id: int = Depends(auth.verify_token)
):
    """Update AI service settings"""
    settings_dict = {k: v for k, v in settings.dict().items() if v is not None}
    success = ai_config.update_ai_settings(settings_dict)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update AI settings"
        )
    
    # Refresh AI service settings
    ai_service.refresh_settings()
    
    return {"success": True, "message": "AI settings updated successfully"}

@app.get("/ai/models")
async def get_available_models(user_id: int = Depends(auth.verify_token)):
    """Get list of available AI models"""
    success, models_list, error = await ai_service.list_available_models()
    
    if not success:
        # Return configured models as fallback
        fallback_models = ai_config.get_available_models()
        return {
            "success": False,
            "models": fallback_models,
            "error": error,
            "source": "fallback_config"
        }
    
    return {
        "success": True,
        "models": models_list,
        "source": "ollama_api"
    }

@app.get("/ai/health")
async def check_ai_health(user_id: int = Depends(auth.verify_token)):
    """Check AI service health"""
    is_healthy = await ai_service.check_ollama_health()
    return {
        "healthy": is_healthy,
        "service": "ollama",
        "base_url": ai_config.get_ai_settings().get("ollama_base_url", "unknown")
    }

@app.post("/ai/feedback")
def submit_ai_feedback(
    feedback: models.AIUsageFeedback,
    user_id: int = Depends(auth.verify_token)
):
    """Submit feedback for AI usage"""
    # Log feedback for analytics
    ai_config.log_ai_usage(
        user_id=user_id,
        document_type="feedback",
        prompt_used="user_feedback",
        response_length=0,
        processing_time=0.0,
        feedback=feedback.feedback_rating
    )
    
    return {"success": True, "message": "Feedback submitted successfully"}

# ========== Review Management Endpoints ==========

@app.get("/projects/{project_id}/reviews")
def get_project_reviews(
    project_id: str,
    status: Optional[str] = None,
    reviewer_id: Optional[int] = None,
    user_id: int = Depends(auth.verify_token)
):
    """Get all reviews for a project with optional filters"""
    reviews = documents_service.get_reviews_for_project(
        project_id=project_id,
        user_id=user_id,
        status_filter=status,
        reviewer_filter=reviewer_id
    )
    return reviews

@app.get("/reviews/queue")
def get_user_review_queue(
    project_id: Optional[str] = None,
    user_id: int = Depends(auth.verify_token)
):
    """Get review queue for current user"""
    try:
        queue = documents_service.get_review_queue_for_user(
            user_id=user_id,
            project_id=project_id
        )
        if queue:
            first_item = queue[0]
        return queue
    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

@app.get("/projects/{project_id}/reviews/submitted")
def get_submitted_reviews(
    project_id: str,
    user_id: int = Depends(auth.verify_token)
):
    """Get all submitted reviews for a project"""
    reviews = documents_service.get_submitted_reviews(project_id, user_id)
    return reviews

@app.get("/projects/{project_id}/reviews/analytics")
def get_review_analytics(
    project_id: str,
    user_id: int = Depends(auth.verify_token)
):
    """Get review analytics for a project"""
    analytics = documents_service.get_review_analytics(project_id, user_id)
    return analytics

@app.post("/documents/{document_id}/reviews")
def submit_document_review(
    document_id: str,
    review: models.DocumentReviewCreate,
    user_id: int = Depends(auth.verify_token)
):
    """Submit a review for a document"""
    result = documents_service.submit_document_review(
        document_id=document_id,
        revision_id=review.revision_id,
        reviewer_id=user_id,
        approved=review.approved,
        comments=review.comments
    )
    
    if not result["success"]:
        if "not assigned" in result["error"] or "already submitted" in result["error"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result

# ========== AUDIT MANAGEMENT ENDPOINTS ==========

@app.post("/audits", response_model=models.AuditResponse)
def create_audit(audit: models.AuditCreate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Create new audit"""
    audit_service = AuditService(db)
    return audit_service.create_audit(audit, user_id)

@app.get("/audits", response_model=List[models.AuditResponse])
def get_audits(project_id: Optional[str] = None, status: Optional[str] = None, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get all audits with optional filtering"""
    audit_service = AuditService(db)
    return audit_service.get_audits(project_id, status)

@app.get("/audits/{audit_id}", response_model=models.AuditResponse)
def get_audit(audit_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get single audit by ID"""
    audit_service = AuditService(db)
    audit = audit_service.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    return audit

@app.put("/audits/{audit_id}", response_model=models.AuditResponse)
def update_audit(audit_id: str, audit_data: models.AuditUpdate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Update existing audit"""
    audit_service = AuditService(db)
    audit = audit_service.update_audit(audit_id, audit_data)
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    return audit

@app.delete("/audits/{audit_id}")
def delete_audit(audit_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Delete audit"""
    audit_service = AuditService(db)
    success = audit_service.delete_audit(audit_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    return {"message": "Audit deleted successfully"}

# === FINDINGS ENDPOINTS ===

@app.post("/findings", response_model=models.FindingResponse)
def create_finding(finding: models.FindingCreate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Create new finding"""
    audit_service = AuditService(db)
    return audit_service.create_finding(finding, user_id)

@app.get("/findings", response_model=List[models.FindingResponse])
def get_findings(audit_id: Optional[str] = None, status: Optional[str] = None, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get findings with optional filtering"""
    audit_service = AuditService(db)
    return audit_service.get_findings(audit_id, status)

@app.get("/findings/{finding_id}", response_model=models.FindingResponse)
def get_finding(finding_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get single finding by ID"""
    audit_service = AuditService(db)
    finding = audit_service.get_finding(finding_id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return finding

@app.put("/findings/{finding_id}", response_model=models.FindingResponse)
def update_finding(finding_id: str, finding_data: models.FindingUpdate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Update existing finding"""
    audit_service = AuditService(db)
    finding = audit_service.update_finding(finding_id, finding_data)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return finding

@app.delete("/findings/{finding_id}")
def delete_finding(finding_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Delete finding"""
    audit_service = AuditService(db)
    success = audit_service.delete_finding(finding_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return {"message": "Finding deleted successfully"}

# === CORRECTIVE ACTIONS ENDPOINTS ===

@app.post("/corrective-actions", response_model=models.CorrectiveActionResponse)
def create_corrective_action(action: models.CorrectiveActionCreate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Create new corrective action"""
    audit_service = AuditService(db)
    return audit_service.create_corrective_action(action, user_id)

@app.get("/corrective-actions", response_model=List[models.CorrectiveActionResponse])
def get_corrective_actions(finding_id: Optional[str] = None, status: Optional[str] = None, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get corrective actions with optional filtering"""
    audit_service = AuditService(db)
    return audit_service.get_corrective_actions(finding_id, status)

@app.get("/corrective-actions/{action_id}", response_model=models.CorrectiveActionResponse)
def get_corrective_action(action_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get single corrective action by ID"""
    audit_service = AuditService(db)
    action = audit_service.get_corrective_action(action_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corrective action not found")
    return action

@app.put("/corrective-actions/{action_id}", response_model=models.CorrectiveActionResponse)
def update_corrective_action(action_id: str, action_data: models.CorrectiveActionUpdate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Update existing corrective action"""
    audit_service = AuditService(db)
    action = audit_service.update_corrective_action(action_id, action_data)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corrective action not found")
    return action

@app.delete("/corrective-actions/{action_id}")
def delete_corrective_action(action_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Delete corrective action"""
    audit_service = AuditService(db)
    success = audit_service.delete_corrective_action(action_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corrective action not found")
    return {"message": "Corrective action deleted successfully"}

# ========== CODE REVIEW MANAGEMENT ENDPOINTS ==========

# === REPOSITORIES ===

@app.post("/repositories", response_model=models.RepositoryResponse)
def create_repository(repo: models.RepositoryCreate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Create new repository"""
    code_review_service = CodeReviewService(db)
    return code_review_service.create_repository(repo, user_id)

@app.get("/repositories", response_model=List[models.RepositoryResponse])
def get_repositories(project_id: Optional[str] = None, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get repositories with optional filtering"""
    code_review_service = CodeReviewService(db)
    return code_review_service.get_repositories(project_id)

@app.get("/repositories/{repository_id}", response_model=models.RepositoryResponse)
def get_repository(repository_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get single repository by ID"""
    code_review_service = CodeReviewService(db)
    repository = code_review_service.get_repository(repository_id)
    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return repository

@app.put("/repositories/{repository_id}", response_model=models.RepositoryResponse)
def update_repository(repository_id: str, repo_data: models.RepositoryUpdate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Update existing repository"""
    code_review_service = CodeReviewService(db)
    repository = code_review_service.update_repository(repository_id, repo_data)
    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return repository

@app.delete("/repositories/{repository_id}")
def delete_repository(repository_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Delete repository"""
    code_review_service = CodeReviewService(db)
    success = code_review_service.delete_repository(repository_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return {"message": "Repository deleted successfully"}

# === PULL REQUESTS ===

@app.post("/pull-requests", response_model=models.PullRequestResponse)
def create_pull_request(pr: models.PullRequestCreate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Create new pull request"""
    code_review_service = CodeReviewService(db)
    return code_review_service.create_pull_request(pr, user_id)

@app.get("/pull-requests", response_model=List[models.PullRequestResponse])
def get_pull_requests(repository_id: Optional[str] = None, status: Optional[str] = None, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get pull requests with optional filtering"""
    code_review_service = CodeReviewService(db)
    return code_review_service.get_pull_requests(repository_id, status)

@app.get("/pull-requests/{pr_id}", response_model=models.PullRequestResponse)
def get_pull_request(pr_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get single pull request by ID"""
    code_review_service = CodeReviewService(db)
    pr = code_review_service.get_pull_request(pr_id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")
    return pr

@app.put("/pull-requests/{pr_id}", response_model=models.PullRequestResponse)
def update_pull_request(pr_id: str, pr_data: models.PullRequestUpdate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Update existing pull request"""
    code_review_service = CodeReviewService(db)
    pr = code_review_service.update_pull_request(pr_id, pr_data)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")
    return pr

@app.delete("/pull-requests/{pr_id}")
def delete_pull_request(pr_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Delete pull request"""
    code_review_service = CodeReviewService(db)
    success = code_review_service.delete_pull_request(pr_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")
    return {"message": "Pull request deleted successfully"}

# === PULL REQUEST FILES ===

@app.get("/pull-requests/{pr_id}/files", response_model=List[models.PullRequestFileResponse])
def get_pr_files(pr_id: str, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get files changed in a pull request"""
    code_review_service = CodeReviewService(db)
    return code_review_service.get_pr_files(pr_id)

@app.post("/pull-requests/{pr_id}/files")
def add_pr_file(pr_id: str, file_path: str = Form(...), file_status: str = Form(...), 
               additions: int = Form(0), deletions: int = Form(0), 
               patch_content: Optional[str] = Form(None),
               user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Add file to pull request"""
    code_review_service = CodeReviewService(db)
    return code_review_service.add_pr_file(pr_id, file_path, file_status, additions, deletions, patch_content)

# === CODE REVIEWS ===

@app.post("/code-reviews", response_model=List[models.CodeReviewResponse])
def create_code_review(review: models.CodeReviewCreate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Create code reviews for multiple reviewers"""
    code_review_service = CodeReviewService(db)
    return code_review_service.create_code_review(review, user_id)

@app.get("/code-reviews", response_model=List[models.CodeReviewResponse])
def get_code_reviews(pr_id: Optional[str] = None, reviewer_id: Optional[int] = None, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get code reviews with optional filtering"""
    code_review_service = CodeReviewService(db)
    return code_review_service.get_code_reviews(pr_id, reviewer_id)

@app.put("/code-reviews/{review_id}", response_model=models.CodeReviewResponse)
def update_code_review(review_id: str, review_data: models.CodeReviewUpdate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Update existing code review"""
    code_review_service = CodeReviewService(db)
    review = code_review_service.update_code_review(review_id, review_data)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code review not found")
    return review

# === CODE COMMENTS ===

@app.post("/code-comments", response_model=models.CodeCommentResponse)
def create_code_comment(comment: models.CodeCommentCreate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Create new code comment"""
    code_review_service = CodeReviewService(db)
    return code_review_service.create_code_comment(comment, user_id)

@app.get("/code-comments", response_model=List[models.CodeCommentResponse])
def get_code_comments(review_id: Optional[str] = None, file_id: Optional[str] = None, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Get code comments with optional filtering"""
    code_review_service = CodeReviewService(db)
    return code_review_service.get_code_comments(review_id, file_id)

@app.put("/code-comments/{comment_id}", response_model=models.CodeCommentResponse)
def update_code_comment(comment_id: str, comment_data: models.CodeCommentUpdate, user_id: int = Depends(auth.verify_token), db: Session = Depends(get_db)):
    """Update existing code comment"""
    code_review_service = CodeReviewService(db)
    comment = code_review_service.update_code_comment(comment_id, comment_data)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code comment not found")
    return comment

# ========== Admin User Management Endpoints ==========

@app.post("/admin/users", response_model=models.User)
def create_admin_user(user_data: models.AdminUserCreate, user_id: int = Depends(auth.verify_token)):
    """Create a new admin user (only super admin can create admin users)"""
    if not user_service.is_super_admin(user_id):
        raise HTTPException(status_code=403, detail="Only super admin can create admin users")
    
    if user_data.password != user_data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    user = user_service.create_admin_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        created_by_user_id=user_id
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="User already exists or creation failed")
    
    return models.User(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        is_super_admin=user.is_super_admin,
        created_at=user.created_at
    )

@app.get("/admin/users", response_model=List[models.User])
def get_all_users(user_id: int = Depends(auth.verify_token)):
    """Get all users (only accessible by super admin)"""
    if not user_service.is_super_admin(user_id):
        raise HTTPException(status_code=403, detail="Only super admin can view all users")
    
    users = user_service.get_all_users()
    return [models.User(**user) for user in users]

@app.put("/admin/users/{target_user_id}/admin-status")
def update_user_admin_status(target_user_id: int, status_data: models.UserAdminStatusUpdate, user_id: int = Depends(auth.verify_token)):
    """Update user admin status (only super admin can change admin status)"""
    if not user_service.is_super_admin(user_id):
        raise HTTPException(status_code=403, detail="Only super admin can change admin status")
    
    success = user_service.update_user_admin_status(
        user_id=target_user_id,
        is_admin=status_data.is_admin,
        updated_by_user_id=user_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update user admin status")
    
    return {"success": True, "message": "User admin status updated successfully"}

# ========== Settings Management Endpoints ==========

@app.get("/settings/smtp")
def get_smtp_settings(user_id: int = Depends(auth.verify_token)):
    """Get SMTP settings (only super admin can access settings)"""
    if not user_service.is_super_admin(user_id):
        raise HTTPException(status_code=403, detail="Only super admin can access settings")
    
    from .settings_service import settings_service
    return settings_service.get_smtp_settings()

@app.post("/settings/smtp")
def update_smtp_settings(smtp_config: models.SMTPConfig, user_id: int = Depends(auth.verify_token)):
    """Update SMTP settings (only super admin can modify settings)"""
    if not user_service.is_super_admin(user_id):
        raise HTTPException(status_code=403, detail="Only super admin can modify settings")
    
    # Update email service with new SMTP settings
    from .email_service import email_service
    
    settings_dict = smtp_config.dict()
    success = email_service.update_smtp_settings(settings_dict, updated_by=user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update SMTP settings"
        )
    
    return {
        "success": True,
        "message": "SMTP settings updated successfully",
        "config": smtp_config.dict()
    }

# ========== Activity Log Endpoints ==========

@app.get("/activity-logs/my")
def get_my_activities(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action_filter: Optional[str] = Query(None),
    resource_type_filter: Optional[str] = Query(None),
    project_id_filter: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get current user's activity logs"""
    try:
        activities = activity_log_service.get_user_activities(
            user_id=user_id,
            limit=limit,
            offset=offset,
            action_filter=action_filter,
            resource_type_filter=resource_type_filter,
            project_id_filter=project_id_filter,
            db=db
        )
        return {
            "success": True,
            "activities": activities,
            "total": len(activities),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity logs: {str(e)}"
        )

@app.get("/activity-logs/project/{project_id}")
def get_project_activities(
    project_id: str,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_id_filter: Optional[int] = Query(None),
    current_user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get activity logs for a specific project (project members and admins only)"""
    try:
        # Check if user has access to this project
        from .db_models import ProjectMember, User
        
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user_id
        ).first()
        
        user = db.query(User).filter(User.id == current_user_id).first()
        if not is_member and not (user and (user.is_admin or user.is_super_admin)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project activity logs"
            )
        
        activities = activity_log_service.get_project_activities(
            project_id=project_id,
            limit=limit,
            offset=offset,
            user_id_filter=user_id_filter,
            db=db
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "activities": activities,
            "total": len(activities),
            "limit": limit,
            "offset": offset
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project activity logs: {str(e)}"
        )

@app.get("/activity-logs/all")
def get_all_activities(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_id_filter: Optional[int] = Query(None),
    action_filter: Optional[str] = Query(None),
    resource_type_filter: Optional[str] = Query(None),
    search_query: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get all activity logs (admin only)"""
    try:
        # Check if user is admin
        from .db_models import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not (user.is_admin or user.is_super_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        activities = activity_log_service.get_all_activities(
            limit=limit,
            offset=offset,
            user_id_filter=user_id_filter,
            action_filter=action_filter,
            resource_type_filter=resource_type_filter,
            search_query=search_query,
            db=db
        )
        
        return {
            "success": True,
            "activities": activities,
            "total": len(activities),
            "limit": limit,
            "offset": offset,
            "filters": {
                "user_id": user_id_filter,
                "action": action_filter,
                "resource_type": resource_type_filter,
                "search": search_query
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity logs: {str(e)}"
        )

@app.get("/activity-logs/stats")
def get_activity_stats(
    user_id_filter: Optional[int] = Query(None),
    days_back: int = Query(30, ge=1, le=365),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get activity statistics"""
    try:
        # Check admin access for system-wide stats
        from .db_models import User
        user = db.query(User).filter(User.id == user_id).first()
        
        # Non-admin users can only see their own stats
        if not user or not (user.is_admin or user.is_super_admin):
            if user_id_filter and user_id_filter != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view your own activity statistics"
                )
            user_id_filter = user_id
        
        from datetime import datetime, timedelta
        start_date = datetime.now() - timedelta(days=days_back)
        end_date = datetime.now()
        
        stats = activity_log_service.get_activity_stats(
            start_date=start_date,
            end_date=end_date,
            user_id_filter=user_id_filter,
            db=db
        )
        
        return {
            "success": True,
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity statistics: {str(e)}"
        )

@app.get("/activity-logs/actions")
def get_available_actions(user_id: int = Depends(auth.verify_token)):
    """Get list of available action types for filtering"""
    return {
        "success": True,
        "actions": list(activity_log_service.ACTIONS.values()),
        "resources": list(activity_log_service.RESOURCES.values())
    }

# ========== Records Management Endpoints ==========

# Supplier Management Endpoints
@app.post("/records/suppliers")
def create_supplier(
    supplier_data: dict,
    user_id: int = Depends(auth.verify_token)
):
    """Create a new supplier record"""
    return records_service.create_supplier(user_id, supplier_data)

@app.get("/records/suppliers")
def get_suppliers(
    approval_status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token)
):
    """Get all suppliers with optional filtering"""
    filters = {"approval_status": approval_status, "risk_level": risk_level, "search": search}
    suppliers = records_service.get_suppliers(user_id, {k: v for k, v in filters.items() if v})
    return {"success": True, "suppliers": suppliers}

@app.put("/records/suppliers/{supplier_id}")
def update_supplier(
    supplier_id: int,
    supplier_data: dict,
    user_id: int = Depends(auth.verify_token)
):
    """Update supplier record"""
    return records_service.update_supplier(user_id, supplier_id, supplier_data)

# Parts & Inventory Management Endpoints
@app.post("/records/parts-inventory")
def create_parts_inventory(
    part_data: dict,
    user_id: int = Depends(auth.verify_token)
):
    """Create a new parts inventory record"""
    return records_service.create_parts_inventory(user_id, part_data)

@app.get("/records/parts-inventory")
def get_parts_inventory(
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    low_stock: Optional[bool] = Query(False),
    search: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token)
):
    """Get all parts inventory with optional filtering"""
    filters = {"status": status, "supplier_id": supplier_id, "low_stock": low_stock, "search": search}
    parts = records_service.get_parts_inventory(user_id, {k: v for k, v in filters.items() if v})
    return {"success": True, "parts": parts}

# Lab Equipment Calibration Endpoints
@app.post("/records/lab-equipment")
def create_lab_equipment(
    equipment_data: dict,
    user_id: int = Depends(auth.verify_token)
):
    """Create a new lab equipment calibration record"""
    return records_service.create_lab_equipment(user_id, equipment_data)

@app.get("/records/lab-equipment")
def get_lab_equipment(
    calibration_status: Optional[str] = Query(None),
    due_soon: Optional[bool] = Query(False),
    search: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token)
):
    """Get all lab equipment with optional filtering"""
    filters = {"calibration_status": calibration_status, "due_soon": due_soon, "search": search}
    equipment = records_service.get_lab_equipment(user_id, {k: v for k, v in filters.items() if v})
    return {"success": True, "equipment": equipment}

# Customer Complaints Endpoints
@app.post("/records/customer-complaints")
def create_customer_complaint(
    complaint_data: dict,
    user_id: int = Depends(auth.verify_token)
):
    """Create a new customer complaint record"""
    return records_service.create_customer_complaint(user_id, complaint_data)

@app.get("/records/customer-complaints")
def get_customer_complaints(
    status: Optional[str] = Query(None),
    mdr_reportable: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token)
):
    """Get all customer complaints with optional filtering"""
    filters = {"status": status, "mdr_reportable": mdr_reportable, "search": search}
    complaints = records_service.get_customer_complaints(user_id, {k: v for k, v in filters.items() if v})
    return {"success": True, "complaints": complaints}

# Non-Conformances Endpoints
@app.post("/records/non-conformances")
def create_non_conformance(
    nc_data: dict,
    user_id: int = Depends(auth.verify_token)
):
    """Create a new non-conformance record"""
    return records_service.create_non_conformance(user_id, nc_data)

@app.get("/records/non-conformances")
def get_non_conformances(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token)
):
    """Get all non-conformances with optional filtering"""
    filters = {"status": status, "severity": severity, "risk_level": risk_level, "search": search}
    ncs = records_service.get_non_conformances(user_id, {k: v for k, v in filters.items() if v})
    return {"success": True, "non_conformances": ncs}

# ================================
# SIMPLIFIED DOCUMENT WORKFLOW V2
# ================================

@app.post("/api/v2/documents")
def create_document_v2(
    name: str,
    document_type: str,
    content: str,
    project_id: str,
    user_id: int = Depends(auth.verify_token)
):
    """Create document in Draft state"""
    result = documents_service_v2.create_document(
        name=name,
        document_type=document_type,
        content=content,
        project_id=project_id,
        user_id=user_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/v2/documents/{document_id}/submit-for-review")
def submit_for_review_v2(
    document_id: str,
    reviewer_id: int,
    comment: str,
    user_id: int = Depends(auth.verify_token)
):
    """Author submits document for review"""
    result = documents_service_v2.submit_for_review(
        document_id=document_id,
        reviewer_id=reviewer_id,
        comment=comment,
        user_id=user_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/v2/documents/{document_id}/submit-review")
def submit_review_v2(
    document_id: str,
    reviewer_comment: str,
    review_decision: str,  # "needs_update" or "approved"
    user_id: int = Depends(auth.verify_token)
):
    """Reviewer submits review"""
    result = documents_service_v2.submit_review(
        document_id=document_id,
        reviewer_comment=reviewer_comment,
        review_decision=review_decision,
        user_id=user_id
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/api/v2/projects/{project_id}/documents/author")
def get_documents_for_author_v2(
    project_id: str,
    user_id: int = Depends(auth.verify_token)
):
    """Get all documents for author"""
    documents = documents_service_v2.get_documents_for_author(user_id, project_id)
    return {"documents": documents}

@app.get("/api/v2/projects/{project_id}/documents/reviewer")
def get_documents_for_reviewer_v2(
    project_id: str,
    user_id: int = Depends(auth.verify_token)
):
    """Get documents assigned to reviewer"""
    documents = documents_service_v2.get_documents_for_reviewer(user_id, project_id)
    return {"documents": documents}

@app.get("/api/v2/projects/{project_id}/documents/approved")
def get_approved_documents_v2(
    project_id: str,
    user_id: int = Depends(auth.verify_token)
):
    """Get all approved documents"""
    documents = documents_service_v2.get_approved_documents(project_id, user_id)
    return {"documents": documents}

@app.get("/api/v2/documents/{document_id}/revisions")
def get_document_revisions_v2(
    document_id: str,
    user_id: int = Depends(auth.verify_token)
):
    """Get revision history for a document"""
    revisions = documents_service_v2.get_document_revisions(document_id, user_id)
    return {"revisions": revisions}

@app.post("/api/v2/documents/{document_id}/revisions")
def create_document_revision_v2(
    document_id: str,
    content: str,
    comment: str = "",
    user_id: int = Depends(auth.verify_token)
):
    """Create a new revision for a document"""
    result = documents_service_v2.create_revision(
        document_id=document_id,
        content=content,
        user_id=user_id,
        comment=comment
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.put("/api/v2/documents/{document_id}/content")
def update_document_content_v2(
    document_id: str,
    content: str,
    create_revision: bool = True,
    comment: str = "",
    user_id: int = Depends(auth.verify_token)
):
    """Update document content with optional revision creation"""
    result = documents_service_v2.update_document_content(
        document_id=document_id,
        content=content,
        user_id=user_id,
        create_revision=create_revision,
        comment=comment
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# ================================
# DESIGN RECORD - SYSTEM REQUIREMENTS
# ================================

@app.get("/design-record/test")
def test_design_record():
    """Test endpoint to verify design-record routes are working"""
    return {"message": "Design Record endpoints are working", "status": "ok"}

@app.get("/design-record/requirements")
def get_system_requirements(
    project_id: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get system requirements for a project"""
    from .db_models import SystemRequirement, ProjectMember, User
    
    try:
        query = db.query(SystemRequirement).options(
            joinedload(SystemRequirement.creator),
            joinedload(SystemRequirement.project)
        )
        
        if project_id:
            # Check if user has access to this project
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            ).first()
            
            user = db.query(User).filter(User.id == user_id).first()
            if not is_member and not (user and (user.is_admin or user.is_super_admin)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to project requirements"
                )
            
            query = query.filter(SystemRequirement.project_id == project_id)
        
        requirements = query.order_by(SystemRequirement.req_id).all()
        
        result = []
        for req in requirements:
            result.append({
                "id": req.id,
                "req_id": req.req_id,
                "req_title": req.req_title,
                "req_description": req.req_description,
                "req_type": req.req_type,
                "req_priority": req.req_priority,
                "req_status": req.req_status,
                "req_version": req.req_version,
                "req_source": req.req_source,
                "acceptance_criteria": req.acceptance_criteria,
                "rationale": req.rationale,
                "assumptions": req.assumptions,
                "project_id": req.project_id,
                "created_by": req.creator.username if req.creator else "Unknown",
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "updated_at": req.updated_at.isoformat() if req.updated_at else None
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch requirements: {str(e)}"
        )

@app.post("/design-record/requirements")
def create_system_requirement(
    requirement_data: dict,
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Create a new system requirement"""
    from .db_models import SystemRequirement, ProjectMember, User
    import uuid
    
    try:
        project_id = requirement_data.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
        
        # Check if user has access to this project
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not is_member and not (user and (user.is_admin or user.is_super_admin)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to create requirements in this project"
            )
        
        # Check if requirement ID already exists in this project
        existing_req = db.query(SystemRequirement).filter(
            SystemRequirement.project_id == project_id,
            SystemRequirement.req_id == requirement_data.get("req_id")
        ).first()
        
        if existing_req:
            raise HTTPException(
                status_code=400, 
                detail=f"Requirement ID '{requirement_data.get('req_id')}' already exists in this project"
            )
        
        # Create new requirement
        requirement_id = str(uuid.uuid4())
        requirement = SystemRequirement(
            id=requirement_id,
            project_id=project_id,
            req_id=requirement_data.get("req_id"),
            req_title=requirement_data.get("req_title"),
            req_description=requirement_data.get("req_description"),
            req_type=requirement_data.get("req_type"),
            req_priority=requirement_data.get("req_priority"),
            req_status=requirement_data.get("req_status", "draft"),
            req_version=requirement_data.get("req_version", "1.0"),
            req_source=requirement_data.get("req_source"),
            acceptance_criteria=requirement_data.get("acceptance_criteria"),
            rationale=requirement_data.get("rationale"),
            assumptions=requirement_data.get("assumptions"),
            created_by=user_id
        )
        
        db.add(requirement)
        db.commit()
        db.refresh(requirement)
        
        return {
            "success": True,
            "requirement_id": requirement_id,
            "message": f"Requirement {requirement.req_id} created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create requirement: {str(e)}"
        )

# ================================
# DESIGN RECORD - HAZARDS & RISKS
# ================================

@app.get("/design-record/hazards")
def get_system_hazards(
    project_id: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get system hazards for a project"""
    from .db_models import SystemHazard, ProjectMember, User
    
    try:
        query = db.query(SystemHazard).options(
            joinedload(SystemHazard.creator),
            joinedload(SystemHazard.project)
        )
        
        if project_id:
            # Check if user has access to this project
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            ).first()
            
            user = db.query(User).filter(User.id == user_id).first()
            if not is_member and not (user and (user.is_admin or user.is_super_admin)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to project hazards"
                )
            
            query = query.filter(SystemHazard.project_id == project_id)
        
        hazards = query.order_by(SystemHazard.hazard_id).all()
        
        result = []
        for hazard in hazards:
            result.append({
                "id": hazard.id,
                "hazard_id": hazard.hazard_id,
                "hazard_title": hazard.hazard_title,
                "hazard_description": hazard.hazard_description,
                "hazard_category": hazard.hazard_category,
                "severity_level": hazard.severity_level,
                "likelihood": hazard.likelihood,
                "risk_rating": hazard.risk_rating,
                "triggering_conditions": hazard.triggering_conditions,
                "operational_context": hazard.operational_context,
                "use_error_potential": hazard.use_error_potential,
                "current_controls": hazard.current_controls,
                "affected_stakeholders": hazard.affected_stakeholders,
                "asil_level": hazard.asil_level,
                "sil_level": hazard.sil_level,
                "project_id": hazard.project_id,
                "created_by": hazard.creator.username if hazard.creator else "Unknown",
                "created_at": hazard.created_at.isoformat() if hazard.created_at else None,
                "updated_at": hazard.updated_at.isoformat() if hazard.updated_at else None
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch hazards: {str(e)}"
        )

@app.post("/design-record/hazards")
def create_system_hazard(
    hazard_data: dict,
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Create a new system hazard"""
    from .db_models import SystemHazard, ProjectMember, User
    import uuid
    
    try:
        project_id = hazard_data.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
        
        # Check if user has access to this project
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not is_member and not (user and (user.is_admin or user.is_super_admin)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to create hazards in this project"
            )
        
        # Check if hazard ID already exists in this project
        existing_hazard = db.query(SystemHazard).filter(
            SystemHazard.project_id == project_id,
            SystemHazard.hazard_id == hazard_data.get("hazard_id")
        ).first()
        
        if existing_hazard:
            raise HTTPException(
                status_code=400, 
                detail=f"Hazard ID '{hazard_data.get('hazard_id')}' already exists in this project"
            )
        
        # Create new hazard
        hazard_id = str(uuid.uuid4())
        hazard = SystemHazard(
            id=hazard_id,
            project_id=project_id,
            hazard_id=hazard_data.get("hazard_id"),
            hazard_title=hazard_data.get("hazard_title"),
            hazard_description=hazard_data.get("hazard_description"),
            hazard_category=hazard_data.get("hazard_category"),
            severity_level=hazard_data.get("severity_level"),
            likelihood=hazard_data.get("likelihood"),
            risk_rating=hazard_data.get("risk_rating"),
            triggering_conditions=hazard_data.get("triggering_conditions"),
            operational_context=hazard_data.get("operational_context"),
            use_error_potential=hazard_data.get("use_error_potential", False),
            current_controls=hazard_data.get("current_controls"),
            affected_stakeholders=hazard_data.get("affected_stakeholders", []),
            asil_level=hazard_data.get("asil_level"),
            sil_level=hazard_data.get("sil_level"),
            created_by=user_id
        )
        
        db.add(hazard)
        db.commit()
        db.refresh(hazard)
        
        return {
            "success": True,
            "hazard_id": hazard_id,
            "message": f"Hazard {hazard.hazard_id} created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create hazard: {str(e)}"
        )



# ================================
# DESIGN RECORD - FMEA ANALYSIS
# ================================

@app.get("/design-record/fmea")
def get_fmea_analyses(
    project_id: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get FMEA analyses for a project"""
    from .db_models import FMEAAnalysis, ProjectMember, User
    
    try:
        query = db.query(FMEAAnalysis).options(
            joinedload(FMEAAnalysis.creator),
            joinedload(FMEAAnalysis.project)
        )
        
        if project_id:
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            ).first()
            
            user = db.query(User).filter(User.id == user_id).first()
            if not is_member and not (user and (user.is_admin or user.is_super_admin)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to project FMEA analyses"
                )
            
            query = query.filter(FMEAAnalysis.project_id == project_id)
        
        fmeas = query.order_by(FMEAAnalysis.fmea_id).all()
        
        result = []
        for fmea in fmeas:
            result.append({
                "id": fmea.id,
                "fmea_id": fmea.fmea_id,
                "fmea_type": fmea.fmea_type,
                "analysis_level": fmea.analysis_level,
                "hierarchy_level": fmea.hierarchy_level,
                "element_id": fmea.element_id,
                "element_function": fmea.element_function,
                "performance_standards": fmea.performance_standards,
                "fmea_team": fmea.fmea_team,
                "analysis_date": str(fmea.analysis_date) if fmea.analysis_date else None,
                "review_status": fmea.review_status,
                "failure_modes": fmea.failure_modes,
                "project_id": fmea.project_id,
                "created_by": fmea.creator.username if fmea.creator else "Unknown",
                "created_at": fmea.created_at.isoformat() if fmea.created_at else None,
                "updated_at": fmea.updated_at.isoformat() if fmea.updated_at else None
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch FMEA analyses: {str(e)}"
        )

@app.post("/design-record/fmea")
def create_fmea_analysis(
    fmea_data: dict,
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Create a new FMEA analysis"""
    from .db_models import FMEAAnalysis, ProjectMember, User
    import uuid
    from datetime import datetime
    
    try:
        project_id = fmea_data.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
        
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not is_member and not (user and (user.is_admin or user.is_super_admin)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to create FMEA analyses in this project"
            )
        
        existing_fmea = db.query(FMEAAnalysis).filter(
            FMEAAnalysis.project_id == project_id,
            FMEAAnalysis.fmea_id == fmea_data.get("fmea_id")
        ).first()
        
        if existing_fmea:
            raise HTTPException(
                status_code=400, 
                detail=f"FMEA ID '{fmea_data.get('fmea_id')}' already exists in this project"
            )
        
        analysis_date = None
        if fmea_data.get("analysis_date"):
            analysis_date = datetime.strptime(fmea_data.get("analysis_date"), "%Y-%m-%d").date()
        
        fmea_id = str(uuid.uuid4())
        fmea = FMEAAnalysis(
            id=fmea_id,
            project_id=project_id,
            fmea_id=fmea_data.get("fmea_id"),
            fmea_type=fmea_data.get("fmea_type"),
            analysis_level=fmea_data.get("analysis_level"),
            hierarchy_level=fmea_data.get("hierarchy_level"),
            element_id=fmea_data.get("element_id"),
            element_function=fmea_data.get("element_function"),
            performance_standards=fmea_data.get("performance_standards"),
            fmea_team=fmea_data.get("fmea_team", []),
            analysis_date=analysis_date,
            review_status=fmea_data.get("review_status", "draft"),
            failure_modes=fmea_data.get("failure_modes", []),
            created_by=user_id
        )
        
        db.add(fmea)
        db.commit()
        db.refresh(fmea)
        
        return {
            "success": True,
            "fmea_id": fmea_id,
            "message": f"FMEA {fmea.fmea_id} created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create FMEA analysis: {str(e)}"
        )

# ================================
# DESIGN RECORD - DESIGN ARTIFACTS
# ================================

@app.get("/design-record/design")
def get_design_artifacts(
    project_id: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get design artifacts for a project"""
    from .db_models import DesignArtifact, ProjectMember, User
    
    try:
        query = db.query(DesignArtifact).options(
            joinedload(DesignArtifact.creator),
            joinedload(DesignArtifact.project)
        )
        
        if project_id:
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            ).first()
            
            user = db.query(User).filter(User.id == user_id).first()
            if not is_member and not (user and (user.is_admin or user.is_super_admin)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to project design artifacts"
                )
            
            query = query.filter(DesignArtifact.project_id == project_id)
        
        designs = query.order_by(DesignArtifact.design_id).all()
        
        result = []
        for design in designs:
            result.append({
                "id": design.id,
                "design_id": design.design_id,
                "design_title": design.design_title,
                "design_type": design.design_type,
                "design_description": design.design_description,
                "implementation_approach": design.implementation_approach,
                "architecture_diagrams": design.architecture_diagrams,
                "interface_definitions": design.interface_definitions,
                "design_patterns": design.design_patterns,
                "technology_stack": design.technology_stack,
                "project_id": design.project_id,
                "created_by": design.creator.username if design.creator else "Unknown",
                "created_at": design.created_at.isoformat() if design.created_at else None,
                "updated_at": design.updated_at.isoformat() if design.updated_at else None
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch design artifacts: {str(e)}"
        )

@app.post("/design-record/design")
def create_design_artifact(
    design_data: dict,
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Create a new design artifact"""
    from .db_models import DesignArtifact, ProjectMember, User
    import uuid
    
    try:
        project_id = design_data.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
        
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not is_member and not (user and (user.is_admin or user.is_super_admin)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to create design artifacts in this project"
            )
        
        existing_design = db.query(DesignArtifact).filter(
            DesignArtifact.project_id == project_id,
            DesignArtifact.design_id == design_data.get("design_id")
        ).first()
        
        if existing_design:
            raise HTTPException(
                status_code=400, 
                detail=f"Design ID '{design_data.get('design_id')}' already exists in this project"
            )
        
        design_id = str(uuid.uuid4())
        design = DesignArtifact(
            id=design_id,
            project_id=project_id,
            design_id=design_data.get("design_id"),
            design_title=design_data.get("design_title"),
            design_type=design_data.get("design_type"),
            design_description=design_data.get("design_description"),
            implementation_approach=design_data.get("implementation_approach"),
            architecture_diagrams=design_data.get("architecture_diagrams", []),
            interface_definitions=design_data.get("interface_definitions", []),
            design_patterns=design_data.get("design_patterns", []),
            technology_stack=design_data.get("technology_stack", []),
            created_by=user_id
        )
        
        db.add(design)
        db.commit()
        db.refresh(design)
        
        return {
            "success": True,
            "design_id": design_id,
            "message": f"Design {design.design_id} created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create design artifact: {str(e)}"
        )

# ================================
# DESIGN RECORD - TEST ARTIFACTS
# ================================

@app.get("/design-record/tests")
def get_test_artifacts(
    project_id: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get test artifacts for a project"""
    from .db_models import TestArtifact, ProjectMember, User
    
    try:
        query = db.query(TestArtifact).options(
            joinedload(TestArtifact.creator),
            joinedload(TestArtifact.project)
        )
        
        if project_id:
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            ).first()
            
            user = db.query(User).filter(User.id == user_id).first()
            if not is_member and not (user and (user.is_admin or user.is_super_admin)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to project test artifacts"
                )
            
            query = query.filter(TestArtifact.project_id == project_id)
        
        tests = query.order_by(TestArtifact.test_id).all()
        
        result = []
        for test in tests:
            result.append({
                "id": test.id,
                "test_id": test.test_id,
                "test_title": test.test_title,
                "test_type": test.test_type,
                "test_objective": test.test_objective,
                "acceptance_criteria": test.acceptance_criteria,
                "test_environment": test.test_environment,
                "test_execution": test.test_execution,
                "coverage_metrics": test.coverage_metrics,
                "project_id": test.project_id,
                "created_by": test.creator.username if test.creator else "Unknown",
                "created_at": test.created_at.isoformat() if test.created_at else None,
                "updated_at": test.updated_at.isoformat() if test.updated_at else None
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch test artifacts: {str(e)}"
        )

@app.post("/design-record/tests")
def create_test_artifact(
    test_data: dict,
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Create a new test artifact"""
    from .db_models import TestArtifact, ProjectMember, User
    import uuid
    
    try:
        project_id = test_data.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
        
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not is_member and not (user and (user.is_admin or user.is_super_admin)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to create test artifacts in this project"
            )
        
        existing_test = db.query(TestArtifact).filter(
            TestArtifact.project_id == project_id,
            TestArtifact.test_id == test_data.get("test_id")
        ).first()
        
        if existing_test:
            raise HTTPException(
                status_code=400, 
                detail=f"Test ID '{test_data.get('test_id')}' already exists in this project"
            )
        
        test_id = str(uuid.uuid4())
        test = TestArtifact(
            id=test_id,
            project_id=project_id,
            test_id=test_data.get("test_id"),
            test_title=test_data.get("test_title"),
            test_type=test_data.get("test_type"),
            test_objective=test_data.get("test_objective"),
            acceptance_criteria=test_data.get("acceptance_criteria"),
            test_environment=test_data.get("test_environment"),
            test_execution=test_data.get("test_execution"),
            coverage_metrics=test_data.get("coverage_metrics"),
            created_by=user_id
        )
        
        db.add(test)
        db.commit()
        db.refresh(test)
        
        return {
            "success": True,
            "test_id": test_id,
            "message": f"Test {test.test_id} created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test artifact: {str(e)}"
        )
