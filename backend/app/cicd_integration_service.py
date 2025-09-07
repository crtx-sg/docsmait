# backend/app/cicd_integration_service.py
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from .db_models import PullRequest, Repository, Project
from .email_service import email_service

class CICDIntegrationService:
    """Service for CI/CD pipeline integration and status tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_build_status(self, pr_id: str) -> Optional[Dict]:
        """Get CI/CD build status for a pull request"""
        try:
            pr = self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()
            if not pr or not pr.external_url:
                return None
            
            # Extract provider and repo info from external URL
            provider_info = self._parse_external_url(pr.external_url)
            if not provider_info:
                return None
            
            # Get build status based on provider
            if provider_info['provider'] == 'github':
                return self._get_github_build_status(provider_info, pr)
            elif provider_info['provider'] == 'gitlab':
                return self._get_gitlab_build_status(provider_info, pr)
            
            return None
        except Exception as e:
            print(f"Error getting build status: {e}")
            return None
    
    def get_test_coverage(self, pr_id: str) -> Optional[Dict]:
        """Get test coverage information for a pull request"""
        try:
            pr = self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()
            if not pr:
                return None
            
            # Mock coverage data - in real implementation, this would fetch from coverage tools
            return {
                "coverage_percentage": 85.2,
                "lines_covered": 1420,
                "lines_total": 1667,
                "coverage_trend": "increased",  # increased, decreased, stable
                "coverage_change": 2.1,  # percentage change
                "files_coverage": [
                    {"file": "backend/app/services.py", "coverage": 92.5},
                    {"file": "frontend/pages/Code.py", "coverage": 78.3},
                    {"file": "backend/app/models.py", "coverage": 95.1},
                ],
                "uncovered_lines": [
                    {"file": "backend/app/services.py", "lines": [45, 67, 89]},
                    {"file": "frontend/pages/Code.py", "lines": [123, 156, 234, 267]},
                ]
            }
        except Exception as e:
            print(f"Error getting test coverage: {e}")
            return None
    
    def get_quality_gates(self, pr_id: str) -> List[Dict]:
        """Get quality gate status for a pull request"""
        try:
            pr = self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()
            if not pr:
                return []
            
            # Mock quality gates - in real implementation, integrate with SonarQube, CodeClimate, etc.
            gates = [
                {
                    "name": "Code Coverage",
                    "status": "passed",  # passed, failed, pending
                    "threshold": 80.0,
                    "current_value": 85.2,
                    "message": "Coverage above minimum threshold"
                },
                {
                    "name": "Security Scan",
                    "status": "pending",
                    "threshold": 0,
                    "current_value": 2,
                    "message": "2 security issues detected - review required"
                },
                {
                    "name": "Code Quality",
                    "status": "passed",
                    "threshold": 3.0,  # maintainability rating
                    "current_value": 2.1,
                    "message": "Code maintainability rating: B"
                },
                {
                    "name": "Technical Debt",
                    "status": "passed",
                    "threshold": 5.0,  # debt ratio %
                    "current_value": 2.3,
                    "message": "Technical debt ratio within acceptable limits"
                },
                {
                    "name": "Duplication",
                    "status": "failed",
                    "threshold": 3.0,  # duplication %
                    "current_value": 4.2,
                    "message": "Code duplication above threshold (4.2% > 3.0%)"
                }
            ]
            
            return gates
        except Exception as e:
            print(f"Error getting quality gates: {e}")
            return []
    
    def get_deployment_status(self, pr_id: str) -> Optional[Dict]:
        """Get deployment pipeline status"""
        try:
            pr = self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()
            if not pr:
                return None
            
            # Mock deployment status
            return {
                "environments": [
                    {
                        "name": "Development",
                        "status": "deployed",  # deployed, deploying, failed, not_deployed
                        "version": "v1.2.3-pr123",
                        "deployed_at": "2025-01-06T10:30:00Z",
                        "url": "https://dev-pr123.docsmait.com",
                        "health_check": "healthy"
                    },
                    {
                        "name": "Staging",
                        "status": "pending",
                        "version": None,
                        "deployed_at": None,
                        "url": None,
                        "health_check": None
                    },
                    {
                        "name": "Production",
                        "status": "not_deployed",
                        "version": None,
                        "deployed_at": None,
                        "url": None,
                        "health_check": None
                    }
                ],
                "pipeline_status": "running",
                "pipeline_url": "https://github.com/user/repo/actions/runs/123456"
            }
        except Exception as e:
            print(f"Error getting deployment status: {e}")
            return None
    
    def check_merge_requirements(self, pr_id: str) -> Dict:
        """Check if pull request meets all merge requirements"""
        try:
            pr = self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()
            if not pr:
                return {"can_merge": False, "reason": "Pull request not found"}
            
            # Get various status checks
            build_status = self.get_build_status(pr_id)
            quality_gates = self.get_quality_gates(pr_id)
            
            requirements = {
                "build_passed": build_status and build_status.get("status") == "success",
                "quality_gates_passed": all(gate["status"] == "passed" for gate in quality_gates),
                "reviews_approved": pr.status == "approved",
                "no_conflicts": True,  # Would check for merge conflicts
                "branch_up_to_date": True  # Would check if branch is up to date
            }
            
            failed_requirements = [key for key, value in requirements.items() if not value]
            
            return {
                "can_merge": len(failed_requirements) == 0,
                "requirements": requirements,
                "failed_requirements": failed_requirements,
                "message": "Ready to merge" if not failed_requirements else f"Cannot merge: {', '.join(failed_requirements)}"
            }
        except Exception as e:
            print(f"Error checking merge requirements: {e}")
            return {"can_merge": False, "reason": f"Error: {str(e)}"}
    
    def trigger_deployment(self, pr_id: str, environment: str) -> Dict:
        """Trigger deployment to specified environment"""
        try:
            pr = self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()
            if not pr:
                return {"success": False, "message": "Pull request not found"}
            
            # Mock deployment trigger
            if environment in ["development", "staging"]:
                return {
                    "success": True,
                    "message": f"Deployment to {environment} triggered successfully",
                    "deployment_id": f"deploy-{pr_id}-{environment}-{int(datetime.now().timestamp())}",
                    "estimated_duration": "5-10 minutes"
                }
            else:
                return {"success": False, "message": f"Deployment to {environment} not allowed for pull requests"}
        except Exception as e:
            return {"success": False, "message": f"Deployment failed: {str(e)}"}
    
    def _parse_external_url(self, url: str) -> Optional[Dict]:
        """Parse external URL to determine provider and repository info"""
        try:
            if 'github.com' in url:
                # Extract owner/repo from GitHub URL
                parts = url.split('/')
                if len(parts) >= 5:
                    return {
                        'provider': 'github',
                        'owner': parts[3],
                        'repo': parts[4],
                        'pr_number': parts[6] if len(parts) > 6 else None
                    }
            elif 'gitlab.com' in url:
                # Extract project info from GitLab URL
                parts = url.split('/')
                if len(parts) >= 6:
                    return {
                        'provider': 'gitlab',
                        'namespace': parts[3],
                        'project': parts[4],
                        'mr_number': parts[7] if len(parts) > 7 else None
                    }
            
            return None
        except Exception:
            return None
    
    def _get_github_build_status(self, provider_info: Dict, pr: PullRequest) -> Optional[Dict]:
        """Get build status from GitHub Actions"""
        try:
            # Mock GitHub Actions status
            return {
                "status": "success",  # success, failure, pending, error
                "conclusion": "success",
                "started_at": "2025-01-06T10:00:00Z",
                "completed_at": "2025-01-06T10:15:00Z",
                "duration_minutes": 15,
                "jobs": [
                    {"name": "Test", "status": "completed", "conclusion": "success"},
                    {"name": "Build", "status": "completed", "conclusion": "success"},
                    {"name": "Security Scan", "status": "completed", "conclusion": "success"},
                    {"name": "Deploy to Dev", "status": "completed", "conclusion": "success"}
                ],
                "url": f"https://github.com/{provider_info['owner']}/{provider_info['repo']}/actions"
            }
        except Exception as e:
            print(f"Error getting GitHub build status: {e}")
            return None
    
    def _get_gitlab_build_status(self, provider_info: Dict, pr: PullRequest) -> Optional[Dict]:
        """Get build status from GitLab CI/CD"""
        try:
            # Mock GitLab CI/CD status
            return {
                "status": "success",
                "started_at": "2025-01-06T10:00:00Z",
                "finished_at": "2025-01-06T10:12:00Z",
                "duration_minutes": 12,
                "stages": [
                    {"name": "build", "status": "success"},
                    {"name": "test", "status": "success"},
                    {"name": "security", "status": "success"},
                    {"name": "deploy", "status": "success"}
                ],
                "url": f"https://gitlab.com/{provider_info['namespace']}/{provider_info['project']}/-/pipelines"
            }
        except Exception as e:
            print(f"Error getting GitLab build status: {e}")
            return None
    
    def send_deployment_notification(self, pr_id: str, environment: str, status: str, details: Dict = None):
        """Send deployment notification emails"""
        try:
            pr = self.db.query(PullRequest).join(Repository).join(Project).filter(
                PullRequest.id == pr_id
            ).first()
            
            if not pr or not pr.author.email:
                return
            
            project_name = pr.repository.project.name if pr.repository.project else "Unknown Project"
            
            # Send deployment notification
            email_service.send_deployment_notification(
                project_name=project_name,
                pr_title=pr.title,
                environment=environment,
                status=status,
                details=details or {},
                recipient_email=pr.author.email
            )
        except Exception as e:
            print(f"Failed to send deployment notification: {e}")

def create_mock_pipeline_data():
    """Create mock CI/CD pipeline data for testing"""
    return {
        "build_history": [
            {
                "id": "build-123",
                "status": "success",
                "started_at": "2025-01-06T09:00:00Z",
                "completed_at": "2025-01-06T09:15:00Z",
                "duration_minutes": 15,
                "commit_hash": "abc123def456",
                "branch": "feature/new-feature"
            },
            {
                "id": "build-122",
                "status": "failure",
                "started_at": "2025-01-05T14:30:00Z",
                "completed_at": "2025-01-05T14:35:00Z",
                "duration_minutes": 5,
                "commit_hash": "def456ghi789",
                "branch": "feature/new-feature"
            }
        ],
        "performance_metrics": {
            "average_build_time": 12.5,
            "success_rate": 87.3,
            "total_builds": 156,
            "builds_this_month": 23
        }
    }