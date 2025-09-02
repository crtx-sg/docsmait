# backend/app/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .config import config

class Project(BaseModel):
    name: str
    description: str

class KnowledgeBaseQuery(BaseModel):
    query: str

class KBDocumentUpload(BaseModel):
    content: str
    collection_name: str = Field(default_factory=lambda: config.DEFAULT_COLLECTION_NAME)

class KBConfig(BaseModel):
    chunk_size: int = Field(default_factory=lambda: config.DEFAULT_CHUNK_SIZE, ge=100, le=5000)
    collection_name: str = Field(default_factory=lambda: config.DEFAULT_COLLECTION_NAME)

class KBStats(BaseModel):
    documents_indexed: int
    total_documents: int
    queries_today: int
    search_queries_today: int
    index_size_mb: float
    last_updated: Optional[datetime]

class FileUpload(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    collection_name: str = Field(default_factory=lambda: config.DEFAULT_COLLECTION_NAME)

class ChatMessage(BaseModel):
    message: str
    collection_name: str = Field(default_factory=lambda: config.DEFAULT_COLLECTION_NAME)

class ChatResponse(BaseModel):
    response: str
    sources: List[dict] = []
    query_embedding_time: float
    retrieval_time: float
    llm_response_time: float

class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool = False
    is_super_admin: bool = False
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

class UserAdminStatusUpdate(BaseModel):
    user_id: int
    is_admin: bool

class SMTPConfig(BaseModel):
    server_name: str = Field(..., description="SMTP server hostname")
    port: int = Field(25, description="SMTP server port")
    username: str = Field(..., description="SMTP username/email")
    password: str = Field(..., description="SMTP password")
    auth_method: str = Field("normal_password", description="Authentication method")
    connection_security: str = Field("STARTTLS", description="Connection security")
    enabled: bool = Field(True, description="Enable email notifications")

class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, pattern="^[a-zA-Z0-9_-]+$")
    description: str = Field(default="", max_length=500)
    tags: List[str] = Field(default=[])

class CollectionUpdate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[List[str]] = Field(default=None)

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    created_by: int
    created_by_username: str
    created_at: datetime
    updated_at: datetime
    member_count: int
    is_member: bool = False
    is_creator: bool = False

class ProjectMember(BaseModel):
    user_id: int
    username: str
    email: str
    role: str = "member"
    added_at: datetime
    added_by: int
    added_by_username: str

class ProjectMemberAdd(BaseModel):
    user_id: int
    role: str = Field(default="member", pattern="^(member|admin)$")

class ProjectMemberAddByEmail(BaseModel):
    email: str = Field(..., min_length=1, max_length=200)
    role: str = Field(default="member", pattern="^(member|admin)$")

class ProjectResourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    resource_type: str = Field(..., pattern="^(glossary|reference|book)$")
    content: Optional[str] = Field(default=None, max_length=10000)

class ProjectResourceResponse(BaseModel):
    id: str
    project_id: str
    name: str
    resource_type: str
    content: Optional[str]
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    content_type: Optional[str]
    uploaded_by: int
    uploaded_by_username: str
    uploaded_at: datetime

# ========== Template Management Models ==========

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    document_type: str = Field(..., pattern="^(planning_documents|process_documents|specifications|records|templates|policies|manuals)$")
    content: str = Field(..., min_length=1)
    tags: List[str] = Field(default=[])

class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    document_type: Optional[str] = Field(default=None, pattern="^(planning_documents|process_documents|specifications|records|templates|policies|manuals)$")
    content: Optional[str] = Field(default=None, min_length=1)
    tags: Optional[List[str]] = Field(default=None)
    status: Optional[str] = Field(default=None, pattern="^(active|draft|request_review|approved)$")

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    document_type: str
    content: str
    tags: List[str]
    version: str
    status: str
    created_by: int
    created_by_username: str
    created_at: datetime
    updated_at: datetime
    approved_by: Optional[int] = None
    approved_by_username: Optional[str] = None
    approved_at: Optional[datetime] = None

class TemplateApprovalRequest(BaseModel):
    approver_ids: List[int] = Field(..., min_items=1)
    message: Optional[str] = Field(default="", max_length=500)

class TemplateApprovalResponse(BaseModel):
    template_id: str
    approved: bool
    comments: Optional[str] = Field(default=None, max_length=1000)

class TemplateExportRequest(BaseModel):
    format: str = Field(..., pattern="^(pdf)$")
    include_metadata: bool = Field(default=True)

# ========== Document Management Models ==========

class DocumentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    document_type: str = Field(..., pattern="^(planning_documents|process_documents|specifications|records|templates|policies|manuals)$")
    content: str = Field(default="", min_length=0)
    status: str = Field(default="draft", pattern="^(active|draft|request_review|approved)$")
    template_id: Optional[str] = Field(default=None)
    comment: Optional[str] = Field(default="", max_length=1000)
    reviewers: Optional[List[int]] = Field(default=None)

class DocumentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    document_type: Optional[str] = Field(default=None, pattern="^(planning_documents|process_documents|specifications|records|templates|policies|manuals)$")
    content: Optional[str] = Field(default=None, min_length=0)
    status: Optional[str] = Field(default=None, pattern="^(active|draft|request_review|approved)$")
    comment: Optional[str] = Field(default="", max_length=1000)
    reviewers: Optional[List[int]] = Field(default=None)

class DocumentResponse(BaseModel):
    id: str
    name: str
    document_type: str
    content: str
    project_id: str
    status: str
    template_id: Optional[str] = None
    created_by: int
    created_by_username: str
    created_at: datetime
    updated_at: datetime
    current_revision: int
    reviewers: List[dict] = []  # List of {"user_id": int, "username": str, "status": str}
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    reviewed_by_username: Optional[str] = None

class DocumentRevisionCreate(BaseModel):
    document_id: str
    content: str
    status: str
    comment: str = Field(default="", max_length=1000)
    reviewers: List[int] = Field(default=[])

class DocumentRevisionResponse(BaseModel):
    id: str
    document_id: str
    revision_number: int
    content: str
    status: str
    comment: str
    created_by: int
    created_by_username: str
    created_at: datetime
    reviewers: List[dict] = []  # List of {"user_id": int, "username": str, "status": str}

class DocumentReviewCreate(BaseModel):
    document_id: str
    revision_id: str
    approved: bool
    comments: Optional[str] = Field(default="", max_length=1000)

class DocumentReviewResponse(BaseModel):
    id: str
    document_id: str
    revision_id: str
    reviewer_id: int
    reviewer_username: str
    approved: bool
    comments: str
    reviewed_at: datetime

class DocumentExportRequest(BaseModel):
    format: str = Field(..., pattern="^(pdf)$")
    include_metadata: bool = Field(default=True)
    include_revision_history: bool = Field(default=False)

# ========== AI Assistant Models ==========

class AIAssistRequest(BaseModel):
    document_content: str = Field(..., max_length=50000)
    user_input: str = Field(..., min_length=1, max_length=1000)
    document_type: str = Field(..., min_length=1, max_length=100)
    custom_prompt: Optional[str] = Field(default=None, max_length=2000)
    model: Optional[str] = Field(default=None, max_length=50)
    debug_mode: bool = Field(default=False, description="Enable detailed logging for debugging")

class AIAssistResponse(BaseModel):
    success: bool
    response: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

class AIConfigUpdate(BaseModel):
    document_type: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    prompt: str = Field(..., min_length=1, max_length=2000)

class AISettingsUpdate(BaseModel):
    ollama_base_url: Optional[str] = Field(default=None, max_length=200)
    default_model: Optional[str] = Field(default=None, max_length=50)
    ai_timeout: Optional[int] = Field(default=None, ge=10, le=300)
    max_response_length: Optional[int] = Field(default=None, ge=100, le=10000)
    ai_context_window: Optional[int] = Field(default=None, ge=1000, le=20000)
    show_prompt: Optional[bool] = Field(default=None)

class AIUsageFeedback(BaseModel):
    feedback_rating: int = Field(..., ge=1, le=5)
    feedback_comment: Optional[str] = Field(default="", max_length=500)

# ========== Code Review Management Models ==========

class RepositoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, pattern="^[a-zA-Z0-9_-]+$")
    description: str = Field(default="", max_length=1000)
    git_url: Optional[str] = Field(default=None, max_length=500)
    git_provider: Optional[str] = Field(default=None, pattern="^(github|gitlab|bitbucket|azure|other)$")
    default_branch: str = Field(default="main", max_length=100)
    is_private: bool = Field(default=True)
    project_id: str = Field(..., description="Project UUID")

class RepositoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200, pattern="^[a-zA-Z0-9_-]+$")
    description: Optional[str] = Field(default=None, max_length=1000)
    git_url: Optional[str] = Field(default=None, max_length=500)
    git_provider: Optional[str] = Field(default=None, pattern="^(github|gitlab|bitbucket|azure|other)$")
    default_branch: Optional[str] = Field(default=None, max_length=100)
    is_private: Optional[bool] = Field(default=None)

class RepositoryResponse(BaseModel):
    id: str
    project_id: str
    project_name: str
    name: str
    description: str
    git_url: Optional[str] = None
    git_provider: Optional[str] = None
    default_branch: str
    is_private: bool
    created_by: int
    created_by_username: str
    created_at: str
    updated_at: str
    pull_requests_count: int = 0
    open_prs_count: int = 0

class PullRequestCreate(BaseModel):
    repository_id: str = Field(..., description="Repository UUID")
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    source_branch: str = Field(..., min_length=1, max_length=200)
    target_branch: str = Field(..., min_length=1, max_length=200)
    external_id: Optional[str] = Field(default=None, max_length=100)
    external_url: Optional[str] = Field(default=None, max_length=500)

class PullRequestUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Optional[str] = Field(default=None, pattern="^(draft|open|review_requested|changes_requested|approved|merged|closed)$")
    merge_status: Optional[str] = Field(default=None, pattern="^(mergeable|conflicted|unknown)$")

class PullRequestResponse(BaseModel):
    id: str
    repository_id: str
    repository_name: str
    pr_number: int
    title: str
    description: str
    author_id: int
    author_username: str
    source_branch: str
    target_branch: str
    status: str
    merge_status: str
    commits_count: int
    files_changed_count: int
    additions: int
    deletions: int
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    created_at: str
    updated_at: str
    merged_at: Optional[str] = None
    closed_at: Optional[str] = None
    reviews_count: int = 0
    pending_reviews_count: int = 0

class PullRequestFileResponse(BaseModel):
    id: str
    pull_request_id: str
    file_path: str
    file_status: str
    old_file_path: Optional[str] = None
    additions: int
    deletions: int
    changes: int
    patch_content: Optional[str] = None
    comments_count: int = 0

class CodeReviewCreate(BaseModel):
    pull_request_id: str = Field(..., description="Pull Request UUID")
    reviewer_ids: List[int] = Field(..., min_items=1, description="List of reviewer user IDs")
    summary_comment: Optional[str] = Field(default=None, max_length=2000)
    status: str = Field(default="pending", pattern="^(pending|approved|changes_requested|commented)$")

class CodeReviewUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(pending|approved|changes_requested|commented)$")
    summary_comment: Optional[str] = Field(default=None, max_length=2000)

class CodeReviewResponse(BaseModel):
    id: str
    pull_request_id: str
    reviewer_id: int
    reviewer_username: str
    status: str
    summary_comment: Optional[str] = None
    submitted_at: Optional[str] = None
    created_at: str
    updated_at: str
    comments_count: int = 0

class CodeCommentCreate(BaseModel):
    review_id: str = Field(..., description="Code Review UUID")
    file_id: Optional[str] = Field(default=None, description="Pull Request File UUID")
    line_number: Optional[int] = Field(default=None, ge=1)
    line_type: Optional[str] = Field(default=None, pattern="^(old|new)$")
    comment_text: str = Field(..., min_length=1, max_length=2000)
    parent_comment_id: Optional[str] = Field(default=None, description="Parent Comment UUID for replies")

class CodeCommentUpdate(BaseModel):
    comment_text: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    is_resolved: Optional[bool] = Field(default=None)

class CodeCommentResponse(BaseModel):
    id: str
    review_id: str
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    line_type: Optional[str] = None
    comment_text: str
    is_resolved: bool
    parent_comment_id: Optional[str] = None
    author_id: int
    author_username: str
    created_at: str
    updated_at: str
    replies_count: int = 0

class ReviewRequestCreate(BaseModel):
    pull_request_id: str = Field(..., description="Pull Request UUID")
    requested_reviewer_ids: List[int] = Field(..., min_items=1, description="List of reviewer user IDs")
    is_required: bool = Field(default=False)

class ReviewRequestResponse(BaseModel):
    id: str
    pull_request_id: str
    requested_reviewer_id: int
    requested_reviewer_username: str
    requested_by_id: int
    requested_by_username: str
    is_required: bool
    status: str
    requested_at: str
    responded_at: Optional[str] = None

# ========== Audit Management Models ==========

class AuditCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    audit_type: str = Field(..., pattern="^(internal|external|supplier|regulatory)$")
    scope: str = Field(..., min_length=1)
    planned_start_date: str = Field(..., description="Date in YYYY-MM-DD format")
    planned_end_date: str = Field(..., description="Date in YYYY-MM-DD format")
    lead_auditor: int = Field(..., description="User ID of lead auditor")
    audit_team: List[int] = Field(default=[], description="List of user IDs for audit team")
    auditee_department: str = Field(..., min_length=1, max_length=100)
    compliance_standard: str = Field(default="ISO 13485:2016", max_length=100)
    project_id: str = Field(..., description="Project UUID")

class AuditUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    audit_type: Optional[str] = Field(default=None, pattern="^(internal|external|supplier|regulatory)$")
    scope: Optional[str] = Field(default=None, min_length=1)
    planned_start_date: Optional[str] = Field(default=None)
    planned_end_date: Optional[str] = Field(default=None)
    actual_start_date: Optional[str] = Field(default=None)
    actual_end_date: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None, pattern="^(planned|in_progress|completed|cancelled)$")
    lead_auditor: Optional[int] = Field(default=None)
    audit_team: Optional[List[int]] = Field(default=None)
    auditee_department: Optional[str] = Field(default=None, max_length=100)
    overall_rating: Optional[str] = Field(default=None, pattern="^(compliant|minor_nc|major_nc|critical_nc)$")

class AuditResponse(BaseModel):
    id: str
    audit_number: str
    title: str
    audit_type: str
    scope: str
    planned_start_date: str
    planned_end_date: str
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    status: str
    lead_auditor: int
    lead_auditor_username: str
    audit_team: List[int]
    audit_team_usernames: List[str]
    auditee_department: str
    compliance_standard: str
    overall_rating: Optional[str] = None
    project_id: str
    project_name: str
    created_by: int
    created_by_username: str
    created_at: str
    updated_at: str
    findings_count: int = 0
    open_findings_count: int = 0

class FindingCreate(BaseModel):
    audit_id: str = Field(..., description="Audit UUID")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(critical|major|minor|observation)$")
    category: str = Field(..., min_length=1, max_length=100)
    clause_reference: Optional[str] = Field(default=None, max_length=100)
    evidence: Optional[str] = Field(default=None)
    root_cause: Optional[str] = Field(default=None)
    immediate_action: Optional[str] = Field(default=None)
    identified_date: str = Field(..., description="Date in YYYY-MM-DD format")
    due_date: Optional[str] = Field(default=None)

class FindingUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1)
    severity: Optional[str] = Field(default=None, pattern="^(critical|major|minor|observation)$")
    category: Optional[str] = Field(default=None, max_length=100)
    clause_reference: Optional[str] = Field(default=None, max_length=100)
    evidence: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None, pattern="^(open|closed|verified)$")
    root_cause: Optional[str] = Field(default=None)
    immediate_action: Optional[str] = Field(default=None)
    due_date: Optional[str] = Field(default=None)
    closed_date: Optional[str] = Field(default=None)
    verified_by: Optional[int] = Field(default=None)
    verified_date: Optional[str] = Field(default=None)

class FindingResponse(BaseModel):
    id: str
    audit_id: str
    finding_number: str
    title: str
    description: str
    severity: str
    category: str
    clause_reference: Optional[str] = None
    evidence: Optional[str] = None
    status: str
    root_cause: Optional[str] = None
    immediate_action: Optional[str] = None
    identified_by: int
    identified_by_username: str
    identified_date: str
    due_date: Optional[str] = None
    closed_date: Optional[str] = None
    verified_by: Optional[int] = None
    verified_by_username: Optional[str] = None
    verified_date: Optional[str] = None
    created_at: str
    updated_at: str
    corrective_actions_count: int = 0

class CorrectiveActionCreate(BaseModel):
    finding_id: str = Field(..., description="Finding UUID")
    description: str = Field(..., min_length=1)
    responsible_person: int = Field(..., description="User ID of responsible person")
    target_date: str = Field(..., description="Date in YYYY-MM-DD format")
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    resources_required: Optional[str] = Field(default=None)
    success_criteria: Optional[str] = Field(default=None)

class CorrectiveActionUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1)
    responsible_person: Optional[int] = Field(default=None)
    target_date: Optional[str] = Field(default=None)
    actual_completion_date: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None, pattern="^(assigned|in_progress|completed|overdue)$")
    effectiveness_check: Optional[str] = Field(default=None)
    effectiveness_verified_by: Optional[int] = Field(default=None)
    effectiveness_verified_date: Optional[str] = Field(default=None)
    priority: Optional[str] = Field(default=None, pattern="^(low|medium|high|critical)$")
    resources_required: Optional[str] = Field(default=None)
    success_criteria: Optional[str] = Field(default=None)

class CorrectiveActionResponse(BaseModel):
    id: str
    finding_id: str
    action_number: str
    description: str
    responsible_person: int
    responsible_person_username: str
    target_date: str
    actual_completion_date: Optional[str] = None
    status: str
    effectiveness_check: Optional[str] = None
    effectiveness_verified_by: Optional[int] = None
    effectiveness_verified_by_username: Optional[str] = None
    effectiveness_verified_date: Optional[str] = None
    priority: str
    resources_required: Optional[str] = None
    success_criteria: Optional[str] = None
    created_at: str
    updated_at: str

# ========== Training Models ==========

class TrainingLearningRequest(BaseModel):
    topics: List[str] = Field(..., description="Topics/document types to generate learning content from")

class TrainingAssessmentRequest(BaseModel):
    topics: List[str] = Field(..., description="Topics/document types to generate questions from")
    num_questions: int = Field(default=20, ge=1, le=50, description="Number of questions to generate")

class AssessmentQuestion(BaseModel):
    id: str
    question: str
    correct_answer: bool

class AssessmentSubmissionRequest(BaseModel):
    question_ids: List[str] = Field(..., description="List of question IDs")
    answers: List[bool] = Field(..., description="User's True/False answers")

class AssessmentResult(BaseModel):
    score: int
    total_questions: int
    percentage: float
    passed: bool
    correct_answers: List[bool]
    questions_with_answers: List[Dict[str, Any]]

class TrainingRecord(BaseModel):
    user_id: int
    document_type: str
    assessment_date: str
    score: int
    total_questions: int
    percentage: float
    passed: bool

class UserTrainingResults(BaseModel):
    user_id: int
    total_assessments: int
    average_score: float
    assessments: List[TrainingRecord]

