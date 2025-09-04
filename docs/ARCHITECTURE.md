# Docsmait - System Architecture Documentation

## 1. Architecture Overview

Docsmait is built using a modern, scalable microservices-inspired architecture with clear separation of concerns between the frontend, backend API, and supporting services. The system follows a layered architecture pattern with distinct presentation, business logic, data access, and infrastructure layers.

### 1.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  Streamlit Frontend (Python)                                   │
│  ├── Authentication & Session Management                       │
│  ├── Page Components (Projects, Documents, Audits, etc.)      │
│  ├── User Interface Components                                │
│  └── Client-side State Management                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP/REST API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Backend (Python)                                      │
│  ├── REST API Endpoints                                       │
│  ├── Request/Response Models (Pydantic)                       │
│  ├── Authentication & Authorization (JWT)                     │
│  ├── Input Validation & Serialization                         │
│  └── Error Handling & Logging                                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  Service Classes                                               │
│  ├── User Service          ├── AI Service                     │
│  ├── Project Service       ├── Email Service                  │
│  ├── Document Service      ├── Settings Service               │
│  ├── Template Service      ├── KB Service                     │
│  ├── Audit Service         └── Code Review Service            │
│  └── Workflow & Business Rules Engine                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  SQLAlchemy ORM                                               │
│  ├── Database Models (db_models.py)                          │
│  ├── Repository Pattern Implementation                        │
│  ├── Database Connection Management                           │
│  └── Transaction Management                                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   PostgreSQL    │  │     Qdrant      │  │     Ollama      │ │
│  │   (Primary DB)  │  │  (Vector DB)    │  │  (AI Models)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   File System  │  │   SMTP Server   │  │   Log Files     │ │
│  │  (Documents)    │  │  (Email Notif.) │  │   (Audit)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Component Architecture

### 2.1 Frontend Architecture (Streamlit)

#### 2.1.1 Structure and Components
```
frontend/
├── app.py                         # Main application entry point
├── auth_utils.py                  # Authentication utilities
├── config.py                     # Frontend configuration
└── pages/                        # Page components
    ├── Auth.py                   # Authentication page
    ├── _Projects.py              # Project management
    ├── Documents.py              # Document management
    ├── Templates.py              # Template management
    ├── _Knowledge_Base.py        # Knowledge base interface
    ├── Reviews.py                # Review workflows
    ├── Audit.py                  # Audit management
    ├── Code.py                   # Code review management
    ├── DesignRecord.py           # Design record management
    ├── Records.py                # ISO 13485 records management
    ├── Records_Management.py     # Records management module
    ├── Activity_Logs.py          # Activity log tracking
    ├── AISettings.py             # AI configuration
    ├── Settings.py               # System settings
    ├── Training.py               # Training management system
    └── Help.py                   # Help and documentation
```

#### 2.1.2 Key Features
- **Session-based Authentication**: JWT token management with automatic refresh
- **Responsive UI**: Mobile-friendly interface using Streamlit components
- **Real-time Updates**: Dynamic content loading and state management
- **Role-based Views**: UI components adapt to user permissions
- **Error Handling**: User-friendly error messages and validation feedback
- **Interactive Tables**: st.dataframe implementation with single-row selection
- **Comprehensive Forms**: Full editing capability for all data fields
- **Export Capabilities**: Multiple format export including CSV and Markdown
- **Training System**: AI-powered learning content generation and assessment
- **Password Management**: Admin-level password reset with security controls
- **Knowledge Base Integration**: Intelligent updates and project summaries

#### 2.1.3 State Management
```python
# Session state management pattern
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.token = None

# User context preservation across pages
def get_current_user():
    return st.session_state.user if st.session_state.authenticated else None
```

### 2.2 Backend Architecture (FastAPI)

#### 2.2.1 API Layer Structure
```
backend/app/
├── main.py                     # FastAPI application and routes
├── auth.py                    # JWT authentication
├── models.py                  # Pydantic request/response models
├── db_models.py               # SQLAlchemy database models
├── database_config.py         # Database connection config
├── database_service.py        # Database service layer
├── activity_log_service.py    # Activity logging service
├── records_service.py         # Records management service
├── project_export_service.py  # Project export functionality
├── user_service.py           # User management service
├── projects_service_pg.py    # Project management service
├── documents_service.py      # Document management service
├── templates_service_pg.py   # Template management service
├── kb_service_pg.py          # Knowledge base service
├── audit_service.py          # Audit management service
├── code_review_service.py    # Code review service
├── ai_service.py             # AI integration service
├── email_service.py          # Email notification service
├── settings_service.py       # System settings service
└── training_service.py       # Training system service
```

#### 2.2.2 API Design Patterns

**RESTful Endpoint Structure:**
```
/auth/                     # Authentication endpoints
├── POST /signup          # User registration
├── POST /login           # User authentication
└── GET  /me              # Current user info

/projects/                 # Project management
├── POST /                # Create project
├── GET  /                # List user projects
├── GET  /{id}            # Get project details
├── PUT  /{id}            # Update project
├── DELETE /{id}          # Delete project
└── POST /{id}/members    # Add project members

/documents/                # Document management
├── POST /projects/{id}/documents    # Create document
├── GET  /projects/{id}/documents    # List project documents
├── GET  /{id}                      # Get document
├── PUT  /{id}                      # Update document
├── DELETE /{id}                    # Delete document
└── POST /{id}/reviews              # Submit review

/design-records/           # Design record management
├── POST /projects/{id}/requirements   # Create requirement
├── GET  /projects/{id}/requirements   # List requirements
├── PUT  /requirements/{id}            # Update requirement
├── GET  /projects/{id}/hazards        # List hazards
├── POST /projects/{id}/hazards        # Create hazard
├── GET  /projects/{id}/fmea           # FMEA analysis
├── POST /projects/{id}/traceability   # Update traceability
└── GET  /projects/{id}/export/{type}  # Export design record

/records/                  # ISO 13485 records management
├── GET  /suppliers                    # List suppliers
├── POST /suppliers                    # Create supplier
├── PUT  /suppliers/{id}              # Update supplier
├── GET  /parts                       # List parts
├── POST /parts                       # Create part
├── GET  /lab-equipment               # List lab equipment
├── GET  /customer-complaints         # List complaints
└── GET  /non-conformances           # List non-conformances

/activity-logs/            # Activity logging
├── GET  /                           # List activity logs
├── POST /                           # Create activity log
└── GET  /export                     # Export activity logs

/training/                 # Training system
├── GET  /learning-content           # Generate learning content
├── POST /assessment                 # Create training assessment
├── GET  /results/{user_id}          # Get training results
└── POST /submit-assessment          # Submit assessment answers

/settings/                 # System settings
├── GET  /smtp                       # Get SMTP configuration
├── POST /smtp                       # Update SMTP settings
└── GET  /system-health              # System health check

/admin/                    # Admin functions
├── GET  /users                      # List all users
├── POST /users                      # Create admin user
├── POST /users/{id}/reset-password  # Reset user password
└── PUT  /users/{id}/admin-status    # Update admin status

/kb/                      # Knowledge base
├── POST /collections                # Create collection
├── GET  /collections                # List collections
├── POST /upload                     # Upload document
├── POST /chat                       # Chat with KB
└── POST /update-project-summary     # Update project data
```

**Request/Response Model Pattern:**
```python
class DocumentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    document_type: str = Field(..., pattern="^(planning_documents|process_documents|...)$")
    content: str = Field(default="", min_length=0)
    status: str = Field(default="draft", pattern="^(active|draft|request_review|approved)$")
    reviewers: Optional[List[int]] = Field(default=None)

class DocumentResponse(BaseModel):
    id: str
    name: str
    document_type: str
    content: str
    status: str
    created_by_username: str
    created_at: datetime
    reviewers: List[dict] = []

class RequirementCreate(BaseModel):
    requirement_id: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    category: str = Field(..., pattern="^(functional|performance|safety|usability|...)$")
    priority: str = Field(..., pattern="^(low|medium|high|critical)$")
    verification_method: str = Field(..., pattern="^(test|inspection|analysis|demonstration)$")
    risk_level: str = Field(..., pattern="^(low|medium|high)$")

class HazardCreate(BaseModel):
    hazard_id: str = Field(..., min_length=1, max_length=50)
    hazardous_situation: str = Field(..., min_length=1)
    foreseeable_sequence: str = Field(..., min_length=1)
    harm: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(negligible|minor|serious|critical|catastrophic)$")
    probability: str = Field(..., pattern="^(improbable|remote|occasional|probable|frequent)$")
    risk_level: str = Field(..., pattern="^(low|medium|high)$")
    safety_integrity: str = Field(..., pattern="^(A|B|C|D|1|2|3|4|None)$")

class RecordCreate(BaseModel):
    record_type: str = Field(..., pattern="^(supplier|parts|lab_equipment|customer_complaints|non_conformances)$")
    name: str = Field(..., min_length=1, max_length=200)
    status: str = Field(..., pattern="^(active|pending|approved|rejected|...)$")
    created_date: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TrainingContentRequest(BaseModel):
    topics: List[str] = Field(..., min_items=1, max_items=10)
    collections: List[str] = Field(..., min_items=1, max_items=5)
    content_type: str = Field(..., pattern="^(learning_material|assessment_questions)$")
    difficulty_level: str = Field(default="intermediate", pattern="^(beginner|intermediate|advanced)$")
    question_count: int = Field(default=10, ge=5, le=50)

class AssessmentSubmission(BaseModel):
    user_id: int
    questions: List[dict]
    answers: List[bool]
    time_taken_minutes: int = Field(ge=1, le=120)
    topic_areas: List[str]

class SMTPConfigUpdate(BaseModel):
    server_name: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    auth_method: str = Field(default="normal_password")
    connection_security: str = Field(default="STARTTLS")
    enabled: bool = Field(default=True)

class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
```

#### 2.2.3 Authentication and Authorization
```python
# JWT Token-based Authentication
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Role-based Authorization Decorator
def verify_admin_token(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user_service.is_admin(user.id):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
```

### 2.3 Service Layer Architecture

#### 2.3.1 Service Design Pattern
Each service follows a consistent pattern for business logic encapsulation:

```python
class DocumentsService:
    def __init__(self):
        self.db = get_db()
    
    def create_document(self, name: str, content: str, project_id: str, user_id: int) -> Dict[str, Any]:
        # Business logic validation
        # Data transformation
        # Database operations
        # Notification triggers
        # Return structured response
    
    def update_document(self, document_id: str, **kwargs) -> Dict[str, Any]:
        # Permission checking
        # Version control logic
        # Update operations
        # Audit trail creation
    
    def _private_helper_method(self):
        # Internal business logic
```

#### 2.3.2 Service Dependencies and Integration
```python
# Service dependency injection pattern
class DocumentsService:
    def __init__(self):
        self.email_service = email_service
        self.kb_service = kb_service
        self.audit_service = audit_service
    
    def create_document(self, ...):
        # Create document
        document = self._create_db_record(...)
        
        # Trigger notifications
        self.email_service.send_document_notification(...)
        
        # Update knowledge base if approved
        if document.status == 'approved':
            self.kb_service.add_document_to_collection(...)
        
        return document
```

### 2.4 Data Layer Architecture

#### 2.4.1 Database Schema Design

**Core Entity Relationships:**
```
Users ←─────────────────┐
     │                  │
     └──→ Projects ←─────┼─────────────┐
           │             │             │
           ├──→ ProjectMembers         │
           │                          │
           ├──→ Documents ←─────┐      │
           │    │               │      │
           │    ├──→ DocumentRevisions │
           │    ├──→ DocumentReviewers │
           │    └──→ DocumentReviews   │
           │                          │
           ├──→ Templates ←─────┐      │
           │    │               │      │
           │    └──→ TemplateApprovals │
           │                          │
           ├──→ DesignRecords ←─────┐  │
           │    ├──→ Requirements    │  │
           │    ├──→ Hazards        │  │
           │    ├──→ FMEAAnalysis   │  │
           │    ├──→ TestArtifacts  │  │
           │    ├──→ DesignArtifacts│  │
           │    ├──→ Traceability   │  │
           │    └──→ Compliance     │  │
           │                          │
           ├──→ Records ←─────┐        │
           │    ├──→ Suppliers        │
           │    ├──→ Parts           │
           │    ├──→ LabEquipment    │
           │    ├──→ CustomerComplaints
           │    └──→ NonConformances │
           │                          │
           ├──→ ActivityLogs          │
           │                          │
           ├──→ Audits ←─────┐        │
           │    │            │        │
           │    └──→ Findings ←──→ CorrectiveActions
           │                          │
           └──→ Repositories ←──→ PullRequests ←──→ CodeReviews
```

#### 2.4.2 SQLAlchemy Model Architecture
```python
# Base model with common fields
class BaseModel:
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Domain models with relationships
class Document(Base, BaseModel):
    __tablename__ = "documents"
    
    name = Column(String(200), nullable=False)
    content = Column(Text, default="")
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships with lazy loading optimization
    project = relationship("Project", back_populates="documents")
    creator = relationship("User", foreign_keys=[created_by])
    reviewers = relationship("DocumentReviewer", back_populates="document")
    revisions = relationship("DocumentRevision", back_populates="document")

# Design Record Models
class Requirement(Base, BaseModel):
    __tablename__ = "requirements"
    
    requirement_id = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False)
    verification_method = Column(String(50), nullable=False)
    risk_level = Column(String(20), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    
    project = relationship("Project", back_populates="requirements")

class Hazard(Base, BaseModel):
    __tablename__ = "hazards"
    
    hazard_id = Column(String(50), nullable=False)
    hazardous_situation = Column(Text, nullable=False)
    foreseeable_sequence = Column(Text, nullable=False)
    harm = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    probability = Column(String(20), nullable=False)
    risk_level = Column(String(20), nullable=False)
    safety_integrity = Column(String(10))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    
    project = relationship("Project", back_populates="hazards")

# Records Management Models
class Supplier(Base, BaseModel):
    __tablename__ = "suppliers"
    
    supplier_id = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(200))
    email = Column(String(100))
    phone = Column(String(50))
    address = Column(Text)
    certification_status = Column(String(50))
    approval_status = Column(String(50))
    performance_rating = Column(String(20))
    quality_rating = Column(String(20))
    risk_level = Column(String(20))

class Part(Base, BaseModel):
    __tablename__ = "parts"
    
    part_number = Column(String(100), nullable=False)
    description = Column(String(500))
    supplier_id = Column(String(36), ForeignKey("suppliers.id"))
    udi = Column(String(100))
    lot_number = Column(String(100))
    serial_number = Column(String(100))
    expiration_date = Column(Date)
    received_date = Column(Date)
    current_stock = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=0)
    location = Column(String(200))
    status = Column(String(50))
    unit_cost = Column(Numeric(10, 2))
    
    supplier = relationship("Supplier", back_populates="parts")

class ActivityLog(Base, BaseModel):
    __tablename__ = "activity_logs"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    project_id = Column(String(36), ForeignKey("projects.id"))
    
    user = relationship("User", back_populates="activity_logs")
    project = relationship("Project", back_populates="activity_logs")
```

#### 2.4.3 Database Connection Management
```python
# Connection pooling and session management
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency injection for database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 3. Integration Architecture

### 3.1 Knowledge Base Services Integration

#### 3.1.1 Core Knowledge Base Architecture

The knowledge base system implements a comprehensive RAG (Retrieval Augmented Generation) pipeline that integrates multiple backend services to automatically build and maintain a searchable organizational knowledge repository.

```python
# Core Knowledge Base Service (kb_service_pg.py)
class KnowledgeBaseService:
    def __init__(self):
        # Hybrid database architecture
        self.db = get_database()  # PostgreSQL for metadata
        self.qdrant_client = qdrant_client.QdrantClient(url=config.QDRANT_URL)  # Vector DB
        self.ollama_client = ollama.Client(host=config.OLLAMA_BASE_URL)  # LLM service
        
        # Configuration
        self.embedding_model = config.DEFAULT_EMBEDDING_MODEL  # nomic-embed-text
        self.chat_model = config.DEFAULT_CHAT_MODEL  # qwen2:1.5b
        self.chunk_size = config.DEFAULT_CHUNK_SIZE  # 1000 chars
        self.similarity_limit = config.RAG_SIMILARITY_SEARCH_LIMIT  # 5
    
    def create_collection(self, name: str, description: str = "", created_by: int = 1):
        """Creates collection in both PostgreSQL and Qdrant"""
        # PostgreSQL metadata
        kb_collection = KBCollection(
            name=name,
            description=description,
            created_by=created_by,
            document_count=0,
            total_size_bytes=0
        )
        session.add(kb_collection)
        
        # Qdrant vector collection
        self.qdrant_client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=config.EMBEDDING_DIMENSIONS,  # 768
                distance=Distance.COSINE
            )
        )
        return kb_collection
    
    def add_document_to_collection(self, file_path: str, collection_name: str):
        """Processes document and adds to both databases"""
        # Extract text content
        content = self._extract_text_from_file(file_path)

#### 3.1.2 Automatic Integration Points

The system includes automatic knowledge base integration at key workflow completion points to build comprehensive organizational knowledge:

**Document Approval Integration (Documents.py:~412)**
```python
# Triggered when document status changes to "approved"
if edit_status == "approved":
    kb_content = f"# Document: {doc['name']}\n\n{doc['content']}"
    metadata = {
        "document_id": doc_id,
        "document_name": doc['name'],
        "approval_date": datetime.now().isoformat(),
        "approved_by": st.session_state.user_id,
        "document_type": doc.get('type', 'general'),
        "version": doc.get('version', '1.0')
    }
    # Automatically adds to default "knowledge_base" collection
    requests.post(f"{BACKEND_URL}/kb/add_text", 
                  params={"collection_name": "knowledge_base", ...})
```

**Template Approval Integration (Templates.py:~389)**
```python
# Triggered when template status changes to "approved"
if edit_status == "approved":
    kb_content = f"# Template: {edit_name}\n\n{edit_content}"
    metadata = {
        "template_id": template_id,
        "template_name": edit_name,
        "template_type": edit_type,
        "approval_date": datetime.now().isoformat(),
        "approved_by": st.session_state.user_id
    }
    # Silent integration with error handling
```

**Audit Completion Integration (Audit.py:~254)**
```python
# Triggered when audit status changes to "completed"
if edited_status == "completed":
    kb_content = f"""# Audit Report: {edited_title}
    **Audit Number**: {audit.get('audit_number', 'N/A')}
    **Type**: {edited_type.replace('_', ' ').title()}
    **Findings**: {edited_findings}
    **Recommendations**: {edited_recommendations}"""
    # Comprehensive audit metadata for searchability
```

**Design Record Export Integration (DesignRecord.py:~523)**
```python
# Triggered on Design Record PDF export
kb_content = f"# Design Record: {device_name}"
# Includes full design history, clinical data, and compliance information
```

**Integration Characteristics:**
- **Silent Operation**: All integrations use try/except blocks to prevent workflow disruption
- **Default Collection**: All content goes to configurable "knowledge_base" collection
- **Rich Metadata**: Each integration includes comprehensive contextual information
- **Configurable Timeouts**: Uses `KB_REQUEST_TIMEOUT` from config for network resilience
- **Authentication**: All requests include proper user authentication headers
        
        # Chunk content for optimal embedding
        chunks = self._chunk_text(content, self.chunk_size)
        
        # Generate embeddings for each chunk
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = self._generate_embedding(chunk)
            
            # Store in Qdrant with metadata payload
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[PointStruct(
                    id=f"{document_id}_{i}",
                    vector=embedding,
                    payload={
                        "document_id": document_id,
                        "filename": os.path.basename(file_path),
                        "chunk_index": i,
                        "text": chunk,
                        "collection": collection_name
                    }
                )]
            )
        
        # Update PostgreSQL metadata
        kb_document = KBDocument(
            filename=os.path.basename(file_path),
            content_type=self._detect_content_type(file_path),
            size_bytes=os.path.getsize(file_path),
            collection_name=collection_name,
            chunk_count=len(chunks),
            status="processed"
        )
        session.add(kb_document)
    
    def query_knowledge_base(self, query: str, collection_name: str):
        """RAG implementation for intelligent document querying"""
        # Step 1: Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Step 2: Vector similarity search
        search_results = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=self.similarity_limit,
            score_threshold=0.7
        )
        
        # Step 3: Assemble context from retrieved chunks
        context_chunks = [result.payload["text"] for result in search_results]
        context = "\n\n".join(context_chunks)
        
        # Step 4: Generate LLM response with context
        prompt = self._build_rag_prompt(query, context)
        response = self.ollama_client.chat(
            model=self.chat_model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Step 5: Log query for analytics
        self._log_query(query, collection_name, len(search_results))
        
        return {
            "response": response["message"]["content"],
            "sources": [r.payload for r in search_results],
            "confidence": min([r.score for r in search_results])
        }
```

#### 3.1.2 Integrated Services Architecture

**Service Integration Pattern**: Each domain service automatically integrates with the knowledge base to create a comprehensive organizational knowledge repository.

```python
# Documents Service Integration (documents_service.py)
class DocumentsService:
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
        self.db = get_database()
    
    def _update_document_knowledge_base(self, document_id: str):
        """Automatically adds approved documents to knowledge base"""
        document = self.get_document_by_id(document_id)
        if document.status == "approved":
            # Create project-specific collection
            collection_name = f"{document.project.name}".replace(' ', '_').lower()
            
            try:
                # Ensure collection exists
                self.kb_service.create_collection(
                    name=collection_name,
                    description=f"Documents for project: {document.project.name}"
                )
            except CollectionAlreadyExistsException:
                pass
            
            # Add document content to knowledge base
            self.kb_service.add_text_to_collection(
                text=document.content,
                collection_name=collection_name,
                metadata={
                    "document_id": document.id,
                    "document_name": document.name,
                    "project_id": document.project_id,
                    "document_type": document.document_type
                }
            )

# Templates Service Integration (templates_service_pg.py)
class TemplatesService:
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
    
    def _update_knowledge_base(self, template_id: str):
        """Adds approved templates to document-type collections"""
        template = self.get_template_by_id(template_id)
        if template.status == "approved":
            # Create document-type specific collection
            collection_name = template.document_type.replace(' ', '_').lower()
            
            self.kb_service.add_text_to_collection(
                text=template.content,
                collection_name=collection_name,
                metadata={
                    "template_id": template.id,
                    "template_name": template.name,
                    "document_type": template.document_type,
                    "version": template.version
                }
            )

# Audit Service Integration (audit_service.py)
class AuditService:
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
    
    def _update_finding_knowledge_base(self, finding_id: str):
        """Adds closed audit findings to knowledge base"""
        finding = self.get_finding_by_id(finding_id)
        if finding.status == "closed":
            collection_name = "audit_findings"
            
            # Combine finding details for knowledge base
            content = f"""
            Finding: {finding.finding_description}
            Root Cause: {finding.root_cause}
            Corrective Action: {finding.corrective_action}
            Resolution: {finding.resolution}
            """
            
            self.kb_service.add_text_to_collection(
                text=content,
                collection_name=collection_name,
                metadata={
                    "finding_id": finding.id,
                    "audit_id": finding.audit_id,
                    "severity": finding.severity,
                    "finding_type": finding.finding_type
                }
            )
```

#### 3.1.3 AI Service Integration

```python
# AI Service (ai_service.py)
class AIService:
    def __init__(self):
        self.ollama_client = ollama.Client(host=config.OLLAMA_BASE_URL)
        self.kb_service = KnowledgeBaseService()
        self.available_models = self._load_available_models()
    
    async def generate_document_assistance(self, document_type: str, content: str, user_input: str):
        """Provides AI assistance using knowledge base context"""
        # Query knowledge base for relevant context
        collection_name = document_type.replace(' ', '_').lower()
        kb_results = self.kb_service.query_knowledge_base(user_input, collection_name)
        
        # Build contextual prompt with KB results
        prompt = self._build_contextual_prompt(
            document_type, content, user_input, kb_results["response"]
        )
        
        try:
            response = await self.ollama_client.chat(
                model=self._get_optimal_model(document_type),
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.7, "top_p": 0.9}
            )
            return self._process_ai_response(response)
        except Exception as e:
            return self._handle_ai_error(e)
    
    def generate_learning_content_multi_topics(self, topics: List[str], collections: List[str]):
        """Generates training content from multiple knowledge base collections"""
        combined_content = []
        
        for collection in collections:
            # Extract content from each collection
            content = self.kb_service.search_collection(collection, limit=10)
            combined_content.extend(content)
        
        # Generate structured learning material
        prompt = self._build_learning_content_prompt(topics, combined_content)
        return self.ollama_client.generate(model=self.chat_model, prompt=prompt)
```

#### 3.1.4 Training System Integration

```python
# Training System (integrated with knowledge base)
class TrainingService:
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
        self.ai_service = AIService()
    
    def generate_learning_content(self, topics: List[str], collections: List[str]):
        """Generates comprehensive learning content from knowledge base"""
        # Aggregate content from multiple knowledge base collections
        combined_content = []
        for collection in collections:
            # Search for relevant content in each collection
            results = self.kb_service.search_collection(
                collection_name=collection,
                query=" ".join(topics),
                limit=10
            )
            combined_content.extend(results)
        
        # Generate structured learning material using AI
        learning_material = self.ai_service.generate_learning_content(
            source_content=combined_content,
            topics=topics,
            format="structured_content"
        )
        
        return {
            "content": learning_material,
            "sources": [r["metadata"] for r in combined_content],
            "topics_covered": topics
        }
    
    def generate_assessment_questions_multi_topics(self, topics: List[str], collections: List[str]):
        """Generates assessment questions from knowledge base content"""
        # Retrieve relevant content from multiple collections
        source_content = {}
        for collection in collections:
            results = self.kb_service.search_collection(
                collection_name=collection,
                query=" ".join(topics),
                limit=5
            )
            source_content[collection] = results
        
        # Generate True/False questions based on content
        questions = self.ai_service.generate_questions_from_content(
            source_content, question_type="true_false", count=10
        )
        
        return questions
    
    def evaluate_assessment(self, submission: AssessmentSubmission):
        """Evaluates training assessment and provides detailed feedback"""
        total_questions = len(submission.questions)
        correct_answers = sum(1 for i, answer in enumerate(submission.answers) 
                            if answer == submission.questions[i]["correct_answer"])
        
        score_percentage = (correct_answers / total_questions) * 100
        passing_score = 70  # From config.TRAINING_PASS_PERCENTAGE
        
        # Generate detailed feedback using AI
        feedback = self.ai_service.generate_assessment_feedback(
            questions=submission.questions,
            user_answers=submission.answers,
            topic_areas=submission.topic_areas,
            score=score_percentage
        )
        
        result = {
            "user_id": submission.user_id,
            "score_percentage": score_percentage,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "passed": score_percentage >= passing_score,
            "time_taken_minutes": submission.time_taken_minutes,
            "feedback": feedback,
            "topic_performance": self._analyze_topic_performance(
                submission.questions, submission.answers, submission.topic_areas
            )
        }
        
        # Store results in database
        self._store_assessment_result(result)
        
        return result
    
    def _analyze_topic_performance(self, questions, answers, topics):
        """Analyzes performance by topic area"""
        topic_scores = {}
        for topic in topics:
            topic_questions = [q for q in questions if topic in q.get("topics", [])]
            if topic_questions:
                correct = sum(1 for i, q in enumerate(topic_questions) 
                            if i < len(answers) and answers[i] == q["correct_answer"])
                topic_scores[topic] = (correct / len(topic_questions)) * 100
        return topic_scores
```

#### 3.1.5 Database Schema for Knowledge Base

```sql
-- PostgreSQL Schema for Knowledge Base Metadata
CREATE TABLE kb_collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    document_count INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,
    tags TEXT[],
    is_default BOOLEAN DEFAULT FALSE
);

CREATE TABLE kb_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(500) NOT NULL,
    content_type VARCHAR(100),
    size_bytes BIGINT,
    collection_name VARCHAR(255) REFERENCES kb_collections(name),
    chunk_count INTEGER,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'processing',
    metadata JSONB
);

CREATE TABLE kb_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    collection_name VARCHAR(255),
    response_time_ms INTEGER,
    result_count INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE kb_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE kb_document_tags (
    id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES kb_documents(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    tag_value VARCHAR(500)
);
```

This comprehensive knowledge base architecture automatically builds organizational knowledge from approved documents, templates, and audit findings, providing intelligent search and AI-powered assistance throughout the document workflow system.

#### 3.1.6 Training System Database Schema

```sql
-- Training System Database Schema
CREATE TABLE training_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) NOT NULL,
    topics TEXT[] NOT NULL,
    collections_used TEXT[] NOT NULL,
    learning_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB
);

CREATE TABLE training_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES training_sessions(id),
    user_id INTEGER REFERENCES users(id) NOT NULL,
    questions JSONB NOT NULL,
    user_answers BOOLEAN[] NOT NULL,
    correct_answers BOOLEAN[] NOT NULL,
    score_percentage DECIMAL(5,2) NOT NULL,
    passed BOOLEAN NOT NULL,
    time_taken_minutes INTEGER NOT NULL,
    topic_performance JSONB,
    feedback TEXT,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE training_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    total_attempts INTEGER DEFAULT 0,
    passed_attempts INTEGER DEFAULT 0,
    best_score DECIMAL(5,2) DEFAULT 0,
    last_attempt_date TIMESTAMP WITH TIME ZONE,
    competency_level VARCHAR(50) DEFAULT 'beginner',
    UNIQUE(user_id, topic)
);

CREATE TABLE system_smtp_settings (
    id SERIAL PRIMARY KEY,
    server_name VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    username VARCHAR(255) NOT NULL,
    password_encrypted TEXT NOT NULL,
    auth_method VARCHAR(50) DEFAULT 'normal_password',
    connection_security VARCHAR(50) DEFAULT 'STARTTLS',
    enabled BOOLEAN DEFAULT TRUE,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3.2 Email Service Integration

#### 3.2.1 SMTP Integration Architecture
```python
class EmailNotificationService:
    def __init__(self):
        self.smtp_settings = self._load_smtp_settings()
    
    def _create_smtp_connection(self):
        if self.smtp_settings["connection_security"] == "STARTTLS":
            server = smtplib.SMTP(self.smtp_settings["server_name"], self.smtp_settings["port"])
            server.starttls(context=ssl.create_default_context())
        elif self.smtp_settings["connection_security"] == "SSL":
            server = smtplib.SMTP_SSL(self.smtp_settings["server_name"], self.smtp_settings["port"])
        
        if self.smtp_settings["username"]:
            server.login(self.smtp_settings["username"], self.smtp_settings["password"])
        return server
    
    def send_notification(self, to_emails: List[str], subject: str, content: str):
        # Template-based email generation
        # Multi-format support (HTML/text)
        # Delivery tracking and error handling
```

### 3.3 File Storage Architecture

#### 3.3.1 Document Storage Strategy
```python
# File upload and processing pipeline
class DocumentProcessor:
    def process_upload(self, file: UploadFile) -> Dict[str, Any]:
        # File validation
        self._validate_file_type(file)
        self._validate_file_size(file)
        
        # Virus scanning (if configured)
        self._scan_for_malware(file)
        
        # Content extraction
        content = self._extract_text_content(file)
        
        # Metadata extraction
        metadata = self._extract_metadata(file)
        
        # Storage
        file_path = self._store_file(file)
        
        return {
            "file_path": file_path,
            "content": content,
            "metadata": metadata
        }
```

## 4. Security Architecture

### 4.1 Authentication and Authorization

#### 4.1.1 Multi-layered Security Model
```
┌─────────────────────────────────────────────────┐
│                 Frontend Layer                   │
│  ├── Session Management                         │
│  ├── Token Storage (HTTP-only cookies)         │
│  ├── Auto-refresh Logic                        │
│  └── Route Protection                          │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│                 API Gateway Layer               │
│  ├── JWT Token Validation                      │
│  ├── Rate Limiting                             │
│  ├── CORS Configuration                        │
│  └── Request Sanitization                     │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│              Authorization Layer                │
│  ├── Role-based Access Control (RBAC)         │
│  ├── Resource-level Permissions               │
│  ├── Project-level Access Control             │
│  └── Audit Logging                           │
└─────────────────────────────────────────────────┘
```

#### 4.1.2 Security Implementation Details
```python
# JWT Token Configuration
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password Security
PASSWORD_MIN_LENGTH = 8
PASSWORD_HASH_ROUNDS = 12

# Session Security
SECURE_COOKIE_SETTINGS = {
    "httponly": True,
    "secure": True,
    "samesite": "strict"
}

# Rate Limiting Configuration
RATE_LIMITS = {
    "auth": "5/minute",
    "api": "100/minute", 
    "upload": "10/hour"
}
```

### 4.2 Data Security

#### 4.2.1 Encryption Strategy
- **Data in Transit**: TLS 1.3 encryption for all HTTP communications
- **Data at Rest**: Database-level encryption for sensitive fields
- **Password Storage**: bcrypt hashing with salt rounds
- **Token Security**: JWT with short expiration and secure storage

#### 4.2.2 Access Control Matrix
```
Role          | Create | Read | Update | Delete | Admin
------------- |--------|------|--------|--------|-------
Super Admin   |   ✓    |  ✓   |   ✓    |   ✓    |   ✓
Admin         |   ✓    |  ✓   |   ✓    |   ✓    |   △
Project Admin |   △    |  △   |   △    |   △    |   ✗
User          |   △    |  △   |   △    |   ✗    |   ✗

✓ = Full Access, △ = Restricted Access, ✗ = No Access
```

## 5. Scalability Architecture

### 5.1 Horizontal Scaling Strategy

#### 5.1.1 Microservices Decomposition Readiness
```
Current Monolithic Structure → Future Microservices
┌─────────────────────────┐    ┌─────────────────────┐
│     FastAPI App         │    │   API Gateway       │
│  ├── All Services      │    │   (Load Balancer)   │
│  ├── Single Database   │ →  └─────────────────────┘
│  └── Shared Resources  │              │
└─────────────────────────┘              ▼
                                ┌─────────────────────┐
                                │   Service Mesh      │
                                ├─────────────────────┤
                                │ ┌─────┐ ┌─────────┐ │
                                │ │User │ │Document │ │
                                │ │Svc  │ │Service  │ │
                                │ └─────┘ └─────────┘ │
                                │ ┌─────┐ ┌─────────┐ │
                                │ │Audit│ │   KB    │ │
                                │ │Svc  │ │Service  │ │
                                │ └─────┘ └─────────┘ │
                                └─────────────────────┘
```

#### 5.1.2 Database Scaling Strategy
```python
# Read Replica Configuration
DATABASE_CONFIG = {
    "write": {
        "url": "postgresql://primary_db",
        "pool_size": 20,
        "max_overflow": 30
    },
    "read": [
        {
            "url": "postgresql://read_replica_1", 
            "pool_size": 10,
            "max_overflow": 20
        },
        {
            "url": "postgresql://read_replica_2",
            "pool_size": 10, 
            "max_overflow": 20
        }
    ]
}

# Automatic read/write splitting
class DatabaseRouter:
    def route_query(self, query_type: str, query: str):
        if query_type in ['SELECT', 'search', 'analytics']:
            return self._get_read_connection()
        else:
            return self._get_write_connection()
```

### 5.2 Performance Optimization Architecture

#### 5.2.1 Caching Strategy
```python
# Multi-level Caching Implementation
class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis-server')
        self.local_cache = {}
        self.cache_ttl = {
            'user_sessions': 3600,      # 1 hour
            'document_metadata': 1800,   # 30 minutes
            'search_results': 600,       # 10 minutes
            'system_settings': 3600      # 1 hour
        }
    
    def get_cached_data(self, key: str, fetch_function: callable):
        # L1: Local memory cache
        if key in self.local_cache:
            return self.local_cache[key]
        
        # L2: Redis cache
        cached = self.redis_client.get(key)
        if cached:
            data = json.loads(cached)
            self.local_cache[key] = data
            return data
        
        # L3: Database fetch with cache population
        data = fetch_function()
        self._populate_caches(key, data)
        return data
```

#### 5.2.2 Query Optimization
```python
# Optimized database queries with eager loading
class OptimizedQueries:
    def get_project_with_documents(self, project_id: str):
        return db.query(Project)\
            .options(
                joinedload(Project.documents)
                .joinedload(Document.creator),
                joinedload(Project.members)
                .joinedload(ProjectMember.user)
            )\
            .filter(Project.id == project_id)\
            .first()
    
    def get_user_dashboard_data(self, user_id: int):
        # Single query to fetch all dashboard data
        return db.execute(text("""
            SELECT 
                p.name as project_name,
                COUNT(d.id) as document_count,
                COUNT(CASE WHEN d.status = 'draft' THEN 1 END) as draft_count,
                COUNT(dr.id) as pending_reviews
            FROM projects p
            LEFT JOIN documents d ON p.id = d.project_id
            LEFT JOIN document_reviewers dr ON d.id = dr.document_id AND dr.reviewer_id = :user_id
            WHERE p.id IN (SELECT project_id FROM project_members WHERE user_id = :user_id)
            GROUP BY p.id, p.name
        """), {"user_id": user_id}).fetchall()
```

## 6. Monitoring and Observability

### 6.1 Logging Architecture
```python
# Structured logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "user_id": "%(user_id)s", "request_id": "%(request_id)s"}'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detailed'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/docsmait.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json'
        }
    },
    'loggers': {
        'docsmait': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
```

### 6.2 Health Check Architecture
```python
# Comprehensive health monitoring
class HealthChecker:
    async def check_system_health(self):
        checks = {
            'database': self._check_database(),
            'qdrant': self._check_qdrant(),
            'ollama': self._check_ollama(),
            'email': self._check_email_service(),
            'disk_space': self._check_disk_space(),
            'memory': self._check_memory_usage()
        }
        
        results = {}
        overall_status = 'healthy'
        
        for service, check in checks.items():
            try:
                result = await check
                results[service] = {
                    'status': 'healthy',
                    'response_time': result.get('response_time'),
                    'details': result.get('details')
                }
            except Exception as e:
                results[service] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                overall_status = 'degraded'
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'services': results
        }
```

## 7. Deployment Architecture

### 7.1 Container Strategy
```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as base
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

FROM base as backend
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as frontend  
WORKDIR /app
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY frontend/ .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

### 7.2 Docker Compose Architecture
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: docsmait
      POSTGRES_USER: docsmait_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
  
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
  
  backend:
    build:
      context: .
      target: backend
    depends_on:
      - postgres
      - qdrant
      - ollama
    environment:
      DATABASE_URL: postgresql://docsmait_user:${DB_PASSWORD}@postgres:5432/docsmait
      QDRANT_URL: http://qdrant:6333
      OLLAMA_BASE_URL: http://ollama:11434
    ports:
      - "8000:8000"
  
  frontend:
    build:
      context: .
      target: frontend
    depends_on:
      - backend
    environment:
      BACKEND_URL: http://backend:8000
    ports:
      - "8501:8501"
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  qdrant_data:
  ollama_data:
```

## 8. Maintenance and Operations Architecture

### 8.1 Backup Strategy
```python
# Automated backup system
class BackupManager:
    def __init__(self):
        self.postgres_config = get_postgres_config()
        self.qdrant_client = qdrant_client.QdrantClient()
        self.s3_client = boto3.client('s3')  # For cloud backup
    
    def create_full_backup(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"backups/{timestamp}"
        
        # Database backup
        pg_dump_cmd = f"pg_dump {self.postgres_config['url']} > {backup_dir}/database.sql"
        subprocess.run(pg_dump_cmd, shell=True, check=True)
        
        # Vector database backup
        collections = self.qdrant_client.get_collections()
        for collection in collections.collections:
            collection_backup = self.qdrant_client.scroll(
                collection_name=collection.name,
                limit=10000
            )
            with open(f"{backup_dir}/qdrant_{collection.name}.json", 'w') as f:
                json.dump(collection_backup, f)
        
        # File system backup
        shutil.make_archive(f"{backup_dir}/files", 'gztar', 'uploads/')
        
        # Upload to cloud storage
        self._upload_to_cloud(backup_dir)
        
        return backup_dir
```

### 8.2 System Monitoring
```python
# Performance metrics collection
class MetricsCollector:
    def __init__(self):
        self.metrics_db = MetricsDatabase()
    
    def collect_system_metrics(self):
        metrics = {
            'timestamp': datetime.utcnow(),
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'active_connections': self._count_db_connections(),
            'response_times': self._get_response_times(),
            'error_rates': self._get_error_rates(),
            'user_activity': self._get_user_activity()
        }
        
        self.metrics_db.store_metrics(metrics)
        self._check_alerts(metrics)
        
        return metrics
    
    def _check_alerts(self, metrics):
        alerts = []
        if metrics['cpu_usage'] > 80:
            alerts.append({'type': 'high_cpu', 'value': metrics['cpu_usage']})
        if metrics['memory_usage'] > 85:
            alerts.append({'type': 'high_memory', 'value': metrics['memory_usage']})
        if metrics['error_rates'] > 5:
            alerts.append({'type': 'high_errors', 'value': metrics['error_rates']})
        
        if alerts:
            self._send_alerts(alerts)
```

## 9. Technology Stack Summary

### 9.1 Core Technologies
- **Backend Framework**: FastAPI (Python 3.11+)
- **Frontend Framework**: Streamlit (Python)
- **Primary Database**: PostgreSQL 15
- **Vector Database**: Qdrant
- **AI/ML Platform**: Ollama
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT with bcrypt
- **API Documentation**: OpenAPI/Swagger

### 9.2 Infrastructure Dependencies
- **Web Server**: Uvicorn (ASGI)
- **Reverse Proxy**: Nginx
- **Email Service**: SMTP (configurable)
- **File Storage**: Local filesystem (expandable to cloud)
- **Logging**: Python logging with rotation
- **Process Management**: Docker/Docker Compose

### 9.3 Development Tools
- **Package Management**: pip/requirements.txt
- **Database Migrations**: Alembic
- **Code Quality**: Pydantic for validation
- **Testing**: pytest (planned)
- **Documentation**: Markdown with OpenAPI

---

**Document Version**: 1.1  
**Last Updated**: 2025-01-15  
**Architecture Review Date**: 2025-01-15

### Recent Updates (v1.1)
- Added Training System architecture with AI-powered content generation
- Added SMTP email service configuration and management
- Added admin password reset functionality with security controls  
- Enhanced export capabilities with CSV and Markdown formats
- Updated API endpoints for training, settings, and admin functions
- Added comprehensive database schemas for training and system settings