# Docsmait System Architecture

## Overview

Docsmait is a comprehensive AI-powered document and compliance management system built using modern microservices architecture with containerized deployment. This document provides detailed technical architecture, design patterns, and implementation details.

## 1. High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Web Browser]
        API_Client[API Clients]
    end
    
    subgraph "Frontend Layer"
        Streamlit[Streamlit Frontend<br/>Port: 8501]
    end
    
    subgraph "Backend Layer"
        FastAPI[FastAPI Backend<br/>Port: 8000]
        Auth[Authentication Service]
        Services[Business Services]
    end
    
    subgraph "AI Layer"
        Ollama[Ollama LLM Service<br/>Port: 11434]
        Embedding[Embedding Service]
    end
    
    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL<br/>Port: 5432)]
        Qdrant[(Qdrant Vector DB<br/>Port: 6333)]
        FileSystem[File Storage]
    end
    
    UI --> Streamlit
    API_Client --> FastAPI
    Streamlit --> FastAPI
    FastAPI --> Auth
    FastAPI --> Services
    Services --> PostgreSQL
    Services --> Ollama
    Services --> Qdrant
    Services --> FileSystem
    Embedding --> Qdrant
```

## 2. Component Architecture

### 2.1 Frontend Architecture

#### 2.1.1 Streamlit Application Structure
```
frontend/
├── app.py                 # Main application entry point
├── config.py             # Frontend configuration
├── auth_utils.py         # Authentication utilities
├── pages/                # Page components
│   ├── Home.py           # Dashboard
│   ├── Projects.py       # Project management
│   ├── Issues.py         # Issue tracking
│   ├── DesignRecord.py   # Design record system
│   ├── Templates.py      # Template management
│   ├── Training.py       # Training system
│   ├── Settings.py       # System settings
│   └── Auth.py          # Authentication
└── components/           # Reusable UI components
```

#### 2.1.2 Key Frontend Patterns
- **Page-Based Architecture**: Each major feature as separate Streamlit page
- **Session State Management**: Centralized state management using st.session_state
- **Component Reusability**: Shared UI components and utilities
- **Configuration-Driven**: Environment-based configuration management
- **Interactive DataFrames**: st.dataframe with selection and filtering capabilities

### 2.2 Backend Architecture

#### 2.2.1 FastAPI Application Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Backend configuration
│   ├── database_config.py   # Database configuration
│   ├── models.py            # Pydantic models
│   ├── db_models.py         # SQLAlchemy ORM models
│   ├── auth.py              # Authentication handlers
│   ├── dependencies.py      # FastAPI dependencies
│   ├── services/            # Business logic services
│   │   ├── user_service.py
│   │   ├── project_service.py
│   │   ├── issues_service.py
│   │   ├── templates_service.py
│   │   ├── kb_service.py
│   │   └── ai_service.py
│   └── routers/             # API route handlers
│       ├── auth.py
│       ├── projects.py
│       ├── issues.py
│       ├── documents.py
│       └── kb.py
├── migrations/              # Database migration scripts
└── requirements.txt         # Python dependencies
```

#### 2.2.2 Service Layer Pattern
The backend follows a layered architecture with clear separation of concerns:

- **API Layer (Routers)**: HTTP request handling and validation
- **Service Layer**: Business logic and orchestration
- **Data Layer**: Database access and ORM operations
- **Integration Layer**: External service integrations (AI, email)

### 2.3 Database Architecture

#### 2.3.1 PostgreSQL Schema Design

```sql
-- Core entity relationships
Users (1) -> (N) ProjectMembers (N) -> (1) Projects
Projects (1) -> (N) Issues
Projects (1) -> (N) Documents
Projects (1) -> (N) Templates
Users (1) -> (N) Issues (created_by)
Issues (1) -> (N) IssueComments

-- Design Record entities
Projects (1) -> (N) SystemRequirements
Projects (1) -> (N) SystemHazards
Projects (1) -> (N) FMEAAnalyses
Projects (1) -> (N) TestManagement

-- Records Management entities
Projects (1) -> (N) SupplierManagement
Projects (1) -> (N) PartsInventory
Projects (1) -> (N) LabEquipment
Projects (1) -> (N) CustomerComplaints
Projects (1) -> (N) NonConformances
```

#### 2.3.2 Key Database Design Patterns
- **UUID Primary Keys**: All entities use UUID for globally unique identifiers
- **Soft Deletes**: Critical records use soft delete patterns for audit compliance
- **Audit Trail**: Created/updated timestamps with user attribution
- **Composite Indexes**: Optimized queries for project-scoped operations
- **JSON Columns**: Flexible metadata storage (labels, assignees, etc.)

### 2.4 AI/ML Architecture

#### 2.4.1 Knowledge Base Pipeline
```mermaid
graph LR
    Doc[Documents] --> Chunk[Text Chunking]
    Chunk --> Embed[Embedding Generation]
    Embed --> Store[Vector Storage]
    Query[User Query] --> QEmbed[Query Embedding]
    QEmbed --> Search[Similarity Search]
    Store --> Search
    Search --> Retrieve[Retrieved Context]
    Retrieve --> LLM[LLM Generation]
    LLM --> Response[AI Response]
```

#### 2.4.2 AI Service Integration
- **Ollama Integration**: Local LLM deployment for content generation
- **Qdrant Vector Database**: High-performance vector similarity search
- **Embedding Pipeline**: Automatic document vectorization
- **RAG Implementation**: Retrieval-Augmented Generation for accurate responses
- **Model Management**: Configurable AI model selection and parameters

#### 2.4.3 Knowledge Base Chat Architecture

The system now includes AI-powered document creation with Knowledge Base chat functionality integrated across multiple document workflows:

```mermaid
graph TB
    subgraph "Document Creation Flow"
        DC[Document Create] --> ChatToggle{Chat Mode?}
        ChatToggle -->|Yes| ChatInterface[KB Chat Interface]
        ChatToggle -->|No| PreviewMode[Live Preview Mode]
    end
    
    subgraph "Document Editing Flow"
        DE[Document Edit] --> EditChat[KB Chat with Context]
        EditChat --> DocContext[Current Document Content]
    end
    
    subgraph "Document Review Flow"  
        DR[Document Review] --> ReviewChat[KB Chat for Review]
        ReviewChat --> ReviewContext[Document Under Review]
    end
    
    subgraph "KB Chat Processing"
        ChatInterface --> QueryAPI["KB Query with Context API"]
        EditChat --> QueryAPI
        ReviewChat --> QueryAPI
        QueryAPI --> ContextEngine[Context Combination Engine]
        ContextEngine --> VectorSearch[Qdrant Vector Search]
        ContextEngine --> DocContext
        ContextEngine --> ReviewContext
        VectorSearch --> LLMPrompt[Enhanced LLM Prompt]
        LLMPrompt --> OllamaLLM[Ollama LLM Processing]
        OllamaLLM --> ChatResponse[Contextual Response]
    end
```

**Key Features:**
- **Context-Aware Chat**: Combines current document content with Knowledge Base search results
- **Concurrent Editing**: Document content snapshot at query time allows continued editing during chat processing
- **Session Management**: Independent chat histories per document with configurable limits
- **Mutually Exclusive Modes**: Toggle between Live Preview and Chat modes for optimal UX
- **Response Limits**: Configurable limits for chat history (default: 20 responses, 5000 chars per response)

## 3. Data Flow Architecture

### 3.1 Request Processing Flow

```mermaid
sequenceDiagram
    participant Client
    participant Streamlit
    participant FastAPI
    participant Service
    participant Database
    participant AI_Service
    
    Client->>Streamlit: User Action
    Streamlit->>FastAPI: HTTP API Request
    FastAPI->>FastAPI: Authentication Check
    FastAPI->>Service: Business Logic Call
    Service->>Database: Data Operations
    Service->>AI_Service: AI Processing (if needed)
    AI_Service-->>Service: AI Response
    Service-->>FastAPI: Service Response
    FastAPI-->>Streamlit: HTTP Response
    Streamlit-->>Client: UI Update
```

### 3.2 Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant Frontend
    participant Backend
    participant Database
    
    Client->>Frontend: Login Credentials
    Frontend->>Backend: POST /auth/login
    Backend->>Database: Verify User
    Database-->>Backend: User Data
    Backend->>Backend: Generate JWT Token
    Backend-->>Frontend: JWT Token
    Frontend->>Frontend: Store in Session State
    
    Note over Client,Database: Subsequent Requests
    Frontend->>Backend: API Call + JWT Token
    Backend->>Backend: Validate JWT
    Backend-->>Frontend: Protected Resource
```

### 3.3 Issue Management Flow

```mermaid
sequenceDiagram
    participant User
    participant Issues_Page
    participant Issues_API
    participant Issues_Service
    participant Database
    participant Email_Service
    
    User->>Issues_Page: Create Issue
    Issues_Page->>Issues_API: POST /projects/{id}/issues
    Issues_API->>Issues_Service: create_issue()
    Issues_Service->>Issues_Service: Generate Issue Number
    Issues_Service->>Database: Insert Issue
    Issues_Service->>Email_Service: Send Notifications
    Email_Service->>Email_Service: Send SMTP Email
    Issues_Service-->>Issues_API: Success Response
    Issues_API-->>Issues_Page: Issue Created
    Issues_Page-->>User: Success Notification
```

## 4. Security Architecture

### 4.1 Authentication and Authorization

#### 4.1.1 JWT-Based Authentication
- **Token Structure**: Header.Payload.Signature with user claims
- **Expiration**: Configurable token lifetime with automatic refresh
- **Storage**: HTTP-only cookies with secure flags
- **Validation**: Middleware-based token validation on protected routes

#### 4.1.2 Role-Based Access Control (RBAC)
```python
class UserRole(Enum):
    SUPER_ADMIN = "super_admin"  # System-wide access
    ADMIN = "admin"              # Administrative functions
    USER = "user"                # Standard user access

class ProjectRole(Enum):
    ADMIN = "admin"              # Project administration
    MEMBER = "member"            # Project collaboration
```

### 4.2 Data Protection

#### 4.2.1 Encryption Strategy
- **At Rest**: Database-level encryption for sensitive fields
- **In Transit**: HTTPS/TLS for all client-server communication
- **Password Storage**: bcrypt hashing with configurable cost factor
- **Secrets Management**: Environment-based configuration with Docker secrets

#### 4.2.2 Input Validation and Sanitization
- **Pydantic Models**: Comprehensive request/response validation
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy ORM
- **XSS Prevention**: Input sanitization and output encoding
- **CSRF Protection**: Token-based CSRF protection for sensitive operations

## 5. Deployment Architecture

### 5.1 Docker Containerization

#### 5.1.1 Container Structure
```yaml
services:
  frontend:
    image: docsmait/frontend
    ports: ["8501:8501"]
    depends_on: [backend]
    
  backend:
    image: docsmait/backend  
    ports: ["8000:8000"]
    depends_on: [postgres, qdrant, ollama]
    
  postgres:
    image: postgres:13
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
    
  qdrant:
    image: qdrant/qdrant
    ports: ["6333:6333"]
    volumes: [qdrant_data:/qdrant/storage]
    
  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
    volumes: [ollama_data:/root/.ollama]
```

#### 5.1.2 Health Checks and Monitoring
- **Container Health Checks**: HTTP endpoint monitoring
- **Service Dependencies**: Proper startup order with health checks
- **Volume Persistence**: Data persistence across container restarts
- **Resource Limits**: Memory and CPU constraints for stability

### 5.2 Configuration Management

#### 5.2.1 Environment-Based Configuration
```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@postgres:5432/docsmait

# AI Services Configuration  
OLLAMA_BASE_URL=http://ollama:11434
QDRANT_URL=http://qdrant:6333

# Application Configuration
JWT_SECRET_KEY=secure-secret-key
LOG_LEVEL=INFO
```

#### 5.2.2 Secrets Management
- **Environment Variables**: Non-sensitive configuration
- **Docker Secrets**: Sensitive data (passwords, keys)
- **External Secret Management**: Integration with HashiCorp Vault (optional)
- **Configuration Validation**: Startup validation of required settings

## 6. Performance Architecture

### 6.1 Database Optimization

#### 6.1.1 Indexing Strategy
```sql
-- Project-scoped queries
CREATE INDEX idx_issues_project_status ON issues (project_id, status);
CREATE INDEX idx_documents_project_type ON documents (project_id, document_type);

-- Full-text search
CREATE INDEX idx_issues_title_search ON issues USING gin(to_tsvector('english', title));

-- Time-based queries
CREATE INDEX idx_activity_logs_timestamp ON activity_logs (timestamp);
```

#### 6.1.2 Connection Management
- **Connection Pooling**: SQLAlchemy connection pool optimization
- **Query Optimization**: Eager loading for complex relationships
- **Pagination**: Efficient pagination for large datasets
- **Caching**: Application-level caching for frequent queries

### 6.2 AI Service Optimization

#### 6.2.1 Vector Search Optimization
- **Index Configuration**: HNSW indexing for fast similarity search
- **Embedding Caching**: Cache embeddings for frequently accessed content
- **Batch Processing**: Bulk embedding generation for large document sets
- **Model Management**: Efficient model loading and memory management

#### 6.2.2 Response Time Optimization
- **Streaming Responses**: Real-time response streaming for AI queries
- **Context Window Management**: Optimal context size for LLM queries
- **Model Selection**: Appropriate model size for use case requirements
- **Timeout Management**: Configurable timeouts for AI operations

## 7. Integration Architecture

### 7.1 Email Integration

#### 7.1.1 SMTP Service Architecture
```python
class EmailNotificationService:
    def __init__(self):
        self.smtp_settings = self._load_smtp_settings()
        
    def send_notification(self, template, recipients, context):
        # Template-based email generation
        # SMTP connection management
        # Delivery status tracking
```

#### 7.1.2 Notification System
- **Event-Driven Architecture**: Service-based event publishing
- **Template Management**: HTML and text email templates
- **Delivery Tracking**: Email delivery status monitoring
- **Configuration Management**: Database-stored SMTP settings

### 7.2 Export System Architecture

#### 7.2.1 Export Service Design
```python
class ExportService:
    def export_data(self, format: str, filters: dict):
        # Data extraction with filtering
        # Format conversion (CSV, Markdown, PDF)
        # Stream processing for large datasets
        # Audit trail for exports
```

#### 7.2.2 Format Support
- **CSV Export**: Structured data export with configurable columns
- **Markdown Export**: Documentation-friendly format with formatting
- **PDF Generation**: Professional reports with styling
- **Excel Export**: Advanced formatting with multiple sheets

## 8. Monitoring and Observability

### 8.1 Logging Architecture

#### 8.1.1 Structured Logging
```python
import structlog

logger = structlog.get_logger()
logger.info("User action", 
    user_id=user.id,
    action="issue_created",
    issue_id=issue.id,
    project_id=project.id
)
```

#### 8.1.2 Log Management
- **Centralized Logging**: Container log aggregation
- **Log Levels**: Configurable logging levels per service
- **Audit Logging**: Comprehensive audit trail for compliance
- **Log Rotation**: Automated log rotation and retention

### 8.2 Metrics and Monitoring

#### 8.2.1 Application Metrics
- **API Performance**: Response time and error rate monitoring
- **Database Performance**: Query performance and connection metrics
- **AI Service Metrics**: Model performance and resource utilization
- **User Activity**: Usage patterns and feature adoption

#### 8.2.2 Health Monitoring
- **Service Health Checks**: HTTP endpoint monitoring
- **Resource Monitoring**: CPU, memory, and disk usage
- **Dependency Monitoring**: Database and external service health
- **Alerting**: Configurable alerts for critical issues

## 9. Scalability Architecture

### 9.1 Horizontal Scaling

#### 9.1.1 Stateless Design
- **Stateless Services**: Session state managed externally
- **Database-Backed Sessions**: Persistent session storage
- **Load Balancer Ready**: Multiple instance deployment
- **Container Orchestration**: Kubernetes/Docker Swarm support

#### 9.1.2 Database Scaling
- **Read Replicas**: Read-only database replicas for query distribution
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Indexed queries for large datasets
- **Partitioning**: Table partitioning for time-series data

### 9.2 Performance Optimization

#### 9.2.1 Caching Strategy
```python
# Application-level caching
@cache.memoize(timeout=300)
def get_project_members(project_id: str):
    return db.query(ProjectMember).filter(...).all()

# Vector embedding caching
embeddings_cache = TTLCache(maxsize=1000, ttl=3600)
```

#### 9.2.2 Asynchronous Processing
- **Background Tasks**: Celery-based task queue for heavy operations
- **Async API Operations**: FastAPI async/await patterns
- **Streaming Responses**: Real-time data streaming
- **Batch Processing**: Efficient bulk operations

## 10. Security Considerations

### 10.1 Application Security

#### 10.1.1 OWASP Top 10 Mitigation
- **Injection Prevention**: Parameterized queries and input validation
- **Broken Authentication**: JWT best practices and secure session management
- **Sensitive Data Exposure**: Encryption at rest and in transit
- **XML External Entities**: Secure XML parsing (where applicable)
- **Broken Access Control**: Comprehensive RBAC implementation
- **Security Misconfiguration**: Secure default configurations
- **Cross-Site Scripting**: Input sanitization and output encoding
- **Insecure Deserialization**: Safe data serialization practices
- **Known Vulnerabilities**: Regular dependency updates
- **Insufficient Logging**: Comprehensive security event logging

#### 10.1.2 API Security
- **Rate Limiting**: Request throttling to prevent abuse
- **CORS Configuration**: Proper Cross-Origin Resource Sharing setup
- **Request Validation**: Comprehensive input validation with Pydantic
- **Error Handling**: Secure error responses without information leakage

## 11. Compliance Architecture

### 11.1 Regulatory Compliance

#### 11.1.1 21 CFR Part 11 Compliance
- **Electronic Records**: Tamper-proof audit trails
- **Electronic Signatures**: Digital signature support
- **Access Controls**: Role-based access with authentication
- **Data Integrity**: Comprehensive data validation and verification

#### 11.1.2 ISO 13485 Quality Management
- **Document Control**: Version control with approval workflows
- **Risk Management**: Comprehensive risk assessment and mitigation
- **Traceability**: Requirements to design to test traceability
- **Training Records**: Personnel training tracking and verification

### 11.2 Data Governance

#### 11.2.1 Data Retention and Archival
- **Retention Policies**: Configurable data retention periods
- **Archival Strategies**: Long-term data storage and retrieval
- **Data Deletion**: Secure data deletion with audit trails
- **Backup and Recovery**: Comprehensive backup and disaster recovery

---

**Document Control:**
- **Version**: 1.2
- **Last Updated**: January 2025
- **Next Review**: July 2025
- **Approved By**: Architecture Review Board