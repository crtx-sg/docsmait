# backend/app/db_models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, BigInteger, ForeignKey, JSON, UniqueConstraint, Index, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database_config import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_super_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    created_projects = relationship("Project", back_populates="creator")
    project_memberships = relationship("ProjectMember", back_populates="user", foreign_keys="ProjectMember.user_id")
    added_memberships = relationship("ProjectMember", back_populates="added_by_user", foreign_keys="ProjectMember.added_by")
    created_documents = relationship("Document", back_populates="creator", foreign_keys="Document.created_by")
    reviewed_documents = relationship("Document", back_populates="reviewer_user", foreign_keys="Document.reviewed_by")
    created_templates = relationship("Template", back_populates="creator", foreign_keys="Template.created_by")
    approved_templates = relationship("Template", back_populates="approver_user", foreign_keys="Template.approved_by")
    document_reviews = relationship("DocumentReview", back_populates="reviewer")
    training_records = relationship("TrainingRecord", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="created_projects")
    members = relationship("ProjectMember", back_populates="project")
    resources = relationship("ProjectResource", back_populates="project")
    documents = relationship("Document", back_populates="project")

class ProjectMember(Base):
    __tablename__ = "project_members"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships", foreign_keys=[user_id])
    added_by_user = relationship("User", back_populates="added_memberships", foreign_keys=[added_by])
    
    # Constraints
    __table_args__ = (UniqueConstraint('project_id', 'user_id', name='unique_project_user'),)

class ProjectResource(Base):
    __tablename__ = "project_resources"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    resource_type = Column(String(50), nullable=False)
    content = Column(Text)
    file_path = Column(String(500))
    file_size_bytes = Column(Integer)
    content_type = Column(String(100))
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="resources")

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    document_type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)  # Store as JSON array
    version = Column(String(10), default="1.0")
    status = Column(String(20), default="draft", index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Relationships
    creator = relationship("User", back_populates="created_templates", foreign_keys=[created_by])
    approver_user = relationship("User", back_populates="approved_templates", foreign_keys=[approved_by])
    template_approvals = relationship("TemplateApproval", back_populates="template")
    documents = relationship("Document", back_populates="template")
    
    # Constraints
    __table_args__ = (UniqueConstraint('name', name='unique_template_name'),)

class TemplateApproval(Base):
    __tablename__ = "template_approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(36), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending")
    message = Column(Text, default="")
    response_comments = Column(Text)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True))
    
    # Relationships
    template = relationship("Template", back_populates="template_approvals")
    
    # Constraints
    __table_args__ = (UniqueConstraint('template_id', 'approver_id', name='unique_template_approver'),)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    name = Column(String(200), nullable=False)
    document_type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="draft", index=True)  # Keep for backward compatibility
    
    # New simplified state management
    document_state = Column(String(20), default="draft")  # draft, review_request, needs_update, approved
    review_state = Column(String(20), default="none")     # none, under_review
    current_reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Single reviewer at a time
    
    template_id = Column(String(36), ForeignKey("templates.id"))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    current_revision = Column(Integer, default=1)
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    template = relationship("Template", back_populates="documents")
    creator = relationship("User", back_populates="created_documents", foreign_keys=[created_by])
    reviewer_user = relationship("User", back_populates="reviewed_documents", foreign_keys=[reviewed_by])
    current_reviewer = relationship("User", foreign_keys=[current_reviewer_id])  # New simplified reviewer
    
    # New simplified comment system
    comments = relationship("DocumentComment", back_populates="document", cascade="all, delete-orphan")
    
    # Keep old complex system for backward compatibility during migration
    revisions = relationship("DocumentRevision", back_populates="document", cascade="all, delete-orphan")
    reviewers = relationship("DocumentReviewer", back_populates="document", cascade="all, delete-orphan")
    reviews = relationship("DocumentReview", back_populates="document", cascade="all, delete-orphan")

class DocumentRevision(Base):
    __tablename__ = "document_revisions"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    comment = Column(Text, default="")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="revisions")
    reviewer_assignments = relationship("DocumentReviewer", back_populates="revision")
    reviews = relationship("DocumentReview", back_populates="revision")
    
    # Constraints
    __table_args__ = (UniqueConstraint('document_id', 'revision_number', name='unique_document_revision'),)

class DocumentReviewer(Base):
    __tablename__ = "document_reviewers"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    revision_id = Column(String(36), ForeignKey("document_revisions.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending")
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="reviewers")
    revision = relationship("DocumentRevision", back_populates="reviewer_assignments")
    
    # Constraints
    __table_args__ = (UniqueConstraint('document_id', 'revision_id', 'reviewer_id', name='unique_document_reviewer'),)

class DocumentReview(Base):
    __tablename__ = "document_reviews"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    revision_id = Column(String(36), ForeignKey("document_revisions.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved = Column(Boolean, nullable=False)
    comments = Column(Text, default="")
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="reviews")
    revision = relationship("DocumentRevision", back_populates="reviews")
    reviewer = relationship("User", back_populates="document_reviews")

# Knowledge Base Models for metadata (vectors stored in Qdrant)
class KBCollection(Base):
    __tablename__ = "kb_collections"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    created_by = Column(String(100))  # Can be user ID or username
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    document_count = Column(Integer, default=0)
    total_size_bytes = Column(BigInteger, default=0)
    tags = Column(Text)  # JSON string of tags
    is_default = Column(Boolean, default=False)
    
    # Relationships
    documents = relationship("KBDocument", back_populates="collection")

class KBDocument(Base):
    __tablename__ = "kb_documents"
    
    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    content_type = Column(String(100))
    size_bytes = Column(BigInteger)
    collection_name = Column(String(200), ForeignKey("kb_collections.name"))
    chunk_count = Column(Integer)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="processing")
    
    # Relationships
    collection = relationship("KBCollection", back_populates="documents")
    tags = relationship("KBDocumentTag", back_populates="document")

class KBQuery(Base):
    __tablename__ = "kb_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    collection_name = Column(String(200))
    response_time_ms = Column(Integer)
    query_date = Column(Date, server_default=func.current_date())
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class KBConfig(Base):
    __tablename__ = "kb_config"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class KBDocumentTag(Base):
    __tablename__ = "kb_document_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("kb_documents.id"), nullable=False)
    tag_name = Column(String(100), nullable=False)
    tag_value = Column(Text)
    
    # Relationships
    document = relationship("KBDocument", back_populates="tags")

# Audit Management Models
class Audit(Base):
    __tablename__ = "audits"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    audit_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    audit_type = Column(String(50), nullable=False, index=True)  # internal, external, supplier, regulatory
    scope = Column(Text, nullable=False)
    planned_start_date = Column(Date, nullable=False)
    planned_end_date = Column(Date, nullable=False)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)
    status = Column(String(30), default="planned", index=True)  # planned, in_progress, completed, cancelled
    lead_auditor = Column(Integer, ForeignKey("users.id"), nullable=False)
    audit_team = Column(JSON, default=list)  # List of user IDs
    auditee_department = Column(String(100), nullable=False)
    compliance_standard = Column(String(100), default="ISO 13485:2016")
    overall_rating = Column(String(20))  # compliant, minor_nc, major_nc, critical_nc
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    lead_auditor_user = relationship("User", foreign_keys=[lead_auditor])
    creator = relationship("User", foreign_keys=[created_by])
    findings = relationship("Finding", back_populates="audit")

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    audit_id = Column(String(36), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False)
    finding_number = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, index=True)  # critical, major, minor, observation
    category = Column(String(100), nullable=False)
    clause_reference = Column(String(100))  # ISO clause reference
    evidence = Column(Text)
    status = Column(String(30), default="open", index=True)  # open, closed, verified
    root_cause = Column(Text)
    immediate_action = Column(Text)
    identified_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    identified_date = Column(Date, nullable=False)
    due_date = Column(Date)
    closed_date = Column(Date)
    verified_by = Column(Integer, ForeignKey("users.id"))
    verified_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    audit = relationship("Audit", back_populates="findings")
    identifier = relationship("User", foreign_keys=[identified_by])
    verifier = relationship("User", foreign_keys=[verified_by])
    corrective_actions = relationship("CorrectiveAction", back_populates="finding")
    
    # Constraints
    __table_args__ = (UniqueConstraint('audit_id', 'finding_number', name='unique_audit_finding'),)

class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    action_number = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    responsible_person = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_date = Column(Date, nullable=False)
    actual_completion_date = Column(Date)
    status = Column(String(30), default="assigned", index=True)  # assigned, in_progress, completed, overdue
    effectiveness_check = Column(Text)
    effectiveness_verified_by = Column(Integer, ForeignKey("users.id"))
    effectiveness_verified_date = Column(Date)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    resources_required = Column(Text)
    success_criteria = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    finding = relationship("Finding", back_populates="corrective_actions")
    responsible_user = relationship("User", foreign_keys=[responsible_person])
    verifier = relationship("User", foreign_keys=[effectiveness_verified_by])
    
    # Constraints
    __table_args__ = (UniqueConstraint('finding_id', 'action_number', name='unique_finding_action'),)

# Code Review Management Models
class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    git_url = Column(String(500))  # Git repository URL
    git_provider = Column(String(50))  # github, gitlab, bitbucket, etc.
    default_branch = Column(String(100), default="main")
    is_private = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    pull_requests = relationship("PullRequest", back_populates="repository")
    
    # Constraints
    __table_args__ = (UniqueConstraint('project_id', 'name', name='unique_project_repository'),)

class PullRequest(Base):
    __tablename__ = "pull_requests"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    pr_number = Column(Integer, nullable=False)  # Sequential PR number within repo
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_branch = Column(String(200), nullable=False)
    target_branch = Column(String(200), nullable=False)
    status = Column(String(30), default="open", index=True)  # draft, open, review_requested, changes_requested, approved, merged, closed
    merge_status = Column(String(30), default="mergeable")  # mergeable, conflicted, unknown
    commits_count = Column(Integer, default=0)
    files_changed_count = Column(Integer, default=0)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    external_id = Column(String(100))  # External PR ID from Git provider
    external_url = Column(String(500))  # URL to PR in external system
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    merged_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    
    # Relationships
    repository = relationship("Repository", back_populates="pull_requests")
    author = relationship("User", foreign_keys=[author_id])
    reviews = relationship("CodeReview", back_populates="pull_request")
    file_changes = relationship("PullRequestFile", back_populates="pull_request")
    
    # Constraints
    __table_args__ = (UniqueConstraint('repository_id', 'pr_number', name='unique_repo_pr_number'),)

class PullRequestFile(Base):
    __tablename__ = "pull_request_files"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    pull_request_id = Column(String(36), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_status = Column(String(20), nullable=False)  # added, modified, deleted, renamed
    old_file_path = Column(String(1000))  # For renamed files
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    changes = Column(Integer, default=0)
    patch_content = Column(Text)  # Git diff content
    
    # Relationships
    pull_request = relationship("PullRequest", back_populates="file_changes")
    comments = relationship("CodeComment", back_populates="file")

class CodeReview(Base):
    __tablename__ = "code_reviews"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    pull_request_id = Column(String(36), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(30), default="pending", index=True)  # pending, approved, changes_requested, commented
    summary_comment = Column(Text)
    submitted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    pull_request = relationship("PullRequest", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    comments = relationship("CodeComment", back_populates="review")
    
    # Constraints
    __table_args__ = (UniqueConstraint('pull_request_id', 'reviewer_id', name='unique_pr_reviewer'),)

class CodeComment(Base):
    __tablename__ = "code_comments"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    review_id = Column(String(36), ForeignKey("code_reviews.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(String(36), ForeignKey("pull_request_files.id", ondelete="CASCADE"))
    line_number = Column(Integer)  # Line number in the file (null for general comments)
    line_type = Column(String(10))  # old, new (for diff context)
    comment_text = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    parent_comment_id = Column(String(36), ForeignKey("code_comments.id"))  # For threaded comments
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    review = relationship("CodeReview", back_populates="comments")
    file = relationship("PullRequestFile", back_populates="comments")
    parent_comment = relationship("CodeComment", remote_side=[id])
    replies = relationship("CodeComment", remote_side=[parent_comment_id], overlaps="parent_comment")

class ReviewRequest(Base):
    __tablename__ = "review_requests"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    pull_request_id = Column(String(36), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    requested_reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_required = Column(Boolean, default=False)  # Required vs optional reviewer
    status = Column(String(30), default="pending")  # pending, accepted, declined
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True))
    
    # Relationships
    pull_request = relationship("PullRequest")
    requested_reviewer = relationship("User", foreign_keys=[requested_reviewer_id])
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    
    # Constraints
    __table_args__ = (UniqueConstraint('pull_request_id', 'requested_reviewer_id', name='unique_pr_review_request'),)

class TraceabilityMatrix(Base):
    __tablename__ = "traceability_matrix"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Source and target entities
    source_type = Column(String(30), nullable=False)  # requirement, hazard, safety_measure, verification
    source_id = Column(String(36), nullable=False)
    target_type = Column(String(30), nullable=False)
    target_id = Column(String(36), nullable=False)
    
    # Relationship details
    relationship_type = Column(String(30), nullable=False)  # derives, verifies, mitigates, implements, traces_to
    relationship_description = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    verification_date = Column(Date)
    
    # Audit trail
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('source_type', 'source_id', 'target_type', 'target_id', name='unique_traceability_link'),
        Index('idx_source_entity', 'source_type', 'source_id'),
        Index('idx_target_entity', 'target_type', 'target_id')
    )

class ComplianceStandard(Base):
    __tablename__ = "compliance_standards"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Standard details
    standard_name = Column(String(100), nullable=False)  # ISO 26262, IEC 61508, DO-178C, etc.
    standard_version = Column(String(20))
    domain = Column(String(20), nullable=False)  # automotive, medical, industrial, aviation, general
    
    # Applicability
    applicable_phases = Column(Text)  # JSON array of lifecycle phases
    mandatory_requirements = Column(Text)  # JSON array of requirement IDs
    recommended_practices = Column(Text)  # JSON array of practices
    
    # Compliance tracking
    overall_compliance_status = Column(String(20), default="in_progress")  # compliant, non_compliant, in_progress, not_applicable
    last_assessment_date = Column(Date)
    next_assessment_date = Column(Date)
    compliance_notes = Column(Text)
    
    # Audit trail
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Constraints
    __table_args__ = (UniqueConstraint('project_id', 'standard_name', 'standard_version', name='unique_project_standard'),)

# Training Records
class DocumentComment(Base):
    __tablename__ = "document_comments"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    comment_type = Column(String(20), nullable=False)  # review_request, needs_update, approved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="comments")
    user = relationship("User")

class TrainingRecord(Base):
    __tablename__ = "training_records"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_type = Column(String(100), nullable=False)
    assessment_date = Column(Date, nullable=False)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    percentage = Column(Integer, nullable=False)  # Store as integer (0-100)
    passed = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="training_records")
    
    # Index for efficient queries
    __table_args__ = (Index('idx_training_user_date', 'user_id', 'assessment_date'),)

class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)  # Store as JSON string for complex values
    category = Column(String(50), nullable=False, index=True)  # e.g., 'smtp', 'general', 'security'
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    updater = relationship("User")


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., 'create', 'update', 'delete', 'approve'
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., 'document', 'project', 'user'
    resource_id = Column(String(100), nullable=True, index=True)  # ID of the affected resource
    resource_name = Column(String(255), nullable=True)  # Human-readable name/title
    description = Column(Text, nullable=True)  # Detailed description of the activity
    activity_metadata = Column(Text, nullable=True)  # JSON string with additional context
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)  # Associate with project if applicable
    ip_address = Column(String(45), nullable=True)  # User's IP address
    user_agent = Column(String(500), nullable=True)  # Browser/client information
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", backref="activity_logs")
    project = relationship("Project", backref="activity_logs")

# ========== Records Management Models ==========

class Supplier(Base):
    __tablename__ = "suppliers"
    
    supplier_id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(255), nullable=False, unique=True)
    address = Column(Text, nullable=True)
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    approval_status = Column(SQLEnum('Approved', 'Conditional', 'Rejected', 'Pending', name='supplier_approval_status'), nullable=True)
    risk_level = Column(SQLEnum('Low', 'Medium', 'High', name='supplier_risk_level'), nullable=True)
    certification_status = Column(Text, nullable=True)
    last_audit_date = Column(Date, nullable=True)
    next_audit_date = Column(Date, nullable=True)
    performance_rating = Column(Numeric(5, 2), nullable=True)
    on_time_delivery_rate = Column(Numeric(5, 2), nullable=True)
    quality_rating = Column(Numeric(5, 2), nullable=True)
    contract_details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    parts = relationship("PartsInventory", back_populates="supplier")

class PartsInventory(Base):
    __tablename__ = "parts_inventory"
    
    part_id = Column(Integer, primary_key=True, index=True)
    part_number = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    udi = Column(String(255), nullable=True)
    lot_number = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=True)
    quantity_in_stock = Column(Integer, nullable=True)
    minimum_stock_level = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    expiration_date = Column(Date, nullable=True)
    status = Column(SQLEnum('In Stock', 'Quarantined', 'Expired', 'Disposed', name='inventory_status'), nullable=True)
    received_date = Column(Date, nullable=True)
    cost = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="parts")

class LabEquipmentCalibration(Base):
    __tablename__ = "lab_equipment_calibration"
    
    equipment_id = Column(Integer, primary_key=True, index=True)
    equipment_name = Column(String(255), nullable=False)
    serial_number = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    calibration_frequency = Column(String(100), nullable=True)
    last_calibration_date = Column(Date, nullable=True)
    next_calibration_date = Column(Date, nullable=True)
    calibration_status = Column(SQLEnum('Calibrated', 'Due', 'Overdue', 'Out of Service', name='calibration_status'), nullable=True)
    technician = Column(String(255), nullable=True)
    standards_used = Column(Text, nullable=True)
    results = Column(Text, nullable=True)
    adjustment_made = Column(Boolean, default=False)
    compliance_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class CustomerComplaint(Base):
    __tablename__ = "customer_complaints"
    
    complaint_id = Column(Integer, primary_key=True, index=True)
    received_date = Column(Date, nullable=False)
    complainant_name = Column(String(255), nullable=True)
    complainant_contact = Column(String(255), nullable=True)
    product_id = Column(String(255), nullable=True)
    lot_number = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    complaint_description = Column(Text, nullable=False)
    investigation_details = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    response_date = Column(Date, nullable=True)
    mdr_reportable = Column(Boolean, default=False)
    status = Column(SQLEnum('Open', 'Under Investigation', 'Closed', name='complaint_status'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class NonConformance(Base):
    __tablename__ = "non_conformances"
    
    nc_id = Column(Integer, primary_key=True, index=True)
    detection_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    product_process_involved = Column(String(255), nullable=True)
    severity = Column(SQLEnum('Minor', 'Major', 'Critical', name='nc_severity'), nullable=True)
    risk_level = Column(SQLEnum('Low', 'Medium', 'High', name='nc_risk_level'), nullable=True)
    root_cause = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    preventive_action = Column(Text, nullable=True)
    responsible_person = Column(String(255), nullable=True)
    disposition = Column(SQLEnum('Use As Is', 'Rework', 'Scrap', 'Return', name='nc_disposition'), nullable=True)
    status = Column(SQLEnum('Open', 'In Progress', 'Closed', name='nc_status'), nullable=True)
    closure_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SystemRequirement(Base):
    __tablename__ = "system_requirements"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    req_id = Column(String(100), nullable=False)  # User-defined requirement ID (REQ-001, etc.)
    req_title = Column(String(500), nullable=False)
    req_description = Column(Text, nullable=False)
    req_type = Column(String(50), nullable=False, index=True)  # functional, non_functional, safety, security, performance, clinical, regulatory
    req_priority = Column(String(20), nullable=False, index=True)  # critical, high, medium, low
    req_status = Column(String(20), default="draft", index=True)  # draft, approved, implemented, verified, obsolete
    req_version = Column(String(20), default="1.0")
    req_source = Column(String(255))  # Stakeholder, regulation, or standard
    acceptance_criteria = Column(Text)
    rationale = Column(Text)
    assumptions = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints
    __table_args__ = (UniqueConstraint('project_id', 'req_id', name='unique_project_requirement_id'),)

class SystemHazard(Base):
    __tablename__ = "system_hazards"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    hazard_id = Column(String(100), nullable=False)  # User-defined hazard ID (HAZ-001, etc.)
    hazard_title = Column(String(500), nullable=False)
    hazard_description = Column(Text, nullable=False)
    hazard_category = Column(String(50), nullable=False, index=True)  # safety, security, operational, environmental, clinical
    severity_level = Column(String(50), nullable=False, index=True)  # catastrophic, critical, marginal, negligible
    likelihood = Column(String(50), nullable=False, index=True)  # frequent, probable, occasional, remote, improbable
    risk_rating = Column(String(20), nullable=False, index=True)  # high, medium, low
    triggering_conditions = Column(Text)
    operational_context = Column(String(255))
    use_error_potential = Column(Boolean, default=False)
    current_controls = Column(Text)
    affected_stakeholders = Column(JSON, default=list)  # JSON array of stakeholders
    asil_level = Column(String(5))  # A, B, C, D, QM
    sil_level = Column(Integer)  # 1, 2, 3, 4
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints
    __table_args__ = (UniqueConstraint('project_id', 'hazard_id', name='unique_project_hazard_id'),)

class FMEAAnalysis(Base):
    __tablename__ = "fmea_analyses"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    fmea_id = Column(String(100), nullable=False)  # User-defined FMEA ID (FMEA-001, etc.)
    fmea_type = Column(String(50), nullable=False, index=True)  # design_fmea, process_fmea, system_fmea, software_fmea
    analysis_level = Column(String(50), nullable=False, index=True)  # component, assembly, subsystem, system
    hierarchy_level = Column(Integer, nullable=False)
    element_id = Column(String(100), nullable=False)
    element_function = Column(String(500), nullable=False)
    performance_standards = Column(Text)
    fmea_team = Column(JSON, default=list)  # JSON array of team members
    analysis_date = Column(Date)
    review_status = Column(String(20), default="draft", index=True)  # draft, under_review, approved, superseded
    failure_modes = Column(JSON, default=list)  # JSON array of failure mode objects
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints
    __table_args__ = (UniqueConstraint('project_id', 'fmea_id', name='unique_project_fmea_id'),)

class DesignArtifact(Base):
    __tablename__ = "design_artifacts"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    design_id = Column(String(100), nullable=False)  # User-defined design ID (DES-001, etc.)
    design_title = Column(String(500), nullable=False)
    design_type = Column(String(50), nullable=False, index=True)  # specification, architecture, interface, detailed_design
    design_description = Column(Text, nullable=False)
    implementation_approach = Column(Text)
    architecture_diagrams = Column(JSON, default=list)  # JSON array of diagram references
    interface_definitions = Column(JSON, default=list)  # JSON array of interface specs
    design_patterns = Column(JSON, default=list)  # JSON array of design patterns
    technology_stack = Column(JSON, default=list)  # JSON array of technologies
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints
    __table_args__ = (UniqueConstraint('project_id', 'design_id', name='unique_project_design_id'),)

class TestArtifact(Base):
    __tablename__ = "test_artifacts"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(String(100), nullable=False)  # User-defined test ID (TEST-001, etc.)
    test_title = Column(String(500), nullable=False)
    test_type = Column(String(50), nullable=False, index=True)  # unit, integration, system, safety, performance, security, clinical, usability, biocompatibility
    test_objective = Column(Text, nullable=False)
    acceptance_criteria = Column(Text, nullable=False)
    test_environment = Column(String(500))
    test_execution = Column(JSON)  # JSON object with execution details
    coverage_metrics = Column(JSON)  # JSON object with coverage data
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints
    __table_args__ = (UniqueConstraint('project_id', 'test_id', name='unique_project_test_id'),)

class ComplianceRecord(Base):
    __tablename__ = "compliance_records"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    compliance_id = Column(String(100), nullable=False)  # User-defined compliance ID
    standard_name = Column(String(100), nullable=False)  # ISO 13485, FDA 510k, etc.
    standard_version = Column(String(20))
    compliance_status = Column(String(20), default="in_progress", index=True)  # compliant, non_compliant, in_progress, not_applicable
    assessment_date = Column(Date)
    next_review_date = Column(Date)
    findings = Column(JSON, default=list)  # JSON array of findings
    gaps = Column(JSON, default=list)  # JSON array of compliance gaps
    action_items = Column(JSON, default=list)  # JSON array of action items
    evidence_documents = Column(JSON, default=list)  # JSON array of document references
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints
    __table_args__ = (UniqueConstraint('project_id', 'compliance_id', name='unique_project_compliance_id'),)

class PostMarketRecord(Base):
    __tablename__ = "post_market_records"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID as string
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    record_id = Column(String(100), nullable=False)  # User-defined record ID
    record_type = Column(String(50), nullable=False, index=True)  # surveillance, complaint, adverse_event, recall, clinical_evaluation
    incident_date = Column(Date)
    reported_date = Column(Date)
    severity_level = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    description = Column(Text, nullable=False)
    root_cause_analysis = Column(Text)
    corrective_actions = Column(Text)
    preventive_actions = Column(Text)
    regulatory_notifications = Column(JSON, default=list)  # JSON array of notifications
    follow_up_actions = Column(JSON, default=list)  # JSON array of follow-up items
    closure_date = Column(Date)
    status = Column(String(20), default="open", index=True)  # open, under_investigation, resolved, closed
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints
    __table_args__ = (UniqueConstraint('project_id', 'record_id', name='unique_project_postmarket_id'),)