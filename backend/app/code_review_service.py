# backend/app/code_review_service.py
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_
from datetime import datetime
import uuid

from .db_models import Repository, PullRequest, PullRequestFile, CodeReview, CodeComment, ReviewRequest, User, Project
from .models import (
    RepositoryCreate, RepositoryUpdate, RepositoryResponse,
    PullRequestCreate, PullRequestUpdate, PullRequestResponse, PullRequestFileResponse,
    CodeReviewCreate, CodeReviewUpdate, CodeReviewResponse,
    CodeCommentCreate, CodeCommentUpdate, CodeCommentResponse,
    ReviewRequestCreate, ReviewRequestResponse
)
from .email_service import email_service

class CodeReviewService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_pr_number(self, repository_id: str) -> int:
        """Generate next PR number for repository"""
        count = self.db.query(PullRequest).filter(PullRequest.repository_id == repository_id).count()
        return count + 1
    
    # === REPOSITORY CRUD ===
    
    def create_repository(self, repo_data: RepositoryCreate, current_user_id: int) -> RepositoryResponse:
        """Create new repository"""
        repo_id = str(uuid.uuid4())
        
        repository = Repository(
            id=repo_id,
            project_id=repo_data.project_id,
            name=repo_data.name,
            description=repo_data.description,
            git_url=repo_data.git_url,
            git_provider=repo_data.git_provider,
            default_branch=repo_data.default_branch,
            is_private=repo_data.is_private,
            created_by=current_user_id
        )
        
        self.db.add(repository)
        self.db.commit()
        self.db.refresh(repository)
        
        return self._repository_to_response(repository)
    
    def get_repositories(self, project_id: Optional[str] = None) -> List[RepositoryResponse]:
        """Get repositories with optional filtering"""
        query = self.db.query(Repository).options(
            joinedload(Repository.creator),
            joinedload(Repository.project)
        )
        
        if project_id:
            query = query.filter(Repository.project_id == project_id)
            
        repositories = query.order_by(desc(Repository.created_at)).all()
        return [self._repository_to_response(repo) for repo in repositories]
    
    def get_repository(self, repository_id: str) -> Optional[RepositoryResponse]:
        """Get single repository by ID"""
        repository = self.db.query(Repository).options(
            joinedload(Repository.creator),
            joinedload(Repository.project)
        ).filter(Repository.id == repository_id).first()
        
        return self._repository_to_response(repository) if repository else None
    
    def update_repository(self, repository_id: str, repo_data: RepositoryUpdate) -> Optional[RepositoryResponse]:
        """Update existing repository"""
        repository = self.db.query(Repository).filter(Repository.id == repository_id).first()
        if not repository:
            return None
        
        for field, value in repo_data.dict(exclude_unset=True).items():
            setattr(repository, field, value)
        
        self.db.commit()
        self.db.refresh(repository)
        return self._repository_to_response(repository)
    
    def delete_repository(self, repository_id: str) -> bool:
        """Delete repository and all related data"""
        repository = self.db.query(Repository).filter(Repository.id == repository_id).first()
        if not repository:
            return False
        
        self.db.delete(repository)
        self.db.commit()
        return True
    
    # === PULL REQUEST CRUD ===
    
    def create_pull_request(self, pr_data: PullRequestCreate, current_user_id: int) -> PullRequestResponse:
        """Create new pull request"""
        pr_id = str(uuid.uuid4())
        pr_number = self.generate_pr_number(pr_data.repository_id)
        
        pull_request = PullRequest(
            id=pr_id,
            repository_id=pr_data.repository_id,
            pr_number=pr_number,
            title=pr_data.title,
            description=pr_data.description,
            author_id=current_user_id,
            source_branch=pr_data.source_branch,
            target_branch=pr_data.target_branch,
            external_id=pr_data.external_id,
            external_url=pr_data.external_url
        )
        
        self.db.add(pull_request)
        self.db.commit()
        self.db.refresh(pull_request)
        
        return self._pull_request_to_response(pull_request)
    
    def get_pull_requests(self, repository_id: Optional[str] = None, status: Optional[str] = None) -> List[PullRequestResponse]:
        """Get pull requests with optional filtering"""
        query = self.db.query(PullRequest).options(
            joinedload(PullRequest.author),
            joinedload(PullRequest.repository)
        )
        
        if repository_id:
            query = query.filter(PullRequest.repository_id == repository_id)
        if status:
            query = query.filter(PullRequest.status == status)
            
        pull_requests = query.order_by(desc(PullRequest.created_at)).all()
        return [self._pull_request_to_response(pr) for pr in pull_requests]
    
    def get_pull_request(self, pr_id: str) -> Optional[PullRequestResponse]:
        """Get single pull request by ID"""
        pull_request = self.db.query(PullRequest).options(
            joinedload(PullRequest.author),
            joinedload(PullRequest.repository)
        ).filter(PullRequest.id == pr_id).first()
        
        return self._pull_request_to_response(pull_request) if pull_request else None
    
    def update_pull_request(self, pr_id: str, pr_data: PullRequestUpdate) -> Optional[PullRequestResponse]:
        """Update existing pull request"""
        pull_request = self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()
        if not pull_request:
            return None
        
        for field, value in pr_data.dict(exclude_unset=True).items():
            setattr(pull_request, field, value)
        
        self.db.commit()
        self.db.refresh(pull_request)
        return self._pull_request_to_response(pull_request)
    
    def delete_pull_request(self, pr_id: str) -> bool:
        """Delete pull request and all related data"""
        pull_request = self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()
        if not pull_request:
            return False
        
        self.db.delete(pull_request)
        self.db.commit()
        return True
    
    # === PULL REQUEST FILES ===
    
    def get_pr_files(self, pr_id: str) -> List[PullRequestFileResponse]:
        """Get files changed in a pull request"""
        files = self.db.query(PullRequestFile).filter(
            PullRequestFile.pull_request_id == pr_id
        ).order_by(PullRequestFile.file_path).all()
        
        return [self._pr_file_to_response(file) for file in files]
    
    def add_pr_file(self, pr_id: str, file_path: str, file_status: str, 
                   additions: int = 0, deletions: int = 0, patch_content: str = None) -> PullRequestFileResponse:
        """Add file to pull request"""
        file_id = str(uuid.uuid4())
        
        pr_file = PullRequestFile(
            id=file_id,
            pull_request_id=pr_id,
            file_path=file_path,
            file_status=file_status,
            additions=additions,
            deletions=deletions,
            changes=additions + deletions,
            patch_content=patch_content
        )
        
        self.db.add(pr_file)
        self.db.commit()
        self.db.refresh(pr_file)
        
        return self._pr_file_to_response(pr_file)
    
    # === CODE REVIEW CRUD ===
    
    def create_code_review(self, review_data: CodeReviewCreate, current_user_id: int) -> List[CodeReviewResponse]:
        """Create code reviews for multiple reviewers"""
        reviews = []
        
        for reviewer_id in review_data.reviewer_ids:
            review_id = str(uuid.uuid4())
            
            code_review = CodeReview(
                id=review_id,
                pull_request_id=review_data.pull_request_id,
                reviewer_id=reviewer_id,
                status=review_data.status,
                summary_comment=review_data.summary_comment
            )
            
            if review_data.status != "pending":
                code_review.submitted_at = datetime.utcnow()
            
            self.db.add(code_review)
            reviews.append(code_review)
        
        self.db.commit()
        
        # Send email notifications to reviewers
        try:
            # Get pull request and project details
            pull_request = self.db.query(PullRequest).options(
                joinedload(PullRequest.repository).joinedload(Repository.project)
            ).filter(PullRequest.id == review_data.pull_request_id).first()
            
            if pull_request:
                project_name = pull_request.repository.project.name if pull_request.repository.project else "Unknown Project"
                
                # Get reviewer emails
                reviewer_emails = []
                for reviewer_id in review_data.reviewer_ids:
                    user = self.db.query(User).filter(User.id == reviewer_id).first()
                    if user and user.email:
                        reviewer_emails.append(user.email)
                
                # Send code review notifications
                if reviewer_emails:
                    email_service.send_code_review_notification(
                        project_name=project_name,
                        pull_request_title=pull_request.title,
                        summary_comment=review_data.summary_comment or "",
                        review_status=review_data.status,
                        reviewer_emails=reviewer_emails
                    )
        except Exception as e:
            print(f"Failed to send code review notification emails: {e}")
            # Don't fail code review creation if email fails
        
        return [self._code_review_to_response(review) for review in reviews]
    
    def get_code_reviews(self, pr_id: Optional[str] = None, reviewer_id: Optional[int] = None) -> List[CodeReviewResponse]:
        """Get code reviews with optional filtering"""
        query = self.db.query(CodeReview).options(
            joinedload(CodeReview.reviewer)
        )
        
        if pr_id:
            query = query.filter(CodeReview.pull_request_id == pr_id)
        if reviewer_id:
            query = query.filter(CodeReview.reviewer_id == reviewer_id)
            
        reviews = query.order_by(desc(CodeReview.created_at)).all()
        return [self._code_review_to_response(review) for review in reviews]
    
    def update_code_review(self, review_id: str, review_data: CodeReviewUpdate) -> Optional[CodeReviewResponse]:
        """Update existing code review"""
        review = self.db.query(CodeReview).filter(CodeReview.id == review_id).first()
        if not review:
            return None
        
        for field, value in review_data.dict(exclude_unset=True).items():
            setattr(review, field, value)
        
        if review_data.status and review_data.status != "pending" and not review.submitted_at:
            review.submitted_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(review)
        return self._code_review_to_response(review)
    
    # === CODE COMMENTS CRUD ===
    
    def create_code_comment(self, comment_data: CodeCommentCreate, current_user_id: int) -> CodeCommentResponse:
        """Create new code comment"""
        comment_id = str(uuid.uuid4())
        
        comment = CodeComment(
            id=comment_id,
            review_id=comment_data.review_id,
            file_id=comment_data.file_id,
            line_number=comment_data.line_number,
            line_type=comment_data.line_type,
            comment_text=comment_data.comment_text,
            parent_comment_id=comment_data.parent_comment_id
        )
        
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        
        return self._code_comment_to_response(comment)
    
    def get_code_comments(self, review_id: Optional[str] = None, file_id: Optional[str] = None) -> List[CodeCommentResponse]:
        """Get code comments with optional filtering"""
        query = self.db.query(CodeComment).options(
            joinedload(CodeComment.review).joinedload(CodeReview.reviewer),
            joinedload(CodeComment.file)
        )
        
        if review_id:
            query = query.filter(CodeComment.review_id == review_id)
        if file_id:
            query = query.filter(CodeComment.file_id == file_id)
            
        comments = query.order_by(CodeComment.created_at).all()
        return [self._code_comment_to_response(comment) for comment in comments]
    
    def update_code_comment(self, comment_id: str, comment_data: CodeCommentUpdate) -> Optional[CodeCommentResponse]:
        """Update existing code comment"""
        comment = self.db.query(CodeComment).filter(CodeComment.id == comment_id).first()
        if not comment:
            return None
        
        for field, value in comment_data.dict(exclude_unset=True).items():
            setattr(comment, field, value)
        
        self.db.commit()
        self.db.refresh(comment)
        return self._code_comment_to_response(comment)
    
    # === HELPER METHODS ===
    
    def _repository_to_response(self, repository: Repository) -> RepositoryResponse:
        """Convert Repository DB model to response model"""
        # Count pull requests
        pr_count = self.db.query(PullRequest).filter(PullRequest.repository_id == repository.id).count()
        open_pr_count = self.db.query(PullRequest).filter(
            and_(PullRequest.repository_id == repository.id, 
                 PullRequest.status.in_(["open", "review_requested", "draft"]))
        ).count()
        
        return RepositoryResponse(
            id=repository.id,
            project_id=repository.project_id,
            project_name=repository.project.name,
            name=repository.name,
            description=repository.description,
            git_url=repository.git_url,
            git_provider=repository.git_provider,
            default_branch=repository.default_branch,
            is_private=repository.is_private,
            created_by=repository.created_by,
            created_by_username=repository.creator.username,
            created_at=repository.created_at.isoformat(),
            updated_at=repository.updated_at.isoformat(),
            pull_requests_count=pr_count,
            open_prs_count=open_pr_count
        )
    
    def _pull_request_to_response(self, pr: PullRequest) -> PullRequestResponse:
        """Convert PullRequest DB model to response model"""
        # Count reviews
        reviews_count = self.db.query(CodeReview).filter(CodeReview.pull_request_id == pr.id).count()
        pending_reviews_count = self.db.query(CodeReview).filter(
            and_(CodeReview.pull_request_id == pr.id, CodeReview.status == "pending")
        ).count()
        
        return PullRequestResponse(
            id=pr.id,
            repository_id=pr.repository_id,
            repository_name=pr.repository.name,
            pr_number=pr.pr_number,
            title=pr.title,
            description=pr.description,
            author_id=pr.author_id,
            author_username=pr.author.username,
            source_branch=pr.source_branch,
            target_branch=pr.target_branch,
            status=pr.status,
            merge_status=pr.merge_status,
            commits_count=pr.commits_count,
            files_changed_count=pr.files_changed_count,
            additions=pr.additions,
            deletions=pr.deletions,
            external_id=pr.external_id,
            external_url=pr.external_url,
            created_at=pr.created_at.isoformat(),
            updated_at=pr.updated_at.isoformat(),
            merged_at=pr.merged_at.isoformat() if pr.merged_at else None,
            closed_at=pr.closed_at.isoformat() if pr.closed_at else None,
            reviews_count=reviews_count,
            pending_reviews_count=pending_reviews_count
        )
    
    def _pr_file_to_response(self, file: PullRequestFile) -> PullRequestFileResponse:
        """Convert PullRequestFile DB model to response model"""
        comments_count = self.db.query(CodeComment).filter(CodeComment.file_id == file.id).count()
        
        return PullRequestFileResponse(
            id=file.id,
            pull_request_id=file.pull_request_id,
            file_path=file.file_path,
            file_status=file.file_status,
            old_file_path=file.old_file_path,
            additions=file.additions,
            deletions=file.deletions,
            changes=file.changes,
            patch_content=file.patch_content,
            comments_count=comments_count
        )
    
    def _code_review_to_response(self, review: CodeReview) -> CodeReviewResponse:
        """Convert CodeReview DB model to response model"""
        comments_count = self.db.query(CodeComment).filter(CodeComment.review_id == review.id).count()
        
        return CodeReviewResponse(
            id=review.id,
            pull_request_id=review.pull_request_id,
            reviewer_id=review.reviewer_id,
            reviewer_username=review.reviewer.username,
            status=review.status,
            summary_comment=review.summary_comment,
            submitted_at=review.submitted_at.isoformat() if review.submitted_at else None,
            created_at=review.created_at.isoformat(),
            updated_at=review.updated_at.isoformat(),
            comments_count=comments_count
        )
    
    def _code_comment_to_response(self, comment: CodeComment) -> CodeCommentResponse:
        """Convert CodeComment DB model to response model"""
        replies_count = self.db.query(CodeComment).filter(
            CodeComment.parent_comment_id == comment.id
        ).count()
        
        return CodeCommentResponse(
            id=comment.id,
            review_id=comment.review_id,
            file_id=comment.file_id,
            file_path=comment.file.file_path if comment.file else None,
            line_number=comment.line_number,
            line_type=comment.line_type,
            comment_text=comment.comment_text,
            is_resolved=comment.is_resolved,
            parent_comment_id=comment.parent_comment_id,
            author_id=comment.review.reviewer_id,
            author_username=comment.review.reviewer.username,
            created_at=comment.created_at.isoformat(),
            updated_at=comment.updated_at.isoformat(),
            replies_count=replies_count
        )