# backend/app/webhook_service.py
import json
import hmac
import hashlib
import uuid
from typing import Dict, Optional
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from .db_models import Repository, PullRequest, PullRequestFile, User
from .code_review_service import CodeReviewService
from .automated_review_service import AutomatedReviewService, get_or_create_ai_reviewer
from .git_integration_service import git_service

class WebhookService:
    """Service for handling webhooks from Git providers (GitHub, GitLab, etc.)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.code_review_service = CodeReviewService(db)
    
    async def handle_github_webhook(self, request: Request, signature: str = None) -> Dict:
        """Handle GitHub webhook events"""
        try:
            payload = await request.body()
            
            # Verify webhook signature if provided
            if signature:
                if not self._verify_github_signature(payload, signature):
                    raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            event_data = json.loads(payload.decode('utf-8'))
            event_type = request.headers.get('X-GitHub-Event', 'unknown')
            
            return await self._process_github_event(event_type, event_data)
            
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
    
    async def handle_gitlab_webhook(self, request: Request, token: str = None) -> Dict:
        """Handle GitLab webhook events"""
        try:
            payload = await request.body()
            event_data = json.loads(payload.decode('utf-8'))
            event_type = event_data.get('object_kind', 'unknown')
            
            # Verify webhook token if provided
            if token:
                webhook_token = request.headers.get('X-Gitlab-Token')
                if webhook_token != token:
                    raise HTTPException(status_code=401, detail="Invalid webhook token")
            
            return await self._process_gitlab_event(event_type, event_data)
            
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
    
    async def _process_github_event(self, event_type: str, event_data: Dict) -> Dict:
        """Process GitHub webhook events"""
        if event_type == 'pull_request':
            return await self._handle_github_pull_request(event_data)
        elif event_type == 'push':
            return await self._handle_github_push(event_data)
        elif event_type == 'repository':
            return await self._handle_github_repository(event_data)
        else:
            return {"message": f"Event type '{event_type}' not handled", "status": "ignored"}
    
    async def _process_gitlab_event(self, event_type: str, event_data: Dict) -> Dict:
        """Process GitLab webhook events"""
        if event_type == 'merge_request':
            return await self._handle_gitlab_merge_request(event_data)
        elif event_type == 'push':
            return await self._handle_gitlab_push(event_data)
        else:
            return {"message": f"Event type '{event_type}' not handled", "status": "ignored"}
    
    async def _handle_github_pull_request(self, event_data: Dict) -> Dict:
        """Handle GitHub pull request events"""
        action = event_data.get('action')
        pr_data = event_data.get('pull_request', {})
        repo_data = event_data.get('repository', {})
        
        # Find corresponding repository in our system
        repository = self.db.query(Repository).filter(
            Repository.git_url.contains(repo_data.get('html_url', ''))
        ).first()
        
        if not repository:
            return {"message": "Repository not found in system", "status": "ignored"}
        
        if action in ['opened', 'synchronize', 'reopened']:
            return await self._sync_github_pull_request(repository, pr_data)
        elif action == 'closed':
            return await self._close_pull_request(repository, pr_data)
        
        return {"message": f"PR action '{action}' processed", "status": "success"}
    
    async def _handle_gitlab_merge_request(self, event_data: Dict) -> Dict:
        """Handle GitLab merge request events"""
        action = event_data.get('object_attributes', {}).get('action')
        mr_data = event_data.get('object_attributes', {})
        project_data = event_data.get('project', {})
        
        # Find corresponding repository in our system
        repository = self.db.query(Repository).filter(
            Repository.git_url.contains(project_data.get('web_url', ''))
        ).first()
        
        if not repository:
            return {"message": "Repository not found in system", "status": "ignored"}
        
        if action in ['open', 'update', 'reopen']:
            return await self._sync_gitlab_merge_request(repository, mr_data)
        elif action == 'close':
            return await self._close_pull_request(repository, mr_data)
        
        return {"message": f"MR action '{action}' processed", "status": "success"}
    
    async def _sync_github_pull_request(self, repository: Repository, pr_data: Dict) -> Dict:
        """Sync GitHub pull request to our system"""
        try:
            external_id = str(pr_data.get('number'))
            
            # Check if PR already exists
            existing_pr = self.db.query(PullRequest).filter(
                PullRequest.repository_id == repository.id,
                PullRequest.external_id == external_id
            ).first()
            
            # Get or create author user
            author_data = pr_data.get('user', {})
            author = self._get_or_create_user(author_data.get('login'), author_data.get('email'))
            
            pr_info = {
                'title': pr_data.get('title'),
                'description': pr_data.get('body', ''),
                'source_branch': pr_data.get('head', {}).get('ref'),
                'target_branch': pr_data.get('base', {}).get('ref'),
                'external_id': external_id,
                'external_url': pr_data.get('html_url'),
                'status': 'open' if pr_data.get('state') == 'open' else pr_data.get('state'),
                'commits_count': pr_data.get('commits', 0),
                'additions': pr_data.get('additions', 0),
                'deletions': pr_data.get('deletions', 0),
                'files_changed_count': pr_data.get('changed_files', 0)
            }
            
            if existing_pr:
                # Update existing PR
                for key, value in pr_info.items():
                    setattr(existing_pr, key, value)
                self.db.commit()
                pr_id = existing_pr.id
            else:
                # Create new PR
                pr_number = self.code_review_service.generate_pr_number(repository.id)
                pull_request = PullRequest(
                    id=str(uuid.uuid4()),
                    repository_id=repository.id,
                    pr_number=pr_number,
                    author_id=author.id,
                    **pr_info
                )
                self.db.add(pull_request)
                self.db.commit()
                pr_id = pull_request.id
            
            # Sync PR files and trigger automated review
            await self._sync_pr_files(pr_id, pr_data)
            await self._trigger_automated_review(pr_id, author.id)
            
            return {"message": "Pull request synced successfully", "status": "success", "pr_id": pr_id}
            
        except Exception as e:
            return {"message": f"Failed to sync PR: {str(e)}", "status": "error"}
    
    async def _sync_gitlab_merge_request(self, repository: Repository, mr_data: Dict) -> Dict:
        """Sync GitLab merge request to our system"""
        # Similar implementation to GitHub but with GitLab API structure
        # Implementation would follow similar pattern to _sync_github_pull_request
        return {"message": "GitLab MR sync not fully implemented", "status": "todo"}
    
    async def _sync_pr_files(self, pr_id: str, pr_data: Dict):
        """Sync pull request files from external API"""
        try:
            # For GitHub, we would need to make additional API calls to get file details
            # This is a simplified version - in production, you'd fetch from GitHub API
            
            files_url = pr_data.get('url') + '/files' if pr_data.get('url') else None
            if not files_url:
                return
            
            # Here you would make API call to get file details
            # For now, we'll create placeholder entries
            
            # Clear existing files
            self.db.query(PullRequestFile).filter(
                PullRequestFile.pull_request_id == pr_id
            ).delete()
            
            # Add files (in real implementation, fetch from API)
            # This is just a placeholder
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error syncing PR files: {e}")
    
    async def _trigger_automated_review(self, pr_id: str, author_id: int):
        """Trigger automated AI review for pull request"""
        try:
            ai_reviewer = get_or_create_ai_reviewer(self.db)
            review_service = AutomatedReviewService(self.db)
            
            # Perform analysis
            analysis_results = review_service.analyze_pull_request(pr_id, ai_reviewer.id)
            
            if not analysis_results.get('error'):
                # Create automated review
                review_service.create_automated_review(pr_id, analysis_results, ai_reviewer.id)
                
        except Exception as e:
            print(f"Error triggering automated review: {e}")
    
    async def _close_pull_request(self, repository: Repository, pr_data: Dict) -> Dict:
        """Close pull request in our system"""
        external_id = str(pr_data.get('number', pr_data.get('iid', '')))
        
        pr = self.db.query(PullRequest).filter(
            PullRequest.repository_id == repository.id,
            PullRequest.external_id == external_id
        ).first()
        
        if pr:
            pr.status = 'merged' if pr_data.get('merged', False) else 'closed'
            if pr_data.get('merged_at'):
                pr.merged_at = pr_data['merged_at']
            if pr_data.get('closed_at'):
                pr.closed_at = pr_data['closed_at']
            self.db.commit()
            
            return {"message": "Pull request closed", "status": "success"}
        
        return {"message": "Pull request not found", "status": "not_found"}
    
    async def _handle_github_push(self, event_data: Dict) -> Dict:
        """Handle GitHub push events"""
        # Could trigger automated analysis of new commits
        return {"message": "Push event received", "status": "success"}
    
    async def _handle_gitlab_push(self, event_data: Dict) -> Dict:
        """Handle GitLab push events"""
        # Similar to GitHub push handling
        return {"message": "Push event received", "status": "success"}
    
    async def _handle_github_repository(self, event_data: Dict) -> Dict:
        """Handle GitHub repository events (created, updated, etc.)"""
        return {"message": "Repository event received", "status": "success"}
    
    def _get_or_create_user(self, username: str, email: str = None) -> User:
        """Get or create user from external service data"""
        if not username:
            # Return a default user or raise error
            return self.db.query(User).filter(User.is_admin == True).first()
        
        user = self.db.query(User).filter(User.username == username).first()
        
        if not user:
            user = User(
                username=username,
                email=email or f"{username}@external.user",
                full_name=username,
                hashed_password="",  # External user, no local password
                is_active=True,
                is_admin=False
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def _verify_github_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        try:
            # In production, get this from environment variables
            webhook_secret = "your-webhook-secret"
            
            expected_signature = 'sha256=' + hmac.new(
                webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False