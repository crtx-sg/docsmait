# Simplified Document and Review Workflow Service
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from .database_config import get_db
from .db_models import Document, DocumentComment, DocumentRevision, User, Project, ProjectMember

class DocumentsServiceV2:
    """Simplified Document and Review Workflow Service"""
    
    def create_document(self, name: str, document_type: str, content: str, 
                       project_id: str, user_id: int) -> Dict[str, Any]:
        """Create a new document in Draft state"""
        db = next(get_db())
        try:
            document_id = str(uuid.uuid4())
            document = Document(
                id=document_id,
                name=name,
                document_type=document_type,
                content=content,
                project_id=project_id,
                created_by=user_id,
                document_state="draft",
                review_state="none"
            )
            
            db.add(document)
            db.commit()
            
            return {
                "success": True,
                "document_id": document_id,
                "message": "Document created successfully"
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Failed to create document: {str(e)}"}
        finally:
            db.close()
    
    def submit_for_review(self, document_id: str, reviewer_id: int, 
                         comment: str, user_id: int) -> Dict[str, Any]:
        """Author submits document for review"""
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return {"success": False, "error": "Document not found"}
            
            if document.created_by != user_id:
                return {"success": False, "error": "Only document author can submit for review"}
            
            # Update document state
            document.document_state = "review_request"
            document.review_state = "under_review"
            document.current_reviewer_id = reviewer_id
            document.updated_at = datetime.now(timezone.utc)
            
            # Add comment
            comment_id = str(uuid.uuid4())
            doc_comment = DocumentComment(
                id=comment_id,
                document_id=document_id,
                user_id=user_id,
                comment_text=comment,
                comment_type="review_request"
            )
            
            db.add(doc_comment)
            db.flush()  # Flush to ensure the comment is saved with an ID
            db.commit()
            db.refresh(document)  # Refresh document to ensure relationships are loaded  
            db.refresh(doc_comment)  # Refresh comment to ensure user relationship is loaded
            
            return {
                "success": True,
                "message": "Document submitted for review successfully"
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Failed to submit for review: {str(e)}"}
        finally:
            db.close()
    
    def submit_review(self, document_id: str, reviewer_comment: str, 
                     review_decision: str, user_id: int) -> Dict[str, Any]:
        """Reviewer submits review (needs_update or approved)"""
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return {"success": False, "error": "Document not found"}
            
            if document.current_reviewer_id != user_id:
                return {"success": False, "error": "Only assigned reviewer can submit review"}
            
            if review_decision not in ["needs_update", "approved"]:
                return {"success": False, "error": "Invalid review decision"}
            
            # Update document state
            if review_decision == "needs_update":
                document.document_state = "needs_update"
                document.review_state = "none"
                document.current_reviewer_id = None
            else:  # approved
                document.document_state = "approved"
                document.review_state = "none"
                document.current_reviewer_id = None
            
            document.updated_at = datetime.now(timezone.utc)
            
            # Add review comment
            comment_id = str(uuid.uuid4())
            doc_comment = DocumentComment(
                id=comment_id,
                document_id=document_id,
                user_id=user_id,
                comment_text=reviewer_comment,
                comment_type=review_decision
            )
            
            db.add(doc_comment)
            db.commit()
            
            return {
                "success": True,
                "message": f"Review submitted successfully - Document {review_decision.replace('_', ' ')}"
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Failed to submit review: {str(e)}"}
        finally:
            db.close()
    
    def get_documents_for_author(self, user_id: int, project_id: str) -> List[Dict[str, Any]]:
        """Get all documents for author"""
        db = next(get_db())
        try:
            documents = db.query(Document).options(
                joinedload(Document.creator),
                joinedload(Document.current_reviewer),
                joinedload(Document.reviewers),
                joinedload(Document.comments).joinedload(DocumentComment.user)
            ).filter(
                and_(
                    Document.created_by == user_id,
                    Document.project_id == project_id
                )
            ).order_by(Document.updated_at.desc()).all()
            
            result = []
            for doc in documents:
                # Get comment history
                comments = []
                for comment in doc.comments:
                    comments.append({
                        "date_time": comment.created_at.isoformat() if comment.created_at else None,
                        "type": comment.comment_type.replace('_', ' ').title(),
                        "user": comment.user.username if comment.user else "Unknown",
                        "comment": comment.comment_text
                    })
                
                # Sort comments by date (most recent first)
                comments.sort(key=lambda x: x['date_time'] if x['date_time'] else '', reverse=True)
                
                # Get creator username
                creator_username = doc.creator.username if doc.creator else "Unknown"
                
                result.append({
                    "id": doc.id,
                    "name": doc.name,
                    "document_type": doc.document_type,
                    "content": doc.content,
                    "project_id": doc.project_id,
                    "document_state": doc.document_state,
                    "review_state": doc.review_state,
                    "status": doc.document_state,  # For backward compatibility
                    "template_id": getattr(doc, 'template_id', None),
                    "current_revision": getattr(doc, 'current_revision', 1),
                    "reviewed_at": doc.reviewed_at.isoformat() if getattr(doc, 'reviewed_at', None) else None,
                    "reviewed_by": getattr(doc, 'reviewed_by', None),
                    "reviewed_by_username": None,  # TODO: Get this if needed
                    "author": creator_username,
                    "created_by_username": creator_username,
                    "current_reviewer": doc.current_reviewer.username if doc.current_reviewer else None,
                    "reviewers": self._get_document_reviewers(doc, db),
                    "created_by": doc.created_by,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    "comment_history": comments
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting documents for author: {e}")
            return []
        finally:
            db.close()
    
    def get_documents_for_reviewer(self, user_id: int, project_id: str) -> List[Dict[str, Any]]:
        """Get all documents assigned to reviewer"""
        db = next(get_db())
        try:
            documents = db.query(Document).options(
                joinedload(Document.creator),
                joinedload(Document.current_reviewer),
                joinedload(Document.reviewers),
                joinedload(Document.comments).joinedload(DocumentComment.user)
            ).filter(
                and_(
                    Document.current_reviewer_id == user_id,
                    Document.project_id == project_id,
                    Document.review_state == "under_review"
                )
            ).order_by(Document.updated_at.desc()).all()
            
            result = []
            for doc in documents:
                # Get comment history
                comments = []
                for comment in doc.comments:
                    comments.append({
                        "date_time": comment.created_at.isoformat() if comment.created_at else None,
                        "type": comment.comment_type.replace('_', ' ').title(),
                        "user": comment.user.username if comment.user else "Unknown",
                        "comment": comment.comment_text
                    })
                
                # Sort comments by date (most recent first)
                comments.sort(key=lambda x: x['date_time'] if x['date_time'] else '', reverse=True)
                
                # Get creator username
                creator_username = doc.creator.username if doc.creator else "Unknown"
                
                result.append({
                    "id": doc.id,
                    "name": doc.name,
                    "document_type": doc.document_type,
                    "content": doc.content,
                    "project_id": doc.project_id,
                    "document_state": doc.document_state,
                    "review_state": doc.review_state,
                    "status": doc.document_state,  # For backward compatibility
                    "template_id": getattr(doc, 'template_id', None),
                    "current_revision": getattr(doc, 'current_revision', 1),
                    "reviewed_at": doc.reviewed_at.isoformat() if getattr(doc, 'reviewed_at', None) else None,
                    "reviewed_by": getattr(doc, 'reviewed_by', None),
                    "reviewed_by_username": None,  # TODO: Get this if needed
                    "author": creator_username,
                    "created_by_username": creator_username,
                    "current_reviewer": doc.current_reviewer.username if doc.current_reviewer else None,
                    "reviewers": self._get_document_reviewers(doc, db),
                    "created_by": doc.created_by,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    "comment_history": comments
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting documents for reviewer: {e}")
            return []
        finally:
            db.close()
    
    def get_approved_documents(self, project_id: str, user_id: int) -> List[Dict[str, Any]]:
        """Get all approved documents in project"""
        db = next(get_db())
        try:
            # Check if user has access to project
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return []
            
            documents = db.query(Document).options(
                joinedload(Document.creator),
                joinedload(Document.reviewers),
                joinedload(Document.comments).joinedload(DocumentComment.user)
            ).filter(
                and_(
                    Document.project_id == project_id,
                    Document.document_state == "approved"
                )
            ).order_by(Document.updated_at.desc()).all()
            
            result = []
            for doc in documents:
                # Get comment history
                comments = []
                for comment in doc.comments:
                    comments.append({
                        "date_time": comment.created_at.isoformat() if comment.created_at else None,
                        "type": comment.comment_type.replace('_', ' ').title(),
                        "user": comment.user.username if comment.user else "Unknown",
                        "comment": comment.comment_text
                    })
                
                # Sort comments by date (most recent first)
                comments.sort(key=lambda x: x['date_time'] if x['date_time'] else '', reverse=True)
                
                result.append({
                    "id": doc.id,
                    "name": doc.name,
                    "document_type": doc.document_type,
                    "content": doc.content,
                    "project_id": doc.project_id,
                    "document_state": doc.document_state,
                    "review_state": doc.review_state,
                    "status": doc.document_state,  # For backward compatibility
                    "template_id": getattr(doc, 'template_id', None),
                    "current_revision": getattr(doc, 'current_revision', 1),
                    "reviewed_at": doc.reviewed_at.isoformat() if getattr(doc, 'reviewed_at', None) else None,
                    "reviewed_by": getattr(doc, 'reviewed_by', None),
                    "reviewed_by_username": None,  # TODO: Get this if needed
                    "author": doc.creator.username if doc.creator else "Unknown",
                    "created_by_username": doc.creator.username if doc.creator else "Unknown",
                    "created_by": doc.created_by,
                    "current_reviewer": None,  # Approved docs don't have current reviewer
                    "reviewers": self._get_document_reviewers(doc, db),
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    "comment_history": comments
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting approved documents: {e}")
            return []
        finally:
            db.close()
    
    def create_revision(self, document_id: str, content: str, user_id: int, comment: str = "") -> Dict[str, Any]:
        """Create a new revision for a document"""
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return {"success": False, "error": "Document not found"}
            
            if document.created_by != user_id:
                return {"success": False, "error": "Only document author can create revisions"}
            
            # Get the next revision number
            latest_revision = db.query(DocumentRevision).filter(
                DocumentRevision.document_id == document_id
            ).order_by(DocumentRevision.revision_number.desc()).first()
            
            next_revision_number = 1 if not latest_revision else latest_revision.revision_number + 1
            
            # Create new revision
            revision_id = str(uuid.uuid4())
            revision = DocumentRevision(
                id=revision_id,
                document_id=document_id,
                revision_number=next_revision_number,
                content=content,
                status=document.document_state,
                comment=comment,
                created_by=user_id
            )
            
            # Update document content and current revision
            document.content = content
            document.current_revision = next_revision_number
            document.updated_at = datetime.now(timezone.utc)
            
            db.add(revision)
            db.commit()
            
            return {
                "success": True,
                "revision_number": next_revision_number,
                "message": f"Revision {next_revision_number} created successfully"
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Failed to create revision: {str(e)}"}
        finally:
            db.close()
    
    def get_document_revisions(self, document_id: str, user_id: int) -> List[Dict[str, Any]]:
        """Get revision history for a document"""
        db = next(get_db())
        try:
            # Check if user has access to the document
            document = db.query(Document).options(
                joinedload(Document.project).joinedload(Project.members)
            ).filter(Document.id == document_id).first()
            
            if not document:
                return []
            
            # Check if user is a project member or document creator
            user_has_access = False
            if document.created_by == user_id:
                user_has_access = True
            else:
                for member in document.project.members:
                    if member.user_id == user_id:
                        user_has_access = True
                        break
            
            if not user_has_access:
                return []
            
            revisions = db.query(DocumentRevision).options(
                joinedload(DocumentRevision.document).joinedload(Document.creator)
            ).filter(
                DocumentRevision.document_id == document_id
            ).order_by(DocumentRevision.revision_number.desc()).all()
            
            result = []
            for revision in revisions:
                creator_username = "Unknown"
                if hasattr(revision, 'created_by'):
                    creator = db.query(User).filter(User.id == revision.created_by).first()
                    if creator:
                        creator_username = creator.username
                
                result.append({
                    "revision_id": revision.id,
                    "revision_number": revision.revision_number,
                    "content": revision.content,
                    "status": revision.status,
                    "comment": revision.comment,
                    "created_by": creator_username,
                    "created_at": revision.created_at.isoformat() if revision.created_at else None,
                    "is_current": revision.revision_number == document.current_revision
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting document revisions: {e}")
            return []
        finally:
            db.close()
    
    def update_document_content(self, document_id: str, content: str, user_id: int, 
                               create_revision: bool = True, comment: str = "") -> Dict[str, Any]:
        """Update document content with optional revision creation"""
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return {"success": False, "error": "Document not found"}
            
            if document.created_by != user_id:
                return {"success": False, "error": "Only document author can update content"}
            
            # Create revision if requested and content has changed
            if create_revision and document.content != content:
                revision_result = self.create_revision(document_id, content, user_id, comment)
                if not revision_result.get("success"):
                    return revision_result
                
                return {
                    "success": True,
                    "message": f"Document updated with revision {revision_result['revision_number']}"
                }
            else:
                # Just update content without creating revision
                document.content = content
                document.updated_at = datetime.now(timezone.utc)
                db.commit()
                
                return {
                    "success": True,
                    "message": "Document content updated"
                }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Failed to update document: {str(e)}"}
        finally:
            db.close()
    
    def _get_document_reviewers(self, doc, db) -> List[str]:
        """Get all reviewers (current and historical) for a document"""
        reviewers = []
        
        # Add current reviewer if exists
        if doc.current_reviewer:
            reviewers.append(doc.current_reviewer.username)
        
        # Add historical reviewers from document_reviewers table
        for reviewer_assignment in doc.reviewers:
            reviewer_user = db.query(User).filter(User.id == reviewer_assignment.reviewer_id).first()
            if reviewer_user and reviewer_user.username not in reviewers:
                reviewers.append(reviewer_user.username)
        
        return reviewers
    
    def get_project_documents(self, project_id: str, user_id: int, 
                             status: str = None, document_type: str = None, 
                             created_by: int = None) -> List[Dict[str, Any]]:
        """Get all documents in a project with optional filtering (v2)"""
        db = next(get_db())
        try:
            # Check if user has access to project
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return []
            
            # Build query
            query = db.query(Document).options(
                joinedload(Document.creator),
                joinedload(Document.current_reviewer),
                joinedload(Document.reviewers),
                joinedload(Document.comments).joinedload(DocumentComment.user)
            ).filter(Document.project_id == project_id)
            
            # Apply filters
            if status:
                # Map old status values to document_state
                if status == "approved":
                    query = query.filter(Document.document_state == "approved")
                elif status == "draft":
                    query = query.filter(Document.document_state == "draft")
                elif status == "request_review":
                    query = query.filter(Document.document_state == "request_review")
                else:
                    query = query.filter(Document.document_state == status)
            
            if document_type:
                query = query.filter(Document.document_type == document_type)
            
            if created_by:
                query = query.filter(Document.created_by == created_by)
            
            documents = query.order_by(Document.updated_at.desc()).all()
            
            result = []
            for doc in documents:
                # Get comment history
                comments = []
                for comment in doc.comments:
                    comments.append({
                        "date_time": comment.created_at.isoformat() if comment.created_at else None,
                        "type": comment.comment_type.replace('_', ' ').title(),
                        "user": comment.user.username if comment.user else "Unknown",
                        "comment": comment.comment_text
                    })
                
                # Sort comments by date (most recent first)
                comments.sort(key=lambda x: x['date_time'] if x['date_time'] else '', reverse=True)
                
                # Get creator username
                creator_username = doc.creator.username if doc.creator else "Unknown"
                
                result.append({
                    "id": doc.id,
                    "name": doc.name,
                    "document_type": doc.document_type,
                    "content": doc.content,
                    "project_id": doc.project_id,
                    "document_state": doc.document_state,
                    "review_state": doc.review_state,
                    "status": doc.document_state,  # For backward compatibility
                    "template_id": getattr(doc, 'template_id', None),
                    "current_revision": getattr(doc, 'current_revision', 1),
                    "reviewed_at": doc.reviewed_at.isoformat() if getattr(doc, 'reviewed_at', None) else None,
                    "reviewed_by": getattr(doc, 'reviewed_by', None),
                    "reviewed_by_username": None,  # TODO: Get this if needed
                    "author": creator_username,
                    "created_by_username": creator_username,
                    "current_reviewer": doc.current_reviewer.username if doc.current_reviewer else None,
                    "reviewers": self._get_document_reviewers(doc, db),
                    "created_by": doc.created_by,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    "comment_history": comments
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting project documents: {e}")
            return []
        finally:
            db.close()

# Create service instance
documents_service_v2 = DocumentsServiceV2()