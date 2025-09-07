# backend/app/git_integration_service.py
import os
import git
import tempfile
import shutil
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import requests
import base64
from datetime import datetime

from .config import config

class GitIntegrationService:
    """Service for Git repository operations and integration with external providers"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix='docsmait_git_')
        
    def __del__(self):
        """Cleanup temporary directory"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def clone_repository(self, git_url: str, branch: str = None) -> Optional[str]:
        """Clone a Git repository to temporary directory"""
        try:
            repo_name = self._get_repo_name_from_url(git_url)
            local_path = os.path.join(self.temp_dir, repo_name)
            
            # Clone with specific branch if provided
            if branch:
                repo = git.Repo.clone_from(git_url, local_path, branch=branch)
            else:
                repo = git.Repo.clone_from(git_url, local_path)
            
            return local_path
        except Exception as e:
            print(f"Error cloning repository {git_url}: {e}")
            return None
    
    def get_repository_branches(self, git_url: str) -> List[str]:
        """Get list of branches from a Git repository"""
        try:
            # For GitHub, use API
            if 'github.com' in git_url:
                return self._get_github_branches(git_url)
            elif 'gitlab.com' in git_url:
                return self._get_gitlab_branches(git_url)
            else:
                # Fallback: clone and get branches
                return self._get_branches_via_clone(git_url)
        except Exception as e:
            print(f"Error getting branches for {git_url}: {e}")
            return []
    
    def get_file_content(self, repo_path: str, file_path: str, branch: str = None) -> Optional[str]:
        """Get content of a specific file from repository"""
        try:
            repo = git.Repo(repo_path)
            if branch and branch != repo.active_branch.name:
                repo.git.checkout(branch)
            
            full_path = os.path.join(repo_path, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            return None
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def get_diff_between_branches(self, repo_path: str, source_branch: str, target_branch: str) -> Optional[str]:
        """Get diff between two branches"""
        try:
            repo = git.Repo(repo_path)
            
            # Get diff between branches
            diff = repo.git.diff(f"{target_branch}...{source_branch}")
            return diff
        except Exception as e:
            print(f"Error getting diff between {source_branch} and {target_branch}: {e}")
            return None
    
    def parse_diff_content(self, diff_content: str) -> List[Dict]:
        """Parse diff content into structured format"""
        if not diff_content:
            return []
        
        files = []
        current_file = None
        
        for line in diff_content.split('\n'):
            if line.startswith('diff --git'):
                if current_file:
                    files.append(current_file)
                
                # Extract file paths
                parts = line.split(' ')
                if len(parts) >= 4:
                    old_path = parts[2].replace('a/', '')
                    new_path = parts[3].replace('b/', '')
                    current_file = {
                        'file_path': new_path,
                        'old_file_path': old_path if old_path != new_path else None,
                        'file_status': 'modified',
                        'additions': 0,
                        'deletions': 0,
                        'diff_content': []
                    }
            elif line.startswith('new file mode'):
                if current_file:
                    current_file['file_status'] = 'added'
            elif line.startswith('deleted file mode'):
                if current_file:
                    current_file['file_status'] = 'deleted'
            elif line.startswith('+') and not line.startswith('+++'):
                if current_file:
                    current_file['additions'] += 1
                    current_file['diff_content'].append(line)
            elif line.startswith('-') and not line.startswith('---'):
                if current_file:
                    current_file['deletions'] += 1
                    current_file['diff_content'].append(line)
            else:
                if current_file:
                    current_file['diff_content'].append(line)
        
        # Add last file
        if current_file:
            files.append(current_file)
        
        # Convert diff_content lists to strings
        for file in files:
            file['diff_content'] = '\n'.join(file['diff_content'])
            file['changes'] = file['additions'] + file['deletions']
        
        return files
    
    def get_commit_info(self, repo_path: str, commit_hash: str = None) -> Optional[Dict]:
        """Get information about a specific commit"""
        try:
            repo = git.Repo(repo_path)
            commit = repo.commit(commit_hash) if commit_hash else repo.head.commit
            
            return {
                'hash': commit.hexsha,
                'short_hash': commit.hexsha[:8],
                'author': str(commit.author),
                'author_email': commit.author.email,
                'message': commit.message.strip(),
                'date': datetime.fromtimestamp(commit.committed_date).isoformat(),
                'files_changed': len(commit.stats.files),
                'insertions': commit.stats.total['insertions'],
                'deletions': commit.stats.total['deletions']
            }
        except Exception as e:
            print(f"Error getting commit info: {e}")
            return None
    
    def _get_repo_name_from_url(self, git_url: str) -> str:
        """Extract repository name from Git URL"""
        parsed = urlparse(git_url)
        path = parsed.path.strip('/')
        if path.endswith('.git'):
            path = path[:-4]
        return path.split('/')[-1]
    
    def _get_github_branches(self, git_url: str) -> List[str]:
        """Get branches from GitHub API"""
        try:
            # Extract owner/repo from URL
            parsed = urlparse(git_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo = path_parts[1].replace('.git', '')
                
                # GitHub API call
                api_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    branches = response.json()
                    return [branch['name'] for branch in branches]
            
            return []
        except Exception as e:
            print(f"Error getting GitHub branches: {e}")
            return []
    
    def _get_gitlab_branches(self, git_url: str) -> List[str]:
        """Get branches from GitLab API"""
        try:
            # Extract project path from URL
            parsed = urlparse(git_url)
            path = parsed.path.strip('/').replace('.git', '')
            project_id = requests.utils.quote(path, safe='')
            
            # GitLab API call
            api_url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/branches"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                branches = response.json()
                return [branch['name'] for branch in branches]
            
            return []
        except Exception as e:
            print(f"Error getting GitLab branches: {e}")
            return []
    
    def _get_branches_via_clone(self, git_url: str) -> List[str]:
        """Get branches by cloning repository (fallback method)"""
        try:
            temp_path = self.clone_repository(git_url)
            if temp_path:
                repo = git.Repo(temp_path)
                branches = [ref.name.replace('origin/', '') for ref in repo.remote().refs]
                return branches
            return []
        except Exception as e:
            print(f"Error getting branches via clone: {e}")
            return []
    
    def validate_git_url(self, git_url: str) -> Tuple[bool, str]:
        """Validate if a Git URL is accessible"""
        try:
            # Try to get basic info without cloning
            if 'github.com' in git_url:
                parsed = urlparse(git_url)
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    owner = path_parts[0]
                    repo = path_parts[1].replace('.git', '')
                    api_url = f"https://api.github.com/repos/{owner}/{repo}"
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        return True, "Repository is accessible"
                    elif response.status_code == 404:
                        return False, "Repository not found or private"
                    else:
                        return False, f"HTTP {response.status_code}"
            
            # For other providers, try basic connection
            try:
                # Simple test - try to fetch remote info
                result = git.cmd.Git().ls_remote(git_url, heads=True)
                return True, "Repository is accessible"
            except git.GitCommandError as e:
                return False, f"Git error: {str(e)}"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

# Global instance
git_service = GitIntegrationService()