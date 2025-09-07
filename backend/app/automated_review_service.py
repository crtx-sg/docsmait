# backend/app/automated_review_service.py
import json
import re
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from .ai_service import ai_service
from .git_integration_service import git_service
from .db_models import PullRequest, PullRequestFile, CodeReview, User
from .models import CodeReviewCreate, CodeReviewResponse
from .code_review_service import CodeReviewService

class AutomatedReviewService:
    """AI-powered automated code review service using Ollama"""
    
    def __init__(self, db: Session):
        self.db = db
        self.code_review_service = CodeReviewService(db)
        
    def analyze_pull_request(self, pr_id: str, user_id: int) -> Dict:
        """Perform comprehensive AI analysis of a pull request"""
        try:
            # Get pull request and files
            pr = self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()
            if not pr:
                return {"error": "Pull request not found"}
            
            pr_files = self.db.query(PullRequestFile).filter(
                PullRequestFile.pull_request_id == pr_id
            ).all()
            
            # Perform analysis even if no files (for demonstration)
            analysis_results = {
                "pr_id": pr_id,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {},
                "files": [],
                "security_issues": [],
                "performance_issues": [],
                "code_quality_issues": [],
                "suggestions": []
            }
            
            total_additions = 0
            total_deletions = 0
            
            if pr_files:
                # Analyze each file
                for pr_file in pr_files:
                    try:
                        file_analysis = self._analyze_file(pr_file)
                        analysis_results["files"].append(file_analysis)
                        
                        # Safely aggregate issues
                        for issue_type in ["security_issues", "performance_issues", "code_quality_issues", "suggestions"]:
                            if issue_type in file_analysis:
                                analysis_results[issue_type].extend(file_analysis[issue_type])
                        
                        # Safely access file attributes
                        total_additions += getattr(pr_file, 'additions', 0) or 0
                        total_deletions += getattr(pr_file, 'deletions', 0) or 0
                        
                    except Exception as file_error:
                        print(f"Error analyzing file {getattr(pr_file, 'file_path', 'unknown')}: {str(file_error)}")
                        continue
            else:
                # Create demo analysis for PRs without files
                analysis_results["suggestions"] = [
                    {
                        "type": "improvement",
                        "severity": "low",
                        "description": "No code files found to analyze. Consider adding files to this pull request.",
                        "rationale": "Pull requests should include code changes for meaningful review"
                    }
                ]
                analysis_results["code_quality_issues"] = [
                    {
                        "type": "code_quality",
                        "severity": "low",
                        "description": "Empty pull request - no files to review",
                        "file_path": "N/A",
                        "line": 0
                    }
                ]
            
            # Generate summary
            analysis_results["summary"] = self._generate_summary(analysis_results, total_additions, total_deletions)
            
            return analysis_results
            
        except Exception as e:
            print(f"Automated review analysis error: {str(e)}")
            # Return a minimal working response even on error
            return {
                "error": f"Analysis failed: {str(e)}",
                "pr_id": pr_id,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_files": 0,
                    "total_additions": 0,
                    "total_deletions": 0,
                    "security_issues_count": 0,
                    "performance_issues_count": 0,
                    "code_quality_issues_count": 1,
                    "suggestions_count": 1,
                    "overall_risk": "low",
                    "recommendation": "⚠️ Analysis failed - manual review required"
                },
                "files": [],
                "security_issues": [],
                "performance_issues": [],
                "code_quality_issues": [
                    {
                        "type": "system",
                        "severity": "low", 
                        "description": "Automated analysis encountered an error",
                        "file_path": "system",
                        "line": 0
                    }
                ],
                "suggestions": [
                    {
                        "type": "system",
                        "severity": "low",
                        "description": "Manual code review recommended due to analysis error",
                        "rationale": "Automated tools failed to complete analysis"
                    }
                ]
            }
    
    def create_automated_review(self, pr_id: str, analysis_results: Dict, reviewer_user_id: int) -> Optional[CodeReviewResponse]:
        """Create an automated code review based on analysis results"""
        try:
            # Generate review summary comment
            summary_comment = self._generate_review_comment(analysis_results)
            
            # Create review
            review_data = CodeReviewCreate(
                pull_request_id=pr_id,
                reviewer_ids=[reviewer_user_id],  # Use AI bot user ID
                summary_comment=summary_comment,
                status="commented"  # Or "changes_requested" if critical issues found
            )
            
            # Determine review status based on issues found
            critical_issues = analysis_results.get("security_issues", []) + [
                issue for issue in analysis_results.get("code_quality_issues", [])
                if issue.get("severity") == "critical"
            ]
            
            if critical_issues:
                review_data.status = "changes_requested"
            elif analysis_results.get("suggestions"):
                review_data.status = "commented"
            else:
                review_data.status = "approved"
            
            reviews = self.code_review_service.create_code_review(review_data, reviewer_user_id)
            return reviews[0] if reviews else None
            
        except Exception as e:
            print(f"Error creating automated review: {e}")
            return None
    
    def _analyze_file(self, pr_file: PullRequestFile) -> Dict:
        """Analyze a single file for issues and improvements"""
        file_analysis = {
            "file_path": pr_file.file_path,
            "file_status": pr_file.file_status,
            "additions": pr_file.additions,
            "deletions": pr_file.deletions,
            "security_issues": [],
            "performance_issues": [],
            "code_quality_issues": [],
            "suggestions": []
        }
        
        if not pr_file.patch_content:
            return file_analysis
        
        # Get file extension to determine analysis approach
        file_ext = self._get_file_extension(pr_file.file_path)
        language = self._detect_language(file_ext)
        
        # Analyze security issues
        security_issues = self._analyze_security(pr_file.patch_content, language)
        file_analysis["security_issues"] = security_issues
        
        # Analyze performance issues
        performance_issues = self._analyze_performance(pr_file.patch_content, language)
        file_analysis["performance_issues"] = performance_issues
        
        # Analyze code quality
        quality_issues = self._analyze_code_quality(pr_file.patch_content, language)
        file_analysis["code_quality_issues"] = quality_issues
        
        # Generate AI suggestions
        suggestions = self._generate_ai_suggestions(pr_file.patch_content, language)
        file_analysis["suggestions"] = suggestions
        
        return file_analysis
    
    def _analyze_security(self, diff_content: str, language: str) -> List[Dict]:
        """Analyze code for security vulnerabilities"""
        security_issues = []
        
        # Security patterns by language
        security_patterns = {
            "python": [
                (r"exec\s*\(", "Dangerous use of exec() - code injection risk"),
                (r"eval\s*\(", "Dangerous use of eval() - code injection risk"),
                (r"import\s+pickle", "Pickle usage - deserialization vulnerability risk"),
                (r"shell=True", "Shell command injection risk"),
                (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
                (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected"),
                (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret detected"),
            ],
            "javascript": [
                (r"eval\s*\(", "Dangerous use of eval() - code injection risk"),
                (r"innerHTML\s*=", "Potential XSS vulnerability with innerHTML"),
                (r"document\.write\s*\(", "Potential XSS vulnerability with document.write"),
                (r"password\s*:\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
                (r"apiKey\s*:\s*['\"][^'\"]+['\"]", "Hardcoded API key detected"),
            ],
            "java": [
                (r"Runtime\.getRuntime\(\)\.exec", "Command injection risk"),
                (r"password\s*=\s*\"[^\"]+\"", "Hardcoded password detected"),
                (r"Statement\.execute", "Potential SQL injection - use PreparedStatement"),
            ]
        }
        
        patterns = security_patterns.get(language, [])
        
        for pattern, description in patterns:
            try:
                matches = re.finditer(pattern, diff_content, re.IGNORECASE)
                for match in matches:
                    line_num = diff_content[:match.start()].count('\n') + 1
                    security_issues.append({
                        "type": "security",
                        "severity": "high",
                        "line": line_num,
                        "description": description,
                        "pattern": pattern,
                        "match": match.group(),
                        "file_path": "unknown"
                    })
            except Exception as regex_error:
                print(f"Regex error in security analysis: {regex_error}")
                continue
        
        return security_issues
    
    def _analyze_performance(self, diff_content: str, language: str) -> List[Dict]:
        """Analyze code for performance issues"""
        performance_issues = []
        
        # Performance patterns by language
        performance_patterns = {
            "python": [
                (r"\.append\(.*\)\s*in\s+for\s+", "Consider list comprehension for better performance"),
                (r"range\(len\(", "Consider using enumerate() instead"),
                (r"\.keys\(\)\s*in\s+for\s+", "Iterating over dict.keys() - consider dict directly"),
            ],
            "javascript": [
                (r"document\.getElementById.*in.*for\s+", "DOM queries in loop - cache outside loop"),
                (r"\.innerHTML\s*\+=", "String concatenation in loop - use array.join()"),
            ],
            "java": [
                (r"String\s+\w+\s*\+=", "String concatenation in loop - use StringBuilder"),
                (r"\.size\(\).*for\s*\(", "Method call in loop condition - cache size"),
            ]
        }
        
        patterns = performance_patterns.get(language, [])
        
        for pattern, description in patterns:
            try:
                matches = re.finditer(pattern, diff_content, re.IGNORECASE)
                for match in matches:
                    line_num = diff_content[:match.start()].count('\n') + 1
                    performance_issues.append({
                        "type": "performance",
                        "severity": "medium",
                        "line": line_num,
                        "description": description,
                        "pattern": pattern,
                        "match": match.group(),
                        "file_path": "unknown"
                    })
            except Exception as regex_error:
                print(f"Regex error in performance analysis: {regex_error}")
                continue
        
        return performance_issues
    
    def _analyze_code_quality(self, diff_content: str, language: str) -> List[Dict]:
        """Analyze code quality issues"""
        quality_issues = []
        
        # Basic quality checks
        lines = diff_content.split('\n')
        added_lines = [line for line in lines if line.startswith('+') and not line.startswith('+++')]
        
        for i, line in enumerate(added_lines):
            line_content = line[1:].strip()  # Remove + prefix
            
            # Long line check
            if len(line_content) > 120:
                quality_issues.append({
                    "type": "code_quality",
                    "severity": "low",
                    "line": i + 1,
                    "description": f"Line too long ({len(line_content)} chars) - consider breaking it up",
                    "suggestion": "Break long lines for better readability",
                    "file_path": "unknown"
                })
            
            # TODO/FIXME comments
            if re.search(r'(TODO|FIXME|HACK)', line_content, re.IGNORECASE):
                quality_issues.append({
                    "type": "code_quality",
                    "severity": "low",
                    "line": i + 1,
                    "description": "TODO/FIXME comment found - consider addressing before merge",
                    "match": line_content
                })
        
        return quality_issues
    
    def _generate_ai_suggestions(self, diff_content: str, language: str) -> List[Dict]:
        """Generate AI-powered suggestions for code improvement"""
        try:
            # Prepare prompt for AI analysis
            prompt = f"""
            You are an expert code reviewer. Analyze the following {language} code diff and provide specific, actionable suggestions for improvement.
            Focus on:
            1. Code quality and maintainability
            2. Best practices for {language}
            3. Potential bugs or edge cases
            4. Performance optimizations
            5. Code readability improvements
            
            Code diff:
            ```
            {diff_content[:2000]}  # Limit to avoid token limits
            ```
            
            Provide suggestions in JSON format:
            {{
                "suggestions": [
                    {{
                        "type": "improvement",
                        "severity": "medium",
                        "description": "Specific suggestion",
                        "rationale": "Why this improvement helps"
                    }}
                ]
            }}
            """
            
            # Get AI analysis
            ai_response = ai_service.generate_response(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse AI response
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    suggestions_data = json.loads(json_match.group())
                    return suggestions_data.get("suggestions", [])
            except json.JSONDecodeError:
                # Fallback: parse text response
                suggestions = []
                for line in ai_response.split('\n'):
                    if line.strip() and ('suggest' in line.lower() or 'improve' in line.lower()):
                        suggestions.append({
                            "type": "improvement",
                            "severity": "medium",
                            "description": line.strip(),
                            "rationale": "AI-generated suggestion"
                        })
                return suggestions[:5]  # Limit to 5 suggestions
            
            return []
        except Exception as e:
            print(f"Error generating AI suggestions: {e}")
            return []
    
    def _generate_summary(self, analysis_results: Dict, total_additions: int, total_deletions: int) -> Dict:
        """Generate analysis summary"""
        return {
            "total_files": len(analysis_results["files"]),
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "security_issues_count": len(analysis_results["security_issues"]),
            "performance_issues_count": len(analysis_results["performance_issues"]),
            "code_quality_issues_count": len(analysis_results["code_quality_issues"]),
            "suggestions_count": len(analysis_results["suggestions"]),
            "overall_risk": self._calculate_risk_level(analysis_results),
            "recommendation": self._generate_recommendation(analysis_results)
        }
    
    def _calculate_risk_level(self, analysis_results: Dict) -> str:
        """Calculate overall risk level"""
        security_count = len(analysis_results["security_issues"])
        
        if security_count > 0:
            return "high"
        elif len(analysis_results["performance_issues"]) > 3:
            return "medium"
        elif len(analysis_results["code_quality_issues"]) > 5:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendation(self, analysis_results: Dict) -> str:
        """Generate overall recommendation"""
        security_count = len(analysis_results["security_issues"])
        performance_count = len(analysis_results["performance_issues"])
        quality_count = len(analysis_results["code_quality_issues"])
        
        if security_count > 0:
            return "⚠️ Changes requested - Security issues must be addressed before merge"
        elif performance_count > 3 or quality_count > 5:
            return "💭 Consider addressing performance and quality issues"
        else:
            return "✅ Code looks good - Ready for review"
    
    def _generate_review_comment(self, analysis_results: Dict) -> str:
        """Generate comprehensive review comment"""
        comment_parts = ["## 🤖 Automated Code Review\n"]
        
        summary = analysis_results["summary"]
        
        # Add summary
        comment_parts.append(f"**Files analyzed:** {summary['total_files']}")
        comment_parts.append(f"**Changes:** +{summary['total_additions']} -{summary['total_deletions']}")
        comment_parts.append(f"**Risk Level:** {summary['overall_risk'].upper()}")
        comment_parts.append(f"\n{summary['recommendation']}\n")
        
        # Add security issues
        if analysis_results["security_issues"]:
            comment_parts.append("### 🔒 Security Issues")
            for issue in analysis_results["security_issues"][:5]:  # Limit to 5
                comment_parts.append(f"- **{issue['file_path']}:{issue.get('line', '?')}** - {issue['description']}")
            comment_parts.append("")
        
        # Add performance issues
        if analysis_results["performance_issues"]:
            comment_parts.append("### ⚡ Performance Considerations")
            for issue in analysis_results["performance_issues"][:3]:  # Limit to 3
                comment_parts.append(f"- **{issue['file_path']}:{issue.get('line', '?')}** - {issue['description']}")
            comment_parts.append("")
        
        # Add suggestions
        if analysis_results["suggestions"]:
            comment_parts.append("### 💡 Suggestions for Improvement")
            for suggestion in analysis_results["suggestions"][:3]:  # Limit to 3
                comment_parts.append(f"- {suggestion['description']}")
                if suggestion.get("rationale"):
                    comment_parts.append(f"  *{suggestion['rationale']}*")
            comment_parts.append("")
        
        comment_parts.append("---")
        comment_parts.append("*This review was generated automatically by Docsmait AI*")
        
        return "\n".join(comment_parts)
    
    def _get_file_extension(self, file_path: str) -> str:
        """Get file extension"""
        return file_path.split('.')[-1].lower() if '.' in file_path else ''
    
    def _detect_language(self, file_ext: str) -> str:
        """Detect programming language from file extension"""
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'cs': 'csharp',
            'php': 'php',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust',
            'swift': 'swift',
            'kt': 'kotlin',
            'scala': 'scala'
        }
        return language_map.get(file_ext, 'unknown')

def get_or_create_ai_reviewer(db: Session) -> User:
    """Get or create AI reviewer user"""
    ai_reviewer = db.query(User).filter(User.username == "ai-reviewer").first()
    
    if not ai_reviewer:
        ai_reviewer = User(
            username="ai-reviewer",
            email="ai-reviewer@docsmait.system",
            password_hash="",  # No login for AI user
            is_admin=False,
            is_super_admin=False
        )
        db.add(ai_reviewer)
        db.commit()
        db.refresh(ai_reviewer)
    
    return ai_reviewer