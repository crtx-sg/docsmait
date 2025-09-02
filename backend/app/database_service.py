# backend/app/database_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from .database_config import get_db
from .db_models import User, Project, ProjectMember, ProjectResource, Template, TemplateApproval, Document, DocumentRevision, DocumentReviewer, DocumentReview
from .models import UserSignup, ProjectCreate, TemplateCreate, DocumentCreate

class DatabaseService:
    """SQLAlchemy-based database service replacing raw SQL operations"""
    
    def __init__(self):
        pass
    
    # ========== User Management ==========
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    def email_exists(self, db: Session, email: str) -> bool:
        """Check if email already exists"""
        return db.query(User).filter(User.email == email).first() is not None
    
    def username_exists(self, db: Session, username: str) -> bool:
        """Check if username already exists"""
        return db.query(User).filter(User.username == username).first() is not None
    
    def get_user_count(self, db: Session) -> int:
        """Get total number of users"""
        return db.query(User).count()
    
    def create_user(self, db: Session, username: str, email: str, password_hash: str, is_admin: bool = False) -> User:
        """Create a new user"""
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=is_admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def get_all_users(self, db: Session) -> List[Dict[str, Any]]:
        """Get all users for member selection"""
        users = db.query(User).order_by(User.username).all()
        return [{"id": user.id, "username": user.username, "email": user.email} for user in users]
    
    # ========== Project Management ==========
    
    def create_project(self, db: Session, name: str, description: str, user_id: int) -> Dict[str, Any]:
        """Create a new project"""
        try:
            # Check if project name already exists
            existing = db.query(Project).filter(Project.name == name).first()
            if existing:
                return {"success": False, "error": "Project name already exists"}
            
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                name=name,
                description=description,
                created_by=user_id
            )
            db.add(project)
            
            # Add creator as admin member
            member = ProjectMember(
                project_id=project_id,
                user_id=user_id,
                role="admin",
                added_by=user_id
            )
            db.add(member)
            
            db.commit()
            db.refresh(project)
            
            return {
                "success": True,
                "message": "Project created successfully",
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "created_by": project.created_by,
                    "created_at": project.created_at.isoformat()
                }
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Failed to create project: {str(e)}"}
    
    def get_user_projects(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get all projects where user is a member"""
        projects = db.query(Project).join(ProjectMember).filter(
            ProjectMember.user_id == user_id
        ).all()
        
        result = []
        for project in projects:
            # Get member count
            member_count = db.query(ProjectMember).filter(
                ProjectMember.project_id == project.id
            ).count()
            
            # Check if user is creator
            is_creator = project.created_by == user_id
            
            # Get user's role
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project.id, ProjectMember.user_id == user_id)
            ).first()
            
            result.append({
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_by": project.created_by,
                "created_by_username": project.creator.username,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "member_count": member_count,
                "is_member": True,
                "is_creator": is_creator,
                "role": membership.role if membership else "member"
            })
        
        return result
    
    def get_project_details(self, db: Session, project_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed project information"""
        # Check if user is a member
        membership = db.query(ProjectMember).filter(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        ).first()
        
        if not membership:
            return None
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        
        # Get all members
        members = db.query(ProjectMember, User).join(User).filter(
            ProjectMember.project_id == project_id
        ).all()
        
        member_list = []
        for member, user in members:
            member_list.append({
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": member.role,
                "added_at": member.added_at.isoformat()
            })
        
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_by": project.created_by,
            "created_by_username": project.creator.username,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "members": member_list,
            "user_role": membership.role
        }
    
    # ========== Document Management ==========
    
    def create_document(self, db: Session, name: str, document_type: str, content: str,
                       project_id: str, user_id: int, status: str = "draft",
                       template_id: Optional[str] = None, comment: str = "",
                       reviewers: List[int] = None) -> Dict[str, Any]:
        """Create a new document"""
        try:
            if reviewers is None:
                reviewers = []
            
            # Check if user is a member of the project
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return {"success": False, "error": "You must be a member of the project to create documents"}
            
            # Check if document name exists in project
            existing = db.query(Document).filter(
                and_(Document.project_id == project_id, Document.name == name)
            ).first()
            
            if existing:
                return {"success": False, "error": "A document with this name already exists in the project"}
            
            doc_id = str(uuid.uuid4())
            revision_id = str(uuid.uuid4())
            
            # Create document
            document = Document(
                id=doc_id,
                name=name,
                document_type=document_type,
                content=content,
                project_id=project_id,
                status=status,
                template_id=template_id,
                created_by=user_id,
                current_revision=1
            )
            db.add(document)
            
            # Create first revision
            revision = DocumentRevision(
                id=revision_id,
                document_id=doc_id,
                revision_number=1,
                content=content,
                status=status,
                comment=comment,
                created_by=user_id
            )
            db.add(revision)
            
            # Add reviewers if status is request_review
            if status == "request_review" and reviewers:
                for reviewer_id in reviewers:
                    reviewer = DocumentReviewer(
                        document_id=doc_id,
                        revision_id=revision_id,
                        reviewer_id=reviewer_id,
                        status="pending"
                    )
                    db.add(reviewer)
            
            db.commit()
            return {"success": True, "message": "Document created successfully", "document_id": doc_id}
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Failed to create document: {str(e)}"}

# Create a global instance
db_service = DatabaseService()