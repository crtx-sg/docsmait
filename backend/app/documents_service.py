# backend/app/documents_service.py
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from .database_config import get_db
from .db_models import Document, DocumentRevision, DocumentReviewer, DocumentReview, User, Project, ProjectMember
from .email_service import email_service
from .activity_log_service import activity_log_service

class DocumentsService:
    """Service for managing documents with revision history and review workflow"""
    
    def create_document(self, name: str, document_type: str, content: str, 
                       project_id: str, user_id: int, status: str = "draft",
                       template_id: Optional[str] = None, comment: str = "",
                       reviewers: List[int] = None) -> Dict[str, Any]:
        """Create a new document"""
        if reviewers is None:
            reviewers = []
        
        db = next(get_db())
        try:
            # Check if user is a member of the project
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return {"success": False, "error": "You must be a member of the project to create documents"}
            
            # Check if document name exists in project
            existing_doc = db.query(Document).filter(
                and_(Document.project_id == project_id, Document.name == name)
            ).first()
            
            if existing_doc:
                return {"success": False, "error": "A document with this name already exists in the project"}
            
            # Create document
            document_id = str(uuid.uuid4())
            document = Document(
                id=document_id,
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
            
            # Create initial revision
            revision_id = str(uuid.uuid4())
            revision = DocumentRevision(
                id=revision_id,
                document_id=document_id,
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
                        document_id=document_id,
                        revision_id=revision_id,
                        reviewer_id=reviewer_id
                    )
                    db.add(reviewer)
            
            db.commit()
            
            # Log document creation activity
            activity_log_service.log_document_created(
                user_id=user_id,
                document_id=document_id,
                document_name=name,
                project_id=int(project_id) if project_id else None,
                db=db
            )
            
            # Log review submission if initial status is request_review
            if status == "request_review" and reviewers:
                activity_log_service.log_document_review_submitted(
                    user_id=user_id,
                    document_id=document_id,
                    document_name=name,
                    reviewers=[str(r) for r in reviewers],
                    project_id=int(project_id) if project_id else None,
                    db=db
                )
            
            # Send email notifications for review request
            if status == "request_review" and reviewers:
                try:
                    for reviewer_id in reviewers:
                        email_service.send_review_notification(
                            document_name=name,
                            reviewer_user_id=reviewer_id,
                            status="request_review",
                            comments="Document submitted for review",
                            next_status=""
                        )
                except Exception as e:
                    print(f"Failed to send review request emails: {e}")
                    # Don't fail document creation if email fails
            
            return {
                "success": True,
                "document_id": document_id,
                "message": "Document created successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error creating document: {e}")
            return {"success": False, "error": f"Failed to create document: {str(e)}"}
        finally:
            db.close()
    
    def get_project_documents(self, project_id: str, user_id: int, 
                             status: Optional[str] = None, 
                             document_type: Optional[str] = None,
                             created_by: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all documents in a project with optional filtering"""
        db = next(get_db())
        try:
            query = db.query(Document).options(
                joinedload(Document.creator),
                joinedload(Document.reviewers),
                joinedload(Document.reviewer_user)
            ).filter(Document.project_id == project_id)
            
            if status:
                query = query.filter(Document.status == status)
            
            if document_type:
                query = query.filter(Document.document_type == document_type)
            
            if created_by:
                query = query.filter(Document.created_by == created_by)
            
            documents_db = query.order_by(Document.updated_at.desc()).all()
            
            documents = []
            for doc in documents_db:
                # Get reviewers with their usernames
                reviewers = []
                for reviewer in doc.reviewers:
                    reviewer_user = db.query(User).filter(User.id == reviewer.reviewer_id).first()
                    if reviewer_user:
                        reviewers.append({
                            "user_id": reviewer.reviewer_id,
                            "username": reviewer_user.username,
                            "status": reviewer.status
                        })
                
                doc_dict = {
                    "id": doc.id,
                    "name": doc.name,
                    "document_type": doc.document_type,
                    "content": doc.content,
                    "project_id": doc.project_id,
                    "status": doc.status,
                    "template_id": doc.template_id,
                    "created_by": doc.created_by,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    "current_revision": doc.current_revision,
                    "reviewed_at": doc.reviewed_at.isoformat() if doc.reviewed_at else None,
                    "reviewed_by": doc.reviewed_by,
                    "created_by_username": doc.creator.username if doc.creator else None,
                    "reviewed_by_username": doc.reviewer_user.username if doc.reviewer_user else None,
                    "reviewers": reviewers
                }
                documents.append(doc_dict)
            
            return documents
            
        except Exception as e:
            print(f"Error getting project documents: {e}")
            return []
        finally:
            db.close()
    
    def get_document(self, document_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a single document by ID"""
        db = next(get_db())
        try:
            document = db.query(Document).options(
                joinedload(Document.creator),
                joinedload(Document.reviewers)
            ).filter(Document.id == document_id).first()
            
            if not document:
                return None
                
            # Check if user has access (project member)
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == document.project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return None
            
            # Get reviewers with their usernames
            reviewers = []
            for reviewer in document.reviewers:
                reviewer_user = db.query(User).filter(User.id == reviewer.reviewer_id).first()
                if reviewer_user:
                    reviewers.append({
                        "user_id": reviewer.reviewer_id,
                        "username": reviewer_user.username,
                        "status": reviewer.status
                    })
            
            return {
                "id": document.id,
                "name": document.name,
                "document_type": document.document_type,
                "content": document.content,
                "project_id": document.project_id,
                "status": document.status,
                "template_id": document.template_id,
                "created_by": document.created_by,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None,
                "current_revision": document.current_revision,
                "reviewed_at": document.reviewed_at.isoformat() if document.reviewed_at else None,
                "reviewed_by": document.reviewed_by,
                "created_by_username": document.creator.username if document.creator else None,
                "reviewers": reviewers
            }
            
        except Exception as e:
            print(f"Error getting document: {e}")
            return None
        finally:
            db.close()
    
    def update_document(self, document_id: str, user_id: int, name: Optional[str] = None,
                       document_type: Optional[str] = None, content: Optional[str] = None,
                       status: Optional[str] = None, comment: str = "",
                       reviewers: Optional[List[int]] = None) -> Dict[str, Any]:
        """Update document and create new revision if content changes"""
        db = next(get_db())
        try:
            # Get document and check permissions
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return {"success": False, "error": "Document not found"}
            
            if document.created_by != user_id:
                return {"success": False, "error": "Only the document creator can edit this document"}
            
            # Store original content and status for comparison
            original_content = document.content
            original_status = document.status
            create_revision = False
            
            # Update document fields
            if name:
                document.name = name
            if document_type:
                document.document_type = document_type
            if status:
                document.status = status
            if content and content != original_content:
                document.content = content
                create_revision = True
                document.current_revision += 1
            
            # Create new revision if content changed or status changed
            if create_revision or (status and status != document.status):
                revision_id = str(uuid.uuid4())
                revision = DocumentRevision(
                    id=revision_id,
                    document_id=document_id,
                    revision_number=document.current_revision,
                    content=content or document.content,
                    status=status or document.status,
                    comment=comment,
                    created_by=user_id
                )
                db.add(revision)
                
                # Update reviewers if provided
                if status == "request_review" and reviewers is not None:
                    # Remove old reviewers for this document
                    db.query(DocumentReviewer).filter(
                        DocumentReviewer.document_id == document_id
                    ).delete()
                    
                    # Add new reviewers
                    for reviewer_id in reviewers:
                        new_reviewer = DocumentReviewer(
                            document_id=document_id,
                            revision_id=revision_id,
                            reviewer_id=reviewer_id
                        )
                        db.add(new_reviewer)
            
            db.commit()
            
            # Log document update activity
            changes = {}
            if name: changes['name'] = name
            if document_type: changes['document_type'] = document_type
            if status: changes['status'] = status
            if content and content != original_content: changes['content'] = 'updated'
            
            if changes:
                activity_log_service.log_document_updated(
                    user_id=user_id,
                    document_id=document_id,
                    document_name=document.name,
                    changes=changes,
                    project_id=int(document.project_id) if document.project_id else None,
                    db=db
                )
            
            # Send email notifications for status changes
            if status and status != original_status:
                try:
                    # Get project details
                    project = db.query(Project).filter(Project.id == document.project_id).first()
                    project_name = project.name if project else "Unknown Project"
                    
                    # Get project members for notifications
                    project_members = db.query(ProjectMember).options(
                        joinedload(ProjectMember.user)
                    ).filter(ProjectMember.project_id == document.project_id).all()
                    
                    stakeholder_emails = []
                    for member in project_members:
                        if member.user and member.user.email:
                            stakeholder_emails.append(member.user.email)
                    
                    # Send document workflow notification
                    if stakeholder_emails:
                        email_service.send_document_workflow_notification(
                            project_name=project_name,
                            document_name=document.name,
                            file_name=document.name,
                            status=status,
                            stakeholder_emails=stakeholder_emails
                        )
                    
                    # Send review notifications if changing to request_review
                    if status == "request_review" and reviewers:
                        # Log review submission activity
                        activity_log_service.log_document_review_submitted(
                            user_id=user_id,
                            document_id=document_id,
                            document_name=document.name,
                            reviewers=[str(r) for r in reviewers],
                            project_id=int(document.project_id) if document.project_id else None,
                            db=db
                        )
                        
                        for reviewer_id in reviewers:
                            email_service.send_review_notification(
                                document_name=document.name,
                                reviewer_user_id=reviewer_id,
                                status="request_review",
                                comments="Document updated and requires review",
                                next_status=""
                            )
                except Exception as e:
                    print(f"Failed to send update notification emails: {e}")
                    # Don't fail document update if email fails
            
            # Check if document was approved and update KB
            if status == "approved" and original_status != "approved":
                updated_document = self.get_document(document_id, user_id)
                if updated_document:
                    self._update_knowledge_base(updated_document)
            
            return {
                "success": True,
                "message": "Document updated successfully",
                "document_id": document_id
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error updating document: {e}")
            return {"success": False, "error": f"Failed to update document: {str(e)}"}
        finally:
            db.close()
    
    def _update_knowledge_base(self, document: Dict[str, Any]) -> None:
        """Update knowledge base when document is approved"""
        try:
            from .kb_service_pg import kb_service
            
            # Create collection name based on project name
            collection_name = document.get('project_name', 'default_project').replace(' ', '_').lower()
            
            # Prepare filename and content
            filename = f"document_{document['name'].replace(' ', '_').lower()}_v{document.get('current_revision', '1.0')}.md"
            
            # Create content with metadata
            content = f"""# Document: {document['name']}

**Project:** {document.get('project_name', 'Unknown Project')}
**Document Type:** {document['document_type']}
**Status:** {document['status']}
**Version:** {document.get('current_revision', '1.0')}
**Created by:** {document.get('created_by_username', 'Unknown')}
**Created on:** {document.get('created_at', 'Unknown')}

## Document Content

{document['content']}
"""
            
            # Prepare metadata for Qdrant payload
            metadata = {
                "document_id": document['id'],
                "document_name": document['name'],
                "project_name": document.get('project_name', 'Unknown'),
                "document_type": document['document_type'],
                "status": document['status'],
                "version": document.get('current_revision', '1.0'),
                "created_by": document.get('created_by_username', 'Unknown')
            }
            
            # Add to knowledge base
            result = kb_service.add_text_to_collection(
                collection_name=collection_name,
                text_content=content,
                filename=filename,
                metadata=metadata
            )
            
            if result.get("success"):
                print(f"✅ Document '{document['name']}' added to knowledge base collection '{collection_name}'")
            else:
                print(f"❌ Failed to add document to KB: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error updating knowledge base for document: {e}")

    def _update_review_knowledge_base(self, review_data: Dict[str, Any]) -> None:
        """Update knowledge base when review is approved"""
        try:
            from .kb_service_pg import kb_service
            
            # Extract project name from document
            project_name = review_data.get('project_name', 'default_project')
            collection_name = project_name.replace(' ', '_').lower()
            
            # Create filename for the review item
            review_item_name = f"review_{review_data.get('document_name', 'unknown')}_{review_data.get('reviewer_username', 'reviewer')}"
            filename = f"{review_item_name.replace(' ', '_').lower()}_comments.md"
            
            # Create content with review comments and metadata
            content = f"""# Review Comments for {review_data.get('document_name', 'Document')}

**Reviewer:** {review_data.get('reviewer_username', 'Unknown')}
**Review Date:** {review_data.get('reviewed_at', 'Unknown')}
**Status:** {'Approved' if review_data.get('approved') else 'Needs Revision'}

## Review Comments
{review_data.get('comments', 'No comments provided')}

**Document Details:**
- Document Type: {review_data.get('document_type', 'Unknown')}
- Project: {review_data.get('project_name', 'Unknown')}
- Revision: {review_data.get('revision_id', 'Unknown')}
"""
            
            # Prepare metadata for Qdrant payload
            metadata = {
                "review_id": review_data['id'],
                "document_id": review_data['document_id'],
                "document_name": review_data.get('document_name', 'Unknown'),
                "project_name": review_data.get('project_name', 'Unknown'),
                "reviewer_username": review_data.get('reviewer_username', 'Unknown'),
                "review_item_name": review_item_name,
                "approved": review_data.get('approved', False),
                "reviewed_at": review_data.get('reviewed_at', 'Unknown')
            }
            
            # Add to knowledge base
            result = kb_service.add_text_to_collection(
                collection_name=collection_name,
                text_content=content,
                filename=filename,
                metadata=metadata
            )
            
            if result.get("success"):
                print(f"✅ Review comments for '{review_item_name}' added to knowledge base collection '{collection_name}'")
            else:
                print(f"❌ Failed to add review to KB: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error updating knowledge base for review: {e}")

    def delete_document(self, document_id: str, user_id: int) -> Dict[str, Any]:
        """Delete document (creator only)"""
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return {"success": False, "error": "Document not found"}
            
            # Check if user is the creator or admin
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            if document.created_by != user_id and not user.is_admin:
                return {"success": False, "error": "Only the document creator or admin can delete this document"}
            
            # Log document deletion activity
            activity_log_service.log_activity(
                user_id=user_id,
                action=activity_log_service.ACTIONS['DELETE'],
                resource_type=activity_log_service.RESOURCES['DOCUMENT'],
                resource_id=document_id,
                resource_name=document.name,
                project_id=int(document.project_id) if document.project_id else None,
                db=db
            )
            
            db.delete(document)
            db.commit()
            
            return {
                "success": True,
                "message": "Document deleted successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error deleting document: {e}")
            return {"success": False, "error": f"Failed to delete document: {str(e)}"}
        finally:
            db.close()
    
    def get_document_revisions(self, document_id: str, user_id: int) -> List[Dict[str, Any]]:
        """Get revision history for a document"""
        db = next(get_db())
        try:
            # Check if user has access to document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return []
                
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == document.project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return []
            
            revisions = db.query(DocumentRevision).options(
                joinedload(DocumentRevision.creator)
            ).filter(DocumentRevision.document_id == document_id)\
             .order_by(DocumentRevision.revision_number.desc()).all()
            
            revision_list = []
            for rev in revisions:
                revision_list.append({
                    "id": rev.id,
                    "revision_number": rev.revision_number,
                    "content": rev.content,
                    "status": rev.status,
                    "comment": rev.comment,
                    "created_by": rev.created_by,
                    "created_by_username": rev.creator.username if rev.creator else None,
                    "created_at": rev.created_at.isoformat() if rev.created_at else None
                })
            
            return revision_list
            
        except Exception as e:
            print(f"Error getting document revisions: {e}")
            return []
        finally:
            db.close()
    
    def export_document_pdf(self, document_id: str, user_id: int, 
                           format_type: str = "pdf", include_metadata: bool = True) -> Dict[str, Any]:
        """Export document to PDF (placeholder implementation)"""
        db = next(get_db())
        try:
            document = db.query(Document).options(
                joinedload(Document.creator)
            ).filter(Document.id == document_id).first()
            
            if not document:
                return {"success": False, "error": "Document not found"}
                
            # Check if user has access
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == document.project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return {"success": False, "error": "Access denied"}
            
            # TODO: Implement actual PDF generation
            # For now, return success with placeholder
            return {
                "success": True,
                "message": "PDF export functionality will be implemented soon",
                "document_id": document_id,
                "format": format_type
            }
            
        except Exception as e:
            print(f"Error exporting document: {e}")
            return {"success": False, "error": f"Failed to export document: {str(e)}"}
        finally:
            db.close()
    
    def submit_document_review(self, document_id: str, revision_id: str, reviewer_id: int, 
                              approved: bool, comments: str) -> Dict[str, Any]:
        """Submit a review for a document"""
        db = next(get_db())
        try:
            # Check if reviewer is assigned to this document
            reviewer_assignment = db.query(DocumentReviewer).filter(
                and_(
                    DocumentReviewer.document_id == document_id,
                    DocumentReviewer.revision_id == revision_id,
                    DocumentReviewer.reviewer_id == reviewer_id
                )
            ).first()
            
            if not reviewer_assignment:
                return {"success": False, "error": "You are not assigned to review this document"}
            
            # Check if review already exists
            existing_review = db.query(DocumentReview).filter(
                and_(
                    DocumentReview.document_id == document_id,
                    DocumentReview.revision_id == revision_id,
                    DocumentReview.reviewer_id == reviewer_id
                )
            ).first()
            
            if existing_review:
                return {"success": False, "error": "You have already submitted a review for this document"}
            
            # Create new review
            review = DocumentReview(
                document_id=document_id,
                revision_id=revision_id,
                reviewer_id=reviewer_id,
                approved=approved,
                comments=comments
            )
            db.add(review)
            
            # Update reviewer status
            reviewer_assignment.status = "approved" if approved else "need_revision"
            
            db.commit()
            
            # Log review submission activity
            activity_log_service.log_activity(
                user_id=reviewer_id,
                action=activity_log_service.ACTIONS['COMPLETE_REVIEW'],
                resource_type=activity_log_service.RESOURCES['REVIEW'],
                resource_id=str(review.id),
                resource_name=f"Review of {document.name}" if document else "Document Review",
                description=f"{'Approved' if approved else 'Rejected'} document review with comments: {comments[:100]}{'...' if len(comments) > 100 else ''}",
                project_id=int(document.project_id) if document and document.project_id else None,
                db=db
            )
            
            # Get document and reviewer details for notifications
            document = db.query(Document).filter(Document.id == document_id).first()
            reviewer = db.query(User).filter(User.id == reviewer_id).first()
            
            # Send email notification for review completion
            try:
                if document and reviewer:
                    status_text = "approved" if approved else "needs_review"
                    next_status = "Approved" if approved else "Needs Revision"
                    
                    # Notify document creator
                    email_service.send_review_notification(
                        document_name=document.name,
                        reviewer_user_id=document.created_by,
                        status=status_text,
                        comments=comments,
                        next_status=next_status
                    )
            except Exception as e:
                print(f"Failed to send review completion email: {e}")
                # Don't fail review submission if email fails
            
            # Check if review was approved and update KB
            if approved:
                # Get review details with document and reviewer info for KB
                review_with_details = db.query(DocumentReview).options(
                    joinedload(DocumentReview.document).joinedload(Document.project),
                    joinedload(DocumentReview.reviewer)
                ).filter(DocumentReview.id == review.id).first()
                
                if review_with_details:
                    review_data = {
                        "id": review_with_details.id,
                        "document_id": review_with_details.document_id,
                        "document_name": review_with_details.document.name,
                        "document_type": review_with_details.document.document_type,
                        "project_name": review_with_details.document.project.name if review_with_details.document.project else 'Unknown',
                        "reviewer_username": review_with_details.reviewer.username,
                        "approved": review_with_details.approved,
                        "comments": review_with_details.comments,
                        "reviewed_at": review_with_details.reviewed_at.isoformat() if review_with_details.reviewed_at else None,
                        "revision_id": review_with_details.revision_id
                    }
                    self._update_review_knowledge_base(review_data)
            
            return {
                "success": True,
                "message": "Review submitted successfully",
                "review_id": review.id
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error submitting review: {e}")
            return {"success": False, "error": f"Failed to submit review: {str(e)}"}
        finally:
            db.close()
    
    def get_reviews_for_project(self, project_id: str, user_id: int, status_filter: str = None, 
                               reviewer_filter: int = None) -> List[Dict[str, Any]]:
        """Get all reviews for a project with optional filters"""
        db = next(get_db())
        try:
            # Check if user has access to the project
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return []
            
            # Base query for documents in the project
            query = db.query(Document).options(
                joinedload(Document.creator),
                joinedload(Document.reviewers),
                joinedload(Document.reviews)
            ).filter(Document.project_id == project_id)
            
            # Apply status filter
            if status_filter:
                if status_filter == "pending":
                    query = query.filter(Document.status == "request_review")
                elif status_filter == "approved":
                    query = query.filter(Document.status == "approved")
                elif status_filter == "need_revision":
                    # Documents that have reviews with need_revision
                    query = query.join(DocumentReview).filter(DocumentReview.approved == False)
            
            documents = query.all()
            reviews = []
            
            for doc in documents:
                # Only include documents that are in review or have been reviewed
                if doc.status in ["request_review", "approved"] or doc.reviews:
                    # Get reviewers info
                    reviewers_info = []
                    for reviewer in doc.reviewers:
                        reviewer_user = db.query(User).filter(User.id == reviewer.reviewer_id).first()
                        if reviewer_user:
                            # Check if reviewer has submitted a review
                            review_submitted = db.query(DocumentReview).filter(
                                and_(
                                    DocumentReview.document_id == doc.id,
                                    DocumentReview.reviewer_id == reviewer.reviewer_id
                                )
                            ).first()
                            
                            reviewers_info.append({
                                "user_id": reviewer.reviewer_id,
                                "username": reviewer_user.username,
                                "status": reviewer.status,
                                "review_submitted": review_submitted is not None,
                                "review_approved": review_submitted.approved if review_submitted else None,
                                "review_comments": review_submitted.comments if review_submitted else None,
                                "reviewed_at": review_submitted.reviewed_at.isoformat() if review_submitted and review_submitted.reviewed_at else None
                            })
                    
                    # Apply reviewer filter
                    if reviewer_filter:
                        reviewers_info = [r for r in reviewers_info if r["user_id"] == reviewer_filter]
                        if not reviewers_info:
                            continue
                    
                    reviews.append({
                        "document_id": doc.id,
                        "document_name": doc.name,
                        "document_type": doc.document_type,
                        "author": doc.creator.username if doc.creator else "Unknown",
                        "author_id": doc.created_by,
                        "status": doc.status,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None,
                        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                        "reviewers": reviewers_info,
                        "current_revision": doc.current_revision,
                        "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                    })
            
            return reviews
            
        except Exception as e:
            print(f"Error getting project reviews: {e}")
            return []
        finally:
            db.close()
    
    def get_review_queue_for_user(self, user_id: int, project_id: str = None) -> List[Dict[str, Any]]:
        """Get review queue for a specific user (documents they need to review)"""
        db = next(get_db())
        try:
            # Base query for reviewer assignments
            query = db.query(DocumentReviewer).options(
                joinedload(DocumentReviewer.document).joinedload(Document.creator),
                joinedload(DocumentReviewer.revision)
            ).filter(
                and_(
                    DocumentReviewer.reviewer_id == user_id,
                    DocumentReviewer.status == "pending"
                )
            )
            
            # Filter by project if specified
            if project_id:
                query = query.join(Document).filter(Document.project_id == project_id)
            
            assignments = query.all()
            review_queue = []
            
            for assignment in assignments:
                doc = assignment.document
                
                # Check if user has already submitted a review
                existing_review = db.query(DocumentReview).filter(
                    and_(
                        DocumentReview.document_id == doc.id,
                        DocumentReview.revision_id == assignment.revision_id,
                        DocumentReview.reviewer_id == user_id
                    )
                ).first()
                
                # Only include if no review submitted yet
                if not existing_review:
                    review_queue.append({
                        "document_id": doc.id,
                        "document_name": doc.name,
                        "document_type": doc.document_type,
                        "project_id": doc.project_id,
                        "revision_id": assignment.revision_id,
                        "author": doc.creator.username if doc.creator else "Unknown",
                        "author_id": doc.created_by,
                        "author_comment": assignment.revision.comment if assignment.revision else "",
                        "submitted_at": doc.updated_at.isoformat() if doc.updated_at else None,
                        "content": doc.content,
                        "content_preview": doc.content[:300] + "..." if len(doc.content) > 300 else doc.content
                    })
            
            return review_queue
            
        except Exception as e:
            print(f"Error getting review queue: {e}")
            return []
        finally:
            db.close()
    
    def get_submitted_reviews(self, project_id: str, user_id: int) -> List[Dict[str, Any]]:
        """Get all submitted reviews for a project"""
        db = next(get_db())
        try:
            # Check if user has access to the project
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return []
            
            # Get all submitted reviews for documents in this project
            reviews = db.query(DocumentReview).options(
                joinedload(DocumentReview.document).joinedload(Document.creator),
                joinedload(DocumentReview.reviewer)
            ).join(Document).filter(Document.project_id == project_id).all()
            
            submitted_reviews = []
            for review in reviews:
                doc = review.document
                submitted_reviews.append({
                    "review_id": review.id,
                    "document_id": doc.id,
                    "document_name": doc.name,
                    "document_type": doc.document_type,
                    "brief_description": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content,
                    "author": doc.creator.username if doc.creator else "Unknown",
                    "author_id": doc.created_by,
                    "reviewer": review.reviewer.username if review.reviewer else "Unknown",
                    "reviewer_id": review.reviewer_id,
                    "approved": review.approved,
                    "comments": review.comments,
                    "submitted_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
                    "status": "approved" if review.approved else "need_revision"
                })
            
            return sorted(submitted_reviews, key=lambda x: x["reviewed_at"] or "", reverse=True)
            
        except Exception as e:
            print(f"Error getting submitted reviews: {e}")
            return []
        finally:
            db.close()
    
    def get_review_analytics(self, project_id: str, user_id: int) -> Dict[str, Any]:
        """Get review analytics for a project"""
        db = next(get_db())
        try:
            # Check if user has access to the project
            membership = db.query(ProjectMember).filter(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            ).first()
            
            if not membership:
                return {}
            
            # Count pending reviews
            pending_count = db.query(DocumentReviewer).join(Document).filter(
                and_(
                    Document.project_id == project_id,
                    DocumentReviewer.status == "pending"
                )
            ).count()
            
            # Count approved reviews
            approved_count = db.query(DocumentReview).join(Document).filter(
                and_(
                    Document.project_id == project_id,
                    DocumentReview.approved == True
                )
            ).count()
            
            # Count reviews needing revision
            revision_count = db.query(DocumentReview).join(Document).filter(
                and_(
                    Document.project_id == project_id,
                    DocumentReview.approved == False
                )
            ).count()
            
            # Count total documents in review process
            total_documents = db.query(Document).filter(
                and_(
                    Document.project_id == project_id,
                    Document.status.in_(["request_review", "approved"])
                )
            ).count()
            
            return {
                "pending_reviews": pending_count,
                "approved_reviews": approved_count,
                "need_revision": revision_count,
                "total_documents_in_review": total_documents
            }
            
        except Exception as e:
            print(f"Error getting review analytics: {e}")
            return {}
        finally:
            db.close()

# Create global instance
documents_service = DocumentsService()