# backend/app/issues_service_pg.py
import uuid
import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from .database_config import get_db
from .db_models import Issue, IssueComment, User, Project, ProjectMember
from .activity_log_service import activity_log_service
from .email_service import email_service

class IssuesService:
    """Service for managing issues using PostgreSQL/SQLAlchemy"""
    
    def _generate_project_code(self, project_name: str) -> str:
        """Generate a project code from project name"""
        # Remove special characters and convert to uppercase
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', project_name)
        words = clean_name.split()
        
        if len(words) >= 2:
            # Use first letter of first two words
            code = (words[0][0] + words[1][0]).upper()
        elif len(words) == 1 and len(words[0]) >= 3:
            # Use first 3 letters of single word
            code = words[0][:3].upper()
        elif len(words) == 1:
            # Use the whole word if short
            code = words[0].upper()
        else:
            code = "PROJ"
        
        return code[:4]  # Limit to 4 characters
    
    def _generate_issue_number(self, project_id: str, db: Session) -> str:
        """Generate a unique issue number for the project"""
        # Get project info
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found")
        
        project_code = self._generate_project_code(project.name)
        
        # Get the highest issue number for this project
        result = db.query(func.max(Issue.issue_number)).filter(
            Issue.project_id == project_id
        ).scalar()
        
        if result:
            # Extract number from existing issue number (e.g., "PROJ-123" -> 123)
            try:
                last_number = int(result.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"{project_code}-{next_number:03d}"
    
    def create_issue(self, project_id: str, title: str, description: str, 
                    issue_type: str, priority: str, severity: str, version: str,
                    labels: List[str], component: str, due_date: Optional[date],
                    story_points: str, assignees: List[int], comment: str,
                    created_by: int) -> Dict[str, Any]:
        """Create a new issue"""
        db = next(get_db())
        try:
            # Check if user is a member of the project
            membership = db.query(ProjectMember).filter(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == created_by
                )
            ).first()
            
            if not membership:
                return {"success": False, "error": "User is not a member of this project"}
            
            # Generate unique issue number
            issue_number = self._generate_issue_number(project_id, db)
            
            # Create issue
            issue_id = str(uuid.uuid4())
            issue = Issue(
                id=issue_id,
                issue_number=issue_number,
                project_id=project_id,
                title=title,
                description=description,
                issue_type=issue_type,
                priority=priority,
                severity=severity,
                version=version,
                labels=labels,
                component=component,
                due_date=due_date,
                story_points=story_points,
                assignees=assignees,
                created_by=created_by
            )
            db.add(issue)
            
            # Add initial comment if provided
            if comment and comment.strip():
                comment_id = str(uuid.uuid4())
                issue_comment = IssueComment(
                    id=comment_id,
                    issue_id=issue_id,
                    user_id=created_by,
                    comment_text=comment
                )
                db.add(issue_comment)
            
            db.commit()
            
            # Log issue creation activity
            activity_log_service.log_issue_created(
                user_id=created_by,
                issue_id=issue_id,
                issue_title=title,
                project_id=project_id,
                db=db
            )
            
            # Send email notifications
            try:
                # Get project and creator details
                project = db.query(Project).filter(Project.id == project_id).first()
                creator = db.query(User).filter(User.id == created_by).first()
                
                if project and creator:
                    # Get assignee emails
                    assignee_emails = []
                    if assignees:
                        assignee_users = db.query(User).filter(User.id.in_(assignees)).all()
                        assignee_emails = [user.email for user in assignee_users]
                    
                    # Send notification
                    email_service.send_issue_created_notification(
                        project_name=project.name,
                        issue_title=title,
                        issue_number=issue_number,
                        issue_type=issue_type,
                        priority=priority,
                        severity=severity,
                        creator_username=creator.username,
                        assignee_emails=assignee_emails,
                        creator_email=creator.email
                    )
            except Exception as e:
                print(f"Warning: Failed to send issue creation email: {e}")
            
            return {
                "success": True,
                "issue_id": issue_id,
                "issue_number": issue_number,
                "message": f"Issue {issue_number} created successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error creating issue: {e}")
            return {"success": False, "error": f"Error creating issue: {str(e)}"}
        finally:
            db.close()
    
    def get_project_issues(self, project_id: str, user_id: int,
                          status_filter: Optional[str] = None,
                          priority_filter: Optional[str] = None,
                          type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all issues for a project with optional filters"""
        db = next(get_db())
        try:
            # Check if user is a member of the project
            membership = db.query(ProjectMember).filter(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id
                )
            ).first()
            
            if not membership:
                return []
            
            # Build query with filters
            query = db.query(Issue).options(
                joinedload(Issue.creator)
            ).filter(Issue.project_id == project_id)
            
            if status_filter:
                query = query.filter(Issue.status == status_filter)
            if priority_filter:
                query = query.filter(Issue.priority == priority_filter)
            if type_filter:
                query = query.filter(Issue.issue_type == type_filter)
            
            issues = query.order_by(Issue.created_at.desc()).all()
            
            result = []
            for issue in issues:
                # Get assignee usernames
                assignee_usernames = []
                if issue.assignees:
                    assignee_users = db.query(User).filter(User.id.in_(issue.assignees)).all()
                    assignee_usernames = [user.username for user in assignee_users]
                
                # Get comment count
                comment_count = db.query(IssueComment).filter(IssueComment.issue_id == issue.id).count()
                
                result.append({
                    "id": issue.id,
                    "issue_number": issue.issue_number,
                    "title": issue.title,
                    "description": issue.description,
                    "issue_type": issue.issue_type,
                    "priority": issue.priority,
                    "severity": issue.severity,
                    "status": issue.status,
                    "version": issue.version,
                    "labels": issue.labels or [],
                    "component": issue.component,
                    "due_date": issue.due_date.isoformat() if issue.due_date else None,
                    "story_points": issue.story_points,
                    "assignees": issue.assignees or [],
                    "assignee_usernames": assignee_usernames,
                    "created_by": issue.created_by,
                    "creator_username": issue.creator.username,
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "comment_count": comment_count
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting project issues: {e}")
            return []
        finally:
            db.close()
    
    def get_issue(self, issue_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific issue by ID"""
        db = next(get_db())
        try:
            issue = db.query(Issue).options(
                joinedload(Issue.creator),
                joinedload(Issue.project)
            ).filter(Issue.id == issue_id).first()
            
            if not issue:
                return None
            
            # Check if user is a member of the project
            membership = db.query(ProjectMember).filter(
                and_(
                    ProjectMember.project_id == issue.project_id,
                    ProjectMember.user_id == user_id
                )
            ).first()
            
            if not membership:
                return None
            
            # Get assignee usernames
            assignee_usernames = []
            if issue.assignees:
                assignee_users = db.query(User).filter(User.id.in_(issue.assignees)).all()
                assignee_usernames = [user.username for user in assignee_users]
            
            return {
                "id": issue.id,
                "issue_number": issue.issue_number,
                "project_id": issue.project_id,
                "project_name": issue.project.name,
                "title": issue.title,
                "description": issue.description,
                "issue_type": issue.issue_type,
                "priority": issue.priority,
                "severity": issue.severity,
                "status": issue.status,
                "version": issue.version,
                "labels": issue.labels or [],
                "component": issue.component,
                "due_date": issue.due_date.isoformat() if issue.due_date else None,
                "story_points": issue.story_points,
                "assignees": issue.assignees or [],
                "assignee_usernames": assignee_usernames,
                "created_by": issue.created_by,
                "creator_username": issue.creator.username,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None
            }
            
        except Exception as e:
            print(f"Error getting issue: {e}")
            return None
        finally:
            db.close()
    
    def update_issue(self, issue_id: str, user_id: int, **updates) -> Dict[str, Any]:
        """Update an issue"""
        db = next(get_db())
        try:
            issue = db.query(Issue).filter(Issue.id == issue_id).first()
            
            if not issue:
                return {"success": False, "error": "Issue not found"}
            
            # Check if user is a member of the project
            membership = db.query(ProjectMember).filter(
                and_(
                    ProjectMember.project_id == issue.project_id,
                    ProjectMember.user_id == user_id
                )
            ).first()
            
            if not membership:
                return {"success": False, "error": "User is not a member of this project"}
            
            # Update fields
            for field, value in updates.items():
                if hasattr(issue, field) and value is not None:
                    setattr(issue, field, value)
            
            # Handle status changes
            if 'status' in updates and updates['status'] in ['closed', 'resolved']:
                issue.closed_at = datetime.utcnow()
            elif 'status' in updates and updates['status'] in ['open', 'in_progress']:
                issue.closed_at = None
            
            db.commit()
            
            # Log issue update activity
            activity_log_service.log_issue_updated(
                user_id=user_id,
                issue_id=issue_id,
                issue_title=issue.title,
                project_id=issue.project_id,
                db=db
            )
            
            # Send email notifications
            try:
                # Get project, updater, creator, and assignee details
                project = db.query(Project).filter(Project.id == issue.project_id).first()
                updater = db.query(User).filter(User.id == user_id).first()
                creator = db.query(User).filter(User.id == issue.created_by).first()
                
                if project and updater:
                    # Get assignee emails
                    assignee_emails = []
                    if issue.assignees:
                        assignee_users = db.query(User).filter(User.id.in_(issue.assignees)).all()
                        assignee_emails = [user.email for user in assignee_users]
                    
                    # Send notification
                    email_service.send_issue_updated_notification(
                        project_name=project.name,
                        issue_title=issue.title,
                        issue_number=issue.issue_number,
                        issue_type=issue.issue_type,
                        priority=issue.priority,
                        severity=issue.severity,
                        status=issue.status,
                        updated_by_username=updater.username,
                        assignee_emails=assignee_emails,
                        creator_email=creator.email if creator else None
                    )
            except Exception as e:
                print(f"Warning: Failed to send issue update email: {e}")
            
            return {"success": True, "message": "Issue updated successfully"}
            
        except Exception as e:
            db.rollback()
            print(f"Error updating issue: {e}")
            return {"success": False, "error": f"Error updating issue: {str(e)}"}
        finally:
            db.close()
    
    def delete_issue(self, issue_id: str, user_id: int) -> Dict[str, Any]:
        """Delete an issue"""
        db = next(get_db())
        try:
            issue = db.query(Issue).filter(Issue.id == issue_id).first()
            
            if not issue:
                return {"success": False, "error": "Issue not found"}
            
            # Check if user is a member of the project and has permission
            membership = db.query(ProjectMember).filter(
                and_(
                    ProjectMember.project_id == issue.project_id,
                    ProjectMember.user_id == user_id
                )
            ).first()
            
            if not membership or (issue.created_by != user_id and membership.role not in ["admin"]):
                return {"success": False, "error": "Insufficient permissions to delete this issue"}
            
            # Store issue info for logging
            issue_title = issue.title
            project_id = issue.project_id
            
            # Delete issue (cascading delete will handle comments)
            db.delete(issue)
            db.commit()
            
            # Log issue deletion activity
            activity_log_service.log_issue_deleted(
                user_id=user_id,
                issue_id=issue_id,
                issue_title=issue_title,
                project_id=project_id,
                db=db
            )
            
            return {"success": True, "message": "Issue deleted successfully"}
            
        except Exception as e:
            db.rollback()
            print(f"Error deleting issue: {e}")
            return {"success": False, "error": f"Error deleting issue: {str(e)}"}
        finally:
            db.close()
    
    def add_comment(self, issue_id: str, user_id: int, comment_text: str) -> Dict[str, Any]:
        """Add a comment to an issue"""
        db = next(get_db())
        try:
            issue = db.query(Issue).filter(Issue.id == issue_id).first()
            
            if not issue:
                return {"success": False, "error": "Issue not found"}
            
            # Check if user is a member of the project
            membership = db.query(ProjectMember).filter(
                and_(
                    ProjectMember.project_id == issue.project_id,
                    ProjectMember.user_id == user_id
                )
            ).first()
            
            if not membership:
                return {"success": False, "error": "User is not a member of this project"}
            
            # Create comment
            comment_id = str(uuid.uuid4())
            comment = IssueComment(
                id=comment_id,
                issue_id=issue_id,
                user_id=user_id,
                comment_text=comment_text
            )
            db.add(comment)
            db.commit()
            
            return {
                "success": True,
                "comment_id": comment_id,
                "message": "Comment added successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error adding comment: {e}")
            return {"success": False, "error": f"Error adding comment: {str(e)}"}
        finally:
            db.close()
    
    def get_issue_comments(self, issue_id: str, user_id: int) -> List[Dict[str, Any]]:
        """Get all comments for an issue"""
        db = next(get_db())
        try:
            issue = db.query(Issue).filter(Issue.id == issue_id).first()
            
            if not issue:
                return []
            
            # Check if user is a member of the project
            membership = db.query(ProjectMember).filter(
                and_(
                    ProjectMember.project_id == issue.project_id,
                    ProjectMember.user_id == user_id
                )
            ).first()
            
            if not membership:
                return []
            
            comments = db.query(IssueComment).options(
                joinedload(IssueComment.user)
            ).filter(IssueComment.issue_id == issue_id).order_by(IssueComment.created_at.asc()).all()
            
            return [
                {
                    "id": comment.id,
                    "comment_text": comment.comment_text,
                    "user_id": comment.user_id,
                    "username": comment.user.username,
                    "created_at": comment.created_at.isoformat(),
                    "updated_at": comment.updated_at.isoformat()
                }
                for comment in comments
            ]
            
        except Exception as e:
            print(f"Error getting issue comments: {e}")
            return []
        finally:
            db.close()

# Create service instance
issues_service = IssuesService()