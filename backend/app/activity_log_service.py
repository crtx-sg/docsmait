# backend/app/activity_log_service.py
"""
Activity Log Service

This service provides comprehensive activity logging capabilities for tracking
all user actions across the Docsmait application for compliance and audit purposes.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from .database_config import get_db
from .db_models import ActivityLog, User, Project


class ActivityLogService:
    """Service for managing user activity logs"""
    
    # Standard action types
    ACTIONS = {
        # CRUD operations
        'CREATE': 'create',
        'UPDATE': 'update', 
        'DELETE': 'delete',
        'VIEW': 'view',
        
        # Document-specific actions
        'UPLOAD': 'upload',
        'DOWNLOAD': 'download',
        'APPROVE': 'approve',
        'REJECT': 'reject',
        'SUBMIT_FOR_REVIEW': 'submit_for_review',
        'COMPLETE_REVIEW': 'complete_review',
        
        # Project-specific actions
        'JOIN_PROJECT': 'join_project',
        'LEAVE_PROJECT': 'leave_project',
        'ADD_MEMBER': 'add_member',
        'REMOVE_MEMBER': 'remove_member',
        
        # Authentication actions
        'LOGIN': 'login',
        'LOGOUT': 'logout',
        'PASSWORD_CHANGE': 'password_change',
        
        # System actions
        'EXPORT': 'export',
        'IMPORT': 'import',
        'BACKUP': 'backup',
        'RESTORE': 'restore',
        'CONFIG_CHANGE': 'config_change'
    }
    
    # Resource types
    RESOURCES = {
        'USER': 'user',
        'PROJECT': 'project',
        'DOCUMENT': 'document',
        'TEMPLATE': 'template',
        'REVIEW': 'review',
        'CODE_REVIEW': 'code_review',
        'AUDIT': 'audit',
        'TRAINING': 'training',
        'REQUIREMENT': 'requirement',
        'RISK': 'risk',
        'FMEA': 'fmea',
        'TEST_ARTIFACT': 'test_artifact',
        'DESIGN_ARTIFACT': 'design_artifact',
        'KNOWLEDGE_BASE': 'knowledge_base',
        'SYSTEM': 'system'
    }

    def log_activity(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Log a user activity
        
        Args:
            user_id: ID of user performing the action
            action: Action performed (use ACTIONS constants)
            resource_type: Type of resource affected (use RESOURCES constants)
            resource_id: ID of the specific resource
            resource_name: Human-readable name of the resource
            description: Detailed description of the activity
            metadata: Additional contextual information as dict
            project_id: Project ID if action is project-related
            ip_address: User's IP address
            user_agent: User's browser/client info
            db: Database session
            
        Returns:
            bool: True if logged successfully
        """
        try:
            # Get database session if not provided
            if db is None:
                db = next(get_db())
            
            # Create activity log entry
            activity = ActivityLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                resource_name=resource_name,
                description=description or self._generate_description(action, resource_type, resource_name),
                activity_metadata=json.dumps(metadata) if metadata else None,
                project_id=project_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(activity)
            db.commit()
            
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to log activity: {str(e)}")
            if db:
                db.rollback()
            return False

    def get_user_activities(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action_filter: Optional[str] = None,
        resource_type_filter: Optional[str] = None,
        project_id_filter: Optional[str] = None,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """Get activities for a specific user"""
        try:
            if db is None:
                db = next(get_db())
            
            query = db.query(ActivityLog).filter(ActivityLog.user_id == user_id)
            
            # Apply filters
            if start_date:
                query = query.filter(ActivityLog.timestamp >= start_date)
            if end_date:
                query = query.filter(ActivityLog.timestamp <= end_date)
            if action_filter:
                query = query.filter(ActivityLog.action == action_filter)
            if resource_type_filter:
                query = query.filter(ActivityLog.resource_type == resource_type_filter)
            if project_id_filter:
                query = query.filter(ActivityLog.project_id == project_id_filter)
            
            # Order by timestamp descending and apply pagination
            activities = query.order_by(desc(ActivityLog.timestamp)).offset(offset).limit(limit).all()
            
            return [self._activity_to_dict(activity) for activity in activities]
            
        except Exception as e:
            print(f"ERROR: Failed to get user activities: {str(e)}")
            return []

    def get_project_activities(
        self,
        project_id: str,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id_filter: Optional[int] = None,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """Get activities for a specific project"""
        try:
            if db is None:
                db = next(get_db())
            
            query = db.query(ActivityLog).filter(ActivityLog.project_id == project_id)
            
            # Apply filters
            if start_date:
                query = query.filter(ActivityLog.timestamp >= start_date)
            if end_date:
                query = query.filter(ActivityLog.timestamp <= end_date)
            if user_id_filter:
                query = query.filter(ActivityLog.user_id == user_id_filter)
            
            # Join with user to get username
            query = query.join(User)
            
            activities = query.order_by(desc(ActivityLog.timestamp)).offset(offset).limit(limit).all()
            
            return [self._activity_to_dict(activity) for activity in activities]
            
        except Exception as e:
            print(f"ERROR: Failed to get project activities: {str(e)}")
            return []

    def get_all_activities(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id_filter: Optional[int] = None,
        action_filter: Optional[str] = None,
        resource_type_filter: Optional[str] = None,
        search_query: Optional[str] = None,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """Get all activities (admin only)"""
        try:
            if db is None:
                db = next(get_db())
            
            query = db.query(ActivityLog).join(User)
            
            # Apply filters
            if start_date:
                query = query.filter(ActivityLog.timestamp >= start_date)
            if end_date:
                query = query.filter(ActivityLog.timestamp <= end_date)
            if user_id_filter:
                query = query.filter(ActivityLog.user_id == user_id_filter)
            if action_filter:
                query = query.filter(ActivityLog.action == action_filter)
            if resource_type_filter:
                query = query.filter(ActivityLog.resource_type == resource_type_filter)
            
            # Search functionality
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.filter(
                    or_(
                        ActivityLog.resource_name.ilike(search_pattern),
                        ActivityLog.description.ilike(search_pattern),
                        User.username.ilike(search_pattern)
                    )
                )
            
            activities = query.order_by(desc(ActivityLog.timestamp)).offset(offset).limit(limit).all()
            
            return [self._activity_to_dict(activity) for activity in activities]
            
        except Exception as e:
            print(f"ERROR: Failed to get all activities: {str(e)}")
            return []

    def get_activity_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id_filter: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get activity statistics"""
        try:
            if db is None:
                db = next(get_db())
            
            # Default to last 30 days if no dates provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            base_query = db.query(ActivityLog).filter(
                and_(
                    ActivityLog.timestamp >= start_date,
                    ActivityLog.timestamp <= end_date
                )
            )
            
            if user_id_filter:
                base_query = base_query.filter(ActivityLog.user_id == user_id_filter)
            
            # Total activities
            total_activities = base_query.count()
            
            # Activities by action
            action_stats = {}
            for action_type in self.ACTIONS.values():
                count = base_query.filter(ActivityLog.action == action_type).count()
                if count > 0:
                    action_stats[action_type] = count
            
            # Activities by resource type
            resource_stats = {}
            for resource_type in self.RESOURCES.values():
                count = base_query.filter(ActivityLog.resource_type == resource_type).count()
                if count > 0:
                    resource_stats[resource_type] = count
            
            # Most active users (if not filtered by user)
            active_users = []
            if not user_id_filter:
                from sqlalchemy import func
                user_activity_counts = (
                    base_query
                    .join(User)
                    .with_entities(
                        User.username,
                        User.id,
                        func.count(ActivityLog.id).label('activity_count')
                    )
                    .group_by(User.id, User.username)
                    .order_by(desc('activity_count'))
                    .limit(10)
                    .all()
                )
                
                active_users = [
                    {
                        'user_id': user.id,
                        'username': user.username,
                        'activity_count': user.activity_count
                    }
                    for user in user_activity_counts
                ]
            
            return {
                'total_activities': total_activities,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'action_breakdown': action_stats,
                'resource_breakdown': resource_stats,
                'most_active_users': active_users
            }
            
        except Exception as e:
            print(f"ERROR: Failed to get activity stats: {str(e)}")
            return {}

    def cleanup_old_activities(
        self,
        retention_days: int = 365,
        db: Optional[Session] = None
    ) -> int:
        """Clean up activities older than retention period"""
        try:
            if db is None:
                db = next(get_db())
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            deleted_count = db.query(ActivityLog).filter(
                ActivityLog.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            
            return deleted_count
            
        except Exception as e:
            print(f"ERROR: Failed to cleanup old activities: {str(e)}")
            if db:
                db.rollback()
            return 0

    def _generate_description(self, action: str, resource_type: str, resource_name: Optional[str]) -> str:
        """Generate a human-readable description for an activity"""
        resource_display = resource_name if resource_name else f"{resource_type}"
        
        action_descriptions = {
            'create': f"Created {resource_type}: {resource_display}",
            'update': f"Updated {resource_type}: {resource_display}",
            'delete': f"Deleted {resource_type}: {resource_display}",
            'view': f"Viewed {resource_type}: {resource_display}",
            'upload': f"Uploaded {resource_type}: {resource_display}",
            'download': f"Downloaded {resource_type}: {resource_display}",
            'approve': f"Approved {resource_type}: {resource_display}",
            'reject': f"Rejected {resource_type}: {resource_display}",
            'submit_for_review': f"Submitted {resource_type} for review: {resource_display}",
            'complete_review': f"Completed review of {resource_type}: {resource_display}",
            'login': "Logged into the system",
            'logout': "Logged out of the system",
            'export': f"Exported {resource_type} data",
            'import': f"Imported {resource_type} data"
        }
        
        return action_descriptions.get(action, f"Performed {action} on {resource_type}: {resource_display}")

    def _activity_to_dict(self, activity: ActivityLog) -> Dict[str, Any]:
        """Convert ActivityLog model to dictionary"""
        metadata = None
        if activity.activity_metadata:
            try:
                metadata = json.loads(activity.activity_metadata)
            except:
                metadata = activity.activity_metadata
        
        return {
            'id': activity.id,
            'user_id': activity.user_id,
            'username': activity.user.username if activity.user else 'Unknown',
            'action': activity.action,
            'resource_type': activity.resource_type,
            'resource_id': activity.resource_id,
            'resource_name': activity.resource_name,
            'description': activity.description,
            'metadata': metadata,
            'project_id': activity.project_id,
            'project_name': activity.project.name if activity.project else None,
            'ip_address': activity.ip_address,
            'user_agent': activity.user_agent,
            'timestamp': activity.timestamp.isoformat()
        }

    # Convenience methods for common activities
    def log_document_created(self, user_id: int, document_id: str, document_name: str, project_id: Optional[str] = None, db: Optional[Session] = None):
        """Log document creation"""
        return self.log_activity(
            user_id=user_id,
            action=self.ACTIONS['CREATE'],
            resource_type=self.RESOURCES['DOCUMENT'],
            resource_id=document_id,
            resource_name=document_name,
            project_id=project_id,
            db=db
        )
    
    def log_document_updated(self, user_id: int, document_id: str, document_name: str, changes: Dict[str, Any], project_id: Optional[str] = None, db: Optional[Session] = None):
        """Log document update"""
        return self.log_activity(
            user_id=user_id,
            action=self.ACTIONS['UPDATE'],
            resource_type=self.RESOURCES['DOCUMENT'],
            resource_id=document_id,
            resource_name=document_name,
            metadata={'changes': changes},
            project_id=project_id,
            db=db
        )
    
    def log_document_review_submitted(self, user_id: int, document_id: str, document_name: str, reviewers: List[str], project_id: Optional[str] = None, db: Optional[Session] = None):
        """Log document submitted for review"""
        return self.log_activity(
            user_id=user_id,
            action=self.ACTIONS['SUBMIT_FOR_REVIEW'],
            resource_type=self.RESOURCES['DOCUMENT'],
            resource_id=document_id,
            resource_name=document_name,
            metadata={'reviewers': reviewers},
            project_id=project_id,
            db=db
        )
    
    def log_project_created(self, user_id: int, project_id: str, project_name: str, db: Optional[Session] = None):
        """Log project creation"""
        return self.log_activity(
            user_id=user_id,
            action=self.ACTIONS['CREATE'],
            resource_type=self.RESOURCES['PROJECT'],
            resource_id=str(project_id),
            resource_name=project_name,
            project_id=project_id,
            db=db
        )
    
    def log_user_login(self, user_id: int, ip_address: Optional[str] = None, user_agent: Optional[str] = None, db: Optional[Session] = None):
        """Log user login"""
        return self.log_activity(
            user_id=user_id,
            action=self.ACTIONS['LOGIN'],
            resource_type=self.RESOURCES['SYSTEM'],
            ip_address=ip_address,
            user_agent=user_agent,
            db=db
        )


# Create global service instance
activity_log_service = ActivityLogService()