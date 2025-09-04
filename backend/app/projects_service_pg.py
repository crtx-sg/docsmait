# backend/app/projects_service_pg.py
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from .database_config import get_db
from .db_models import Project, ProjectMember, ProjectResource, User
from .email_service import email_service
from .activity_log_service import activity_log_service

class ProjectsService:
    """Service for managing projects using PostgreSQL/SQLAlchemy"""
    
    def create_project(self, name: str, description: str, created_by: int) -> Dict[str, Any]:
        """Create a new project"""
        db = next(get_db())
        try:
            # Check if project name already exists
            existing_project = db.query(Project).filter(Project.name == name).first()
            if existing_project:
                return {"success": False, "error": "Project name already exists"}
            
            # Create project
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                name=name,
                description=description,
                created_by=created_by
            )
            db.add(project)
            
            # Add creator as first member with admin role
            membership = ProjectMember(
                project_id=project_id,
                user_id=created_by,
                role="admin",
                added_by=created_by
            )
            db.add(membership)
            
            db.commit()
            
            # Log project creation activity
            activity_log_service.log_project_created(
                user_id=created_by,
                project_id=project_id,  # project_id is now correctly handled as UUID string
                project_name=name,
                db=db
            )
            
            return {
                "success": True,
                "project_id": project_id,
                "message": "Project created successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error creating project: {e}")
            return {"success": False, "error": f"Error creating project: {str(e)}"}
        finally:
            db.close()
    
    def get_user_projects(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all projects where user is a member"""
        db = next(get_db())
        try:
            # Get projects through membership
            memberships = db.query(ProjectMember).options(
                joinedload(ProjectMember.project),
                joinedload(ProjectMember.project).joinedload(Project.creator)
            ).filter(ProjectMember.user_id == user_id).all()
            
            projects = []
            for membership in memberships:
                project = membership.project
                
                # Count project members
                member_count = db.query(ProjectMember).filter(
                    ProjectMember.project_id == project.id
                ).count()
                
                projects.append({
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "created_by": project.created_by,
                    "created_by_username": project.creator.username if project.creator else None,
                    "created_at": project.created_at.isoformat() if project.created_at else None,
                    "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                    "role": membership.role,
                    "member_count": member_count,
                    "is_member": True,  # User is always a member if they're in the list
                    "is_creator": project.created_by == user_id
                })
            
            return projects
            
        except Exception as e:
            print(f"Error getting user projects: {e}")
            return []
        finally:
            db.close()
    
    def get_project(self, project_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get project details if user has access"""
        db = next(get_db())
        try:
            # Check if user is a member
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return None
            
            # Get project with members and resources
            project = db.query(Project).options(
                joinedload(Project.creator),
                joinedload(Project.members).joinedload(ProjectMember.user),
                joinedload(Project.members).joinedload(ProjectMember.added_by_user),
                joinedload(Project.resources)
            ).filter(Project.id == project_id).first()
            
            if not project:
                return None
            
            # Build members list
            members = []
            for member in project.members:
                members.append({
                    "user_id": member.user_id,
                    "username": member.user.username if member.user else None,
                    "email": member.user.email if member.user else None,
                    "role": member.role,
                    "added_at": member.added_at.isoformat() if member.added_at else None,
                    "added_by_username": member.added_by_user.username if member.added_by_user else None
                })
            
            # Build resources list
            resources = []
            try:
                for resource in project.resources:
                    # Get uploader username
                    uploader = db.query(User).filter(User.id == resource.uploaded_by).first()
                    uploaded_by_username = uploader.username if uploader else "Unknown"
                    
                    resources.append({
                        "id": resource.id,
                        "name": resource.name,
                        "resource_type": resource.resource_type,
                        "content": resource.content,
                        "file_path": resource.file_path,
                        "file_size_bytes": resource.file_size_bytes,
                        "content_type": resource.content_type,
                        "uploaded_by": resource.uploaded_by,
                        "uploaded_by_username": uploaded_by_username,
                        "uploaded_at": resource.uploaded_at.isoformat() if resource.uploaded_at else None,
                        "updated_at": resource.updated_at.isoformat() if hasattr(resource, 'updated_at') and resource.updated_at else None
                    })
            except Exception as e:
                print(f"Error loading project resources: {e}")
                resources = []
            
            return {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_by": project.created_by,
                "created_by_username": project.creator.username if project.creator else None,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "members": members,
                "resources": resources,
                "user_role": membership.role,
                "current_user_id": user_id,
                "is_creator": project.created_by == user_id
            }
            
        except Exception as e:
            print(f"Error getting project: {e}")
            return None
        finally:
            db.close()
    
    def add_member(self, project_id: str, user_id: int, new_member_email: str, 
                   role: str = "member") -> Dict[str, Any]:
        """Add a new member to a project"""
        db = next(get_db())
        try:
            # Check if requesting user is admin/creator
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership or membership.role not in ["admin", "creator"]:
                return {"success": False, "error": "Only project admins can add members"}
            
            # Find user by email
            new_user = db.query(User).filter(User.email == new_member_email).first()
            if not new_user:
                return {"success": False, "error": "User not found"}
            
            # Check if already a member
            existing_membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == new_user.id)
            ).first()
            
            if existing_membership:
                return {"success": False, "error": "User is already a member"}
            
            # Add new member
            new_membership = ProjectMember(
                project_id=project_id,
                user_id=new_user.id,
                role=role,
                added_by=user_id
            )
            db.add(new_membership)
            db.commit()
            
            # Log member addition activity
            activity_log_service.log_activity(
                user_id=user_id,
                action=activity_log_service.ACTIONS['ADD_MEMBER'],
                resource_type=activity_log_service.RESOURCES['PROJECT'],
                resource_id=project_id,
                resource_name=project_name,
                description=f"Added {new_user.username} to project with role {role}",
                project_id=project_id,
                db=db
            )
            
            # Get project name for email notification
            project = db.query(Project).filter(Project.id == project_id).first()
            project_name = project.name if project else "Unknown Project"
            
            # Send welcome email notification
            try:
                email_service.send_project_member_welcome(
                    member_user_id=new_user.id,
                    project_name=project_name,
                    added_by_user_id=user_id
                )
            except Exception as e:
                print(f"Failed to send welcome email: {e}")
                # Don't fail the member addition if email fails
            
            return {
                "success": True,
                "message": f"User {new_user.username} added to project"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error adding member: {e}")
            return {"success": False, "error": f"Error adding member: {str(e)}"}
        finally:
            db.close()
    
    def get_project_stats(self, user_id: int) -> Dict[str, Any]:
        """Get project statistics for user"""
        db = next(get_db())
        try:
            # Count user's projects
            project_count = db.query(ProjectMember).filter(ProjectMember.user_id == user_id).count()
            
            # Count projects where user is admin/creator
            admin_count = db.query(ProjectMember).filter(
                and_(ProjectMember.user_id == user_id, ProjectMember.role.in_(["admin", "creator"]))
            ).count()
            
            return {
                "total_projects": project_count,
                "admin_projects": admin_count,
                "member_projects": project_count - admin_count
            }
            
        except Exception as e:
            print(f"Error getting project stats: {e}")
            return {"total_projects": 0, "admin_projects": 0, "member_projects": 0}
        finally:
            db.close()
    
    def update_project(self, project_id: str, user_id: int, **kwargs) -> Dict[str, Any]:
        """Update project (placeholder - not implemented yet)"""
        return {"success": False, "error": "Update project not implemented yet"}
    
    def delete_project(self, project_id: str, user_id: int) -> Dict[str, Any]:
        """Delete project (placeholder - not implemented yet)"""
        return {"success": False, "error": "Delete project not implemented yet"}
    
    def add_project_member(self, project_id: str, user_id: int, member_user_id: int, role: str) -> Dict[str, Any]:
        """Add project member by looking up user email from user_id"""
        db = next(get_db())
        try:
            # Look up the actual user email from the user_id
            user = db.query(User).filter(User.id == member_user_id).first()
            if not user:
                return {"success": False, "error": f"User with ID {member_user_id} not found"}
            
            # Use the real user email
            return self.add_member(project_id, user_id, user.email, role)
        except Exception as e:
            return {"success": False, "error": f"Failed to add project member: {str(e)}"}
        finally:
            db.close()
    
    def remove_project_member(self, project_id: str, user_id: int, target_user_id: int) -> Dict[str, Any]:
        """Remove project member (placeholder - not implemented yet)"""
        return {"success": False, "error": "Remove project member not implemented yet"}
    
    def add_project_resource(self, project_id: str, user_id: int, name: str, 
                            resource_type: str, content: str = "") -> Dict[str, Any]:
        """Add a resource to a project"""
        db = next(get_db())
        try:
            # Check if user is a member of the project
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return {"success": False, "error": "You must be a member of the project to add resources"}
            
            # Create resource
            resource_id = str(uuid.uuid4())
            resource = ProjectResource(
                id=resource_id,
                project_id=project_id,
                name=name,
                resource_type=resource_type,
                content=content,
                uploaded_by=user_id
            )
            db.add(resource)
            db.commit()
            
            # Log resource creation activity
            activity_log_service.log_activity(
                user_id=user_id,
                action=activity_log_service.ACTIONS['CREATE'],
                resource_type=activity_log_service.RESOURCES['PROJECT'],
                resource_id=resource_id,
                resource_name=f"Resource: {name}",
                description=f"Added {resource_type} resource to project",
                project_id=project_id,
                db=db
            )
            
            return {
                "success": True,
                "resource_id": resource_id,
                "message": "Resource added successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error adding project resource: {e}")
            return {"success": False, "error": f"Failed to add resource: {str(e)}"}
        finally:
            db.close()
    
    def update_project_resource(self, resource_id: str, user_id: int, name: str = None, 
                              content: str = None, resource_type: str = None) -> Dict[str, Any]:
        """Update project resource"""
        db = next(get_db())
        try:
            # Get the resource first
            resource = db.query(ProjectResource).filter(
                ProjectResource.id == resource_id
            ).first()
            
            if not resource:
                return {"success": False, "error": "Resource not found"}
            
            # Check if user can update (creator or resource uploader)
            project = db.query(Project).filter(Project.id == resource.project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}
            
            # Check permissions: project creator or resource uploader
            if project.created_by != user_id and resource.uploaded_by != user_id:
                return {"success": False, "error": "Only project creator or resource uploader can update this resource"}
            
            # Update fields if provided
            if name is not None:
                resource.name = name
            if content is not None:
                resource.content = content
            if resource_type is not None:
                resource.resource_type = resource_type
            
            resource.updated_at = datetime.utcnow()
            
            db.commit()
            
            return {
                "success": True,
                "message": "Resource updated successfully",
                "resource_id": resource_id
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error updating project resource: {e}")
            return {"success": False, "error": f"Failed to update resource: {str(e)}"}
        finally:
            db.close()
    
    def delete_project_resource(self, resource_id: str, user_id: int) -> Dict[str, Any]:
        """Delete project resource"""
        db = next(get_db())
        try:
            # Get the resource first
            resource = db.query(ProjectResource).filter(
                ProjectResource.id == resource_id
            ).first()
            
            if not resource:
                return {"success": False, "error": "Resource not found"}
            
            # Check if user can delete (creator or resource uploader)
            project = db.query(Project).filter(Project.id == resource.project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}
            
            # Check permissions: project creator or resource uploader
            if project.created_by != user_id and resource.uploaded_by != user_id:
                return {"success": False, "error": "Only project creator or resource uploader can delete this resource"}
            
            # Delete the resource
            db.delete(resource)
            db.commit()
            
            return {
                "success": True,
                "message": "Resource deleted successfully",
                "resource_id": resource_id
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error deleting project resource: {e}")
            return {"success": False, "error": f"Failed to delete resource: {str(e)}"}
        finally:
            db.close()

# Create global instance
projects_service = ProjectsService()