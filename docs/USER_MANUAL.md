# Docsmait User Manual

**Version**: 2.0  
**Last Updated**: September 2025  
**Document Type**: User Manual

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Requirements](#2-system-requirements)
3. [Installation](#3-installation)
4. [Configuration](#4-configuration)
5. [Getting Started](#5-getting-started)
6. [Features Guide](#6-features-guide)
   - [6.1 Authentication & User Management](#61-authentication--user-management)
   - [6.2 Project Management](#62-project-management)
   - [6.3 Knowledge Base](#63-knowledge-base)
   - [6.4 Template Management](#64-template-management)
   - [6.5 Document Management](#65-document-management)
   - [6.6 Code Review Management](#66-code-review-management)
   - [6.7 Specification Management](#67-specification-management)
   - [6.8 Audit Management](#68-audit-management)
   - [6.9 AI Configuration](#69-ai-configuration)
7. [Advanced Features](#7-advanced-features)
8. [Troubleshooting](#8-troubleshooting)
9. [API Reference](#9-api-reference)
10. [Backup & Migration](#10-backup--migration)
11. [De-installation](#11-de-installation)
12. [Support](#12-support)

---

## 1. Overview

**Docsmait** is a comprehensive document management and AI-powered knowledge base system designed for organizations requiring regulatory compliance and quality management. The platform combines document management, template systems, audit capabilities, and intelligent search powered by Large Language Models (LLMs).

### Key Features
- **AI-Powered Knowledge Base**: RAG (Retrieval Augmented Generation) pipeline with vector search
- **Template Management**: Rich markdown templates with approval workflows
- **Document Management**: Version control, reviews, and compliance tracking
- **Audit Management**: ISO 13485:2016 compliant audit workflows
- **Code Review**: Git integration for code review management
- **Specification Management**: Requirements and risk management with traceability
- **Multi-Domain Support**: Automotive (ASIL), Medical (ISO), Industrial (SIL), Aviation (DAL)

### Architecture
- **Frontend**: Streamlit web interface
- **Backend**: FastAPI with RESTful APIs
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Database**: Qdrant for semantic search
- **AI Engine**: Ollama for local LLM inference
- **Containerization**: Docker Compose orchestration

---

## 2. System Requirements

### Minimum Requirements
- **CPU**: 4 cores, 2.0 GHz
- **RAM**: 8 GB
- **Storage**: 20 GB available space
- **OS**: Linux, Windows 10/11, macOS 10.15+
- **Docker**: Docker Engine 20.10+ and Docker Compose 2.0+

### Recommended Requirements
- **CPU**: 8 cores, 3.0 GHz
- **RAM**: 16 GB (32 GB for large knowledge bases)
- **Storage**: 50 GB SSD
- **GPU**: NVIDIA GPU with 8+ GB VRAM (optional, for faster AI inference)
- **Network**: 1 Gbps for multi-user deployments

### Supported Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## 3. Installation

### 3.1 Prerequisites

1. **Install Docker and Docker Compose**:
   ```bash
   # Linux (Ubuntu/Debian)
   sudo apt update
   sudo apt install docker.io docker-compose-plugin
   sudo usermod -aG docker $USER
   
   # Windows/macOS: Install Docker Desktop
   # Download from: https://www.docker.com/products/docker-desktop
   ```

2. **Clone Repository**:
   ```bash
   git clone https://github.com/your-org/docsmait.git
   cd docsmait
   ```

### 3.2 Quick Start Installation

1. **Configure Environment** (optional):
   ```bash
   # Copy configuration template
   cp .env.docker .env
   
   # Edit configuration (optional)
   nano .env
   ```

2. **Start Services**:
   ```bash
   # Start all services
   docker compose up -d
   
   # Check service status
   docker compose ps
   ```

3. **Initialize Database**:
   ```bash
   # Run database initialization
   docker compose exec backend python init_db.py
   ```

4. **Access Application**:
   - **Frontend**: http://localhost:8501
   - **Backend API**: http://localhost:8001
   - **API Documentation**: http://localhost:8001/docs

### 3.3 Production Installation

1. **Set Production Configuration**:
   ```bash
   # Copy and edit production config
   cp .env.docker .env.production
   
   # Edit production settings
   nano .env.production
   ```

   **Key Production Settings**:
   ```bash
   # Security
   JWT_SECRET_KEY=your_secure_random_key_here
   DB_PASSWORD=secure_database_password
   
   # Performance  
   OLLAMA_MEMORY_LIMIT=8G
   BACKEND_MEMORY_LIMIT=4G
   
   # Ports (change if needed)
   BACKEND_HOST_PORT=80
   FRONTEND_HOST_PORT=443
   ```

2. **Start with Production Config**:
   ```bash
   docker compose --env-file .env.production up -d
   ```

3. **Set Up SSL/TLS** (recommended):
   ```bash
   # Use nginx-proxy or Traefik for SSL termination
   # See Advanced Configuration section
   ```

### 3.4 GPU Support (Optional)

For faster AI inference with NVIDIA GPU:

1. **Install NVIDIA Container Runtime**:
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
   curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
     sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
     sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   sudo apt update
   sudo apt install nvidia-container-toolkit
   sudo systemctl restart docker
   ```

2. **Enable GPU in Configuration**:
   ```bash
   # .env file
   OLLAMA_GPU_ENABLED=true
   ```

---

## 4. Configuration

### 4.1 Environment Variables

Docsmait supports extensive configuration through environment variables. All settings have sensible defaults but can be customized for your environment.

#### Core Services

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://backend:8000` | Backend API URL for frontend |
| `DATABASE_URL` | Auto-constructed | Full PostgreSQL connection string |
| `DB_USER` | `docsmait_user` | Database username |
| `DB_PASSWORD` | `docsmait_password` | Database password |
| `DB_HOST` | `docsmait_postgres` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `docsmait` | Database name |

#### Service Ports

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_HOST_PORT` | `8001` | Host port for backend API |
| `FRONTEND_HOST_PORT` | `8501` | Host port for Streamlit frontend |
| `OLLAMA_HOST_PORT` | `11435` | Host port for Ollama LLM service |
| `QDRANT_REST_HOST_PORT` | `6335` | Host port for Qdrant REST API |
| `QDRANT_GRPC_HOST_PORT` | `6336` | Host port for Qdrant gRPC |
| `POSTGRES_HOST_PORT` | `5433` | Host port for PostgreSQL |

#### AI Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_CHAT_MODEL` | `qwen2:1.5b` | Default LLM model |
| `DEFAULT_EMBEDDING_MODEL` | `nomic-embed-text` | Default embedding model |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama service URL |
| `AI_TIMEOUT` | `120` | AI request timeout (seconds) |
| `MAX_RESPONSE_LENGTH` | `2000` | Maximum AI response length |
| `AI_CONTEXT_WINDOW` | `4000` | AI context window size |
| `EMBEDDING_DIMENSIONS` | `768` | Vector embedding dimensions |

#### Knowledge Base

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_COLLECTION_NAME` | `knowledge_base` | Default vector collection |
| `DEFAULT_CHUNK_SIZE` | `1000` | Text chunking size |
| `MAX_FILE_SIZE_MB` | `10` | Maximum upload file size |
| `RAG_SIMILARITY_SEARCH_LIMIT` | `5` | Number of similar chunks to retrieve |

### 4.2 Configuration Examples

#### Development Environment
```bash
# .env
BACKEND_HOST_PORT=8001
FRONTEND_HOST_PORT=8501
DEFAULT_CHAT_MODEL=qwen2:0.5b  # Faster for dev
AI_TIMEOUT=60                   # Shorter for dev
```

#### Production Environment
```bash
# .env
BACKEND_HOST_PORT=80
FRONTEND_HOST_PORT=443
DEFAULT_CHAT_MODEL=qwen2:7b     # Better quality
AI_TIMEOUT=300                  # Longer for complex queries
DB_PASSWORD=secure_password_123
JWT_SECRET_KEY=your_production_secret
```

### 4.3 Initial Setup

1. **Create Admin User**:
   ```bash
   docker compose exec backend python -c "
   from app.database_config import get_database
   from app.db_models import User
   from passlib.context import CryptContext
   
   db = get_database()
   session = db.get_db_session()
   pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
   
   admin_user = User(
       username='admin',
       email='admin@your-company.com',
       password_hash=pwd_context.hash('your-secure-password'),
       is_admin=True,
       is_active=True
   )
   session.add(admin_user)
   session.commit()
   print('Admin user created')
   "
   ```

2. **Download AI Models**:
   ```bash
   # Pull recommended models
   docker compose exec ollama ollama pull qwen2:1.5b
   docker compose exec ollama ollama pull nomic-embed-text
   
   # For better performance (larger models)
   docker compose exec ollama ollama pull qwen2:7b
   ```

---

## 5. Getting Started

### 5.1 First Login

1. **Access the Application**:
   - Open your browser to http://localhost:8501
   - You'll see the Docsmait login page

2. **Login with Admin Credentials**:
   - Username: `admin`
   - Password: (the password you set during setup)

3. **Initial Setup**:
   - Navigate to **Settings** to configure AI models
   - Go to **Projects** to create your first project
   - Visit **Templates** to see available templates

### 5.2 Creating Your First Project

1. **Navigate to Projects**:
   - Click **📋 Projects** in the sidebar

2. **Create New Project**:
   - Click **Create New Project**
   - Fill in project details:
     - **Name**: Your project name
     - **Description**: Project description
     - **Status**: Active
     - **Client**: Client name (optional)

3. **Project Settings**:
   - Configure compliance standards
   - Set project-specific parameters
   - Assign team members

### 5.3 Setting Up Knowledge Base

1. **Navigate to Knowledge Base**:
   - Click **📚 Knowledge Base** in the sidebar

2. **Create Collection**:
   - Enter collection name (e.g., "project-docs")
   - Click **Create Collection**

3. **Upload Documents**:
   - Select your collection
   - Click **Browse Files** or drag & drop
   - Supported formats: PDF, DOCX, TXT, MD, HTML
   - Click **Upload and Process**

4. **Test Knowledge Base**:
   - Use the chat interface to ask questions
   - The AI will search your documents and provide answers

### 5.4 Basic Workflow

1. **Document Management**:
   - Create/upload templates
   - Generate documents from templates
   - Review and approve documents
   - Track document versions

2. **Knowledge Search**:
   - Upload reference documents
   - Chat with AI about document contents
   - Get instant answers with source citations

3. **Audit & Compliance**:
   - Create audit plans
   - Track findings and corrective actions
   - Generate compliance reports
   - Manage audit schedules

---

## 6. Features Guide

### 6.1 Authentication & User Management

#### User Roles
- **Admin**: Full system access, user management
- **User**: Standard access to features
- **Viewer**: Read-only access

#### User Registration
1. Admin creates user accounts via **User Management**
2. Users receive login credentials
3. First-time login requires password change

#### Password Management
- Strong password requirements enforced
- Password reset via admin interface
- Session timeout configurable

### 6.2 Project Management

Docsmait organizes work around **Projects**, which serve as containers for documents, specifications, audits, and other artifacts.

#### Creating Projects
1. Navigate to **📋 Projects**
2. Click **Create New Project**
3. Fill in project details:
   - **Name**: Unique project identifier
   - **Description**: Project overview
   - **Status**: Active, On Hold, Completed
   - **Client**: Client organization (optional)
   - **Start/End Dates**: Project timeline

#### Project Features
- **Document Organization**: Group related documents
- **Team Management**: Assign users to projects
- **Compliance Tracking**: Map to regulatory standards
- **Progress Monitoring**: Track project milestones

#### Project Templates
- Standard project structures available
- Industry-specific templates (Medical, Automotive, etc.)
- Customizable project templates

### 6.3 Knowledge Base

The Knowledge Base uses RAG (Retrieval Augmented Generation) to provide AI-powered search and question-answering across your document library.

#### Collections
Collections organize documents by topic, project, or domain:

1. **Create Collection**:
   - Navigate to **📚 Knowledge Base**
   - Enter collection name
   - Click **Create Collection**

2. **Manage Collections**:
   - View document count and status
   - Delete empty collections
   - Configure collection settings

#### Document Upload & Processing

1. **Supported Formats**:
   - **PDF**: Extracts text and maintains formatting
   - **DOCX**: Microsoft Word documents  
   - **TXT/MD**: Plain text and Markdown
   - **HTML**: Web pages and formatted text

2. **Upload Process**:
   - Select target collection
   - Drag & drop or browse for files
   - Files are automatically chunked and vectorized
   - Processing status shown in real-time

3. **Bulk Upload**:
   - Upload multiple files simultaneously
   - Batch processing with progress indicators
   - Error handling and retry logic

#### AI Chat Interface

1. **Interactive Chat**:
   - Select collection for search scope
   - Type natural language questions
   - AI provides contextual answers with source citations

2. **Advanced Features**:
   - **Source Citations**: Links to original document sections
   - **Relevance Scoring**: Shows confidence in answers
   - **Context Preservation**: Maintains conversation context
   - **Multi-Document Synthesis**: Combines information from multiple sources

#### Search Optimization
- **Embedding Models**: Optimized for technical documents
- **Chunk Optimization**: Intelligent text segmentation
- **Semantic Search**: Finds conceptually related content
- **Hybrid Search**: Combines keyword and semantic matching

### 6.4 Template Management

Templates provide standardized document structures with rich markdown editing capabilities and approval workflows.

#### Template Types
- **Process Documents**: SOPs, policies, procedures
- **Forms**: Checklists, evaluation forms, reports
- **Reports**: Audit reports, test results, analysis documents
- **Compliance**: Regulatory submissions, documentation

#### Creating Templates

1. **Rich Markdown Editor**:
   - **Visual Toolbar**: Format text without markdown syntax
   - **Live Preview**: See rendered output in real-time  
   - **Advanced Features**: Tables, links, code blocks, lists
   - **Template Variables**: Use `[VARIABLE_NAME]` for placeholders

2. **Editor Features**:
   - **Formatting Tools**: Bold, italic, headers, lists
   - **Insert Functions**: Links, images, tables, code
   - **Advanced Options**: Strikethrough, superscript, subscript
   - **Keyboard Shortcuts**: Standard markdown shortcuts supported

3. **Template Metadata**:
   - **Name**: Unique template identifier
   - **Description**: Template purpose and usage
   - **Document Type**: Category classification
   - **Tags**: Searchable keywords
   - **Version**: Automatic versioning
   - **Status**: Draft, Active, Archived

#### Template Approval Workflow

1. **Approval Process**:
   - Submit template for approval
   - Designated approvers review content
   - Comments and feedback tracked
   - Approval required before activation

2. **Version Control**:
   - All template changes tracked
   - Previous versions maintained
   - Rollback capability
   - Change history logged

#### Bulk Template Import

For organizations with existing template libraries:

1. **Directory Structure**:
   ```
   /app/templates/
   ├── Reports/
   │   ├── quarterly-report.md      → Tags: ["Reports"]
   │   └── Financial/
   │       └── budget-analysis.md   → Tags: ["Reports,Financial"]
   ├── Forms/
   │   └── audit-checklist.md       → Tags: ["Forms"]
   └── meeting-notes.md             → Tags: ["General"]
   ```

2. **Import Process**:
   ```bash
   # Preview import (dry run)
   docker compose exec backend python import_templates.py --dry-run --verbose
   
   # Import templates
   docker compose exec backend python import_templates.py --verbose
   ```

3. **YAML Frontmatter Support**:
   ```markdown
   ---
   name: custom-template-name
   description: Detailed template description
   document_type: Process Documents
   tags: ["Custom", "Override"]
   version: 2.0
   status: active
   ---
   
   # Template Content
   Your template content here...
   ```

4. **Features**:
   - **Automatic Versioning**: `1.0` → `1.1` → `1.2`
   - **Tag Generation**: Directory structure becomes tags
   - **Duplicate Handling**: Updates existing templates
   - **Metadata Extraction**: From frontmatter, content, or filename

### 6.5 Document Management

Documents are created from templates and managed through their entire lifecycle.

#### Document Creation
1. **From Templates**:
   - Select approved template
   - Fill in template variables
   - Set document metadata
   - Generate initial document

2. **Direct Creation**:
   - Create documents without templates
   - Use rich markdown editor
   - Add custom metadata

#### Document Workflow
1. **Draft State**: Initial document creation
2. **Review Process**: Assign reviewers and collect feedback
3. **Approval**: Final approval before publication
4. **Active State**: Published and available for use
5. **Archive**: Retired documents maintained for records

#### Version Control
- **Automatic Versioning**: Major and minor version tracking
- **Change History**: Complete audit trail
- **Comparison**: Side-by-side version comparison
- **Rollback**: Restore previous versions

#### Review & Approval
- **Reviewer Assignment**: Assign specific reviewers
- **Review Tracking**: Monitor review status and progress
- **Comment System**: Inline comments and feedback
- **Approval Gates**: Required approvals before publication

### 6.6 Code Review Management

Integrates with Git repositories to manage code review processes.

#### Repository Integration
1. **Repository Connection**:
   - Connect to Git repositories (GitHub, GitLab, Bitbucket)
   - Configure webhook notifications
   - Set up authentication

2. **Pull Request Tracking**:
   - Automatic PR detection
   - Status tracking (Open, Merged, Closed)
   - Author and reviewer management

#### Review Process
1. **Review Assignment**:
   - Assign reviewers to pull requests
   - Track reviewer availability and workload
   - Send notification reminders

2. **Code Review Features**:
   - **Inline Comments**: Comment on specific code lines
   - **Review Status**: Approved, Changes Requested, Commented
   - **Review Summary**: Overall assessment and recommendations
   - **File-by-File Review**: Organized review by changed files

3. **Review Metrics**:
   - Review completion time
   - Number of review rounds
   - Comment resolution tracking
   - Code quality metrics

#### Integration Features
- **Multi-Repository Support**: Manage multiple code repositories
- **Branch Management**: Track feature branches and releases
- **Merge Conflict Detection**: Identify and resolve conflicts
- **Automated Testing Integration**: Link with CI/CD pipelines

### 6.7 Specification Management

Comprehensive requirements and risk management system supporting multiple safety standards.

#### Multi-Domain Support

1. **Automotive (ISO 26262)**:
   - **ASIL Levels**: A, B, C, D classification
   - **Functional Safety**: Safety goals and requirements
   - **Hazard Analysis**: HAZOP integration
   - **V-Model**: Requirements traceability

2. **Medical Devices (ISO 13485/14971)**:
   - **Risk Management**: ISO 14971 compliant
   - **Design Controls**: FDA 21 CFR Part 820
   - **Clinical Evaluation**: Efficacy and safety
   - **Post-Market Surveillance**: Ongoing monitoring

3. **Industrial (IEC 61508)**:
   - **SIL Levels**: 1, 2, 3, 4 classification
   - **Systematic Capability**: SC ratings
   - **Hardware Fault Tolerance**: Redundancy planning
   - **Software Safety**: SIL-rated software development

4. **Aviation (DO-178C)**:
   - **DAL Levels**: A, B, C, D, E classification
   - **Software Considerations**: Airworthiness requirements  
   - **Certification Basis**: Compliance demonstration
   - **Configuration Management**: Change control

#### Requirements Management

1. **System Requirements**:
   - **Unique IDs**: `REQ-[PROJECT]-YYYY-NNNN` format
   - **Traceability**: Parent-child relationships
   - **Verification Methods**: Test, inspection, analysis, demonstration
   - **Priority Levels**: Critical, High, Medium, Low

2. **Associated Hazards**:
   - **Risk IDs**: `RISK-[PROJECT]-YYYY-NNNN` format
   - **Risk Assessment**: Probability × Severity matrices
   - **Mitigation Strategies**: Risk reduction measures
   - **Residual Risk**: Post-mitigation risk levels

3. **Safety Measures**:
   - **Control Types**: Prevention, Detection, Mitigation
   - **Implementation Status**: Planned, Implemented, Verified
   - **Effectiveness Metrics**: Quantitative risk reduction
   - **Validation Requirements**: Proof of effectiveness

4. **Verification Activities**:
   - **Test Procedures**: Detailed test protocols
   - **Acceptance Criteria**: Pass/fail criteria
   - **Test Results**: Evidence collection
   - **Verification Status**: Complete/Incomplete tracking

#### Project-Specific Features
- **Project Selection**: All specifications tied to projects
- **Audit Trail**: Complete change history with timestamps
- **Unique ID Generation**: Automatic ID assignment per project
- **Cross-References**: Requirements-to-tests traceability
- **Impact Analysis**: Change impact assessment

#### Compliance Standards
- **Template Library**: Pre-configured templates for each standard
- **Checklist Integration**: Compliance verification checklists
- **Report Generation**: Automated compliance reports
- **Regulatory Mapping**: Map requirements to regulations

### 6.8 Audit Management

ISO 13485:2016 compliant audit management system for quality and compliance auditing.

#### Audit Planning

1. **Audit Creation**:
   - **Audit Types**: Internal, External, Supplier, Product
   - **Scope Definition**: Processes, departments, standards covered
   - **Scheduling**: Calendar integration and resource planning
   - **Team Assignment**: Lead auditor and audit team

2. **Audit Standards**:
   - **ISO 13485:2016**: Medical devices QMS
   - **ISO 14971:2019**: Risk management
   - **IEC 62304:2006**: Medical device software
   - **FDA 21 CFR Part 820**: US medical device regulations
   - **Custom Standards**: Organization-specific requirements

#### Audit Execution

1. **Finding Management**:
   - **Finding Types**: Non-conformity, Observation, Opportunity for Improvement
   - **Severity Levels**: Critical, Major, Minor
   - **Evidence Collection**: Photos, documents, witness statements
   - **Root Cause Analysis**: Systematic investigation

2. **Corrective Actions**:
   - **CAPA Integration**: Link to corrective/preventive action system
   - **Action Assignment**: Responsible parties and due dates
   - **Progress Tracking**: Status monitoring and updates
   - **Effectiveness Verification**: Follow-up verification

#### Audit Reporting
- **Standardized Reports**: ISO-compliant audit report templates
- **Executive Summary**: High-level findings and recommendations
- **Detailed Findings**: Comprehensive evidence and analysis
- **Action Plans**: Corrective action tracking
- **Trend Analysis**: Historical audit data analysis

#### Compliance Features
- **Regulatory Requirements**: Built-in compliance checklists
- **Documentation Standards**: Audit trail requirements
- **Training Records**: Auditor qualifications tracking
- **Certification Support**: External audit preparation

### 6.9 AI Configuration

Comprehensive AI model and performance management.

#### Model Management

1. **Available Models**:
   - **qwen2 Series**: 0.5b, 1.5b, 7b, 14b, 32b variants
   - **llama3 Models**: Various sizes and capabilities
   - **Specialized Models**: Domain-specific fine-tuned models
   - **Embedding Models**: nomic-embed-text, sentence-transformers

2. **Model Selection**:
   - **Performance vs. Speed**: Balance response quality and speed
   - **Resource Requirements**: Memory and compute considerations
   - **Language Support**: Multi-language capabilities
   - **Domain Specialization**: Technical, medical, legal expertise

#### Performance Optimization

1. **Response Settings**:
   - **Timeout Configuration**: Request timeout limits
   - **Response Length**: Maximum response size
   - **Context Window**: Available context size
   - **Temperature**: Response creativity control

2. **Hardware Optimization**:
   - **CPU Configuration**: Thread and memory allocation
   - **GPU Acceleration**: CUDA support for faster inference
   - **Memory Management**: Efficient model loading
   - **Concurrent Processing**: Multiple request handling

#### Advanced Features
- **Custom Prompts**: Domain-specific prompt templates
- **Response Caching**: Improve repeated query performance
- **Quality Metrics**: Response relevance scoring
- **Usage Analytics**: Model performance tracking

---

## 7. Advanced Features

### 7.1 API Integration

#### RESTful API
- **Complete API Coverage**: All features available via REST API
- **OpenAPI Documentation**: Interactive API documentation at `/docs`
- **Authentication**: JWT-based API authentication
- **Rate Limiting**: Configurable request rate limits

#### Webhook Support
- **Event Notifications**: Real-time event notifications
- **Custom Integrations**: Connect with external systems
- **Audit Logging**: Complete API usage tracking

### 7.2 Custom Extensions

#### Plugin Architecture
- **Custom Models**: Add domain-specific AI models
- **Workflow Extensions**: Custom approval workflows
- **Integration Connectors**: Third-party system integration
- **Report Templates**: Custom report formats

### 7.3 Enterprise Features

#### High Availability
- **Load Balancing**: Multiple instance deployment
- **Database Clustering**: PostgreSQL cluster support
- **Backup & Recovery**: Automated backup solutions
- **Monitoring**: Health checks and performance metrics

#### Security
- **Role-Based Access Control**: Granular permission management
- **Audit Logging**: Complete user activity tracking
- **Data Encryption**: At-rest and in-transit encryption
- **Compliance**: SOC 2, GDPR compliance features

---

## 8. Troubleshooting

### 8.1 Common Issues

#### Application Won't Start
1. **Check Docker Status**:
   ```bash
   docker --version
   docker compose version
   docker compose ps
   ```

2. **Port Conflicts**:
   ```bash
   # Check what's using your ports
   netstat -tulpn | grep :8501
   
   # Change ports in .env file
   FRONTEND_HOST_PORT=8502
   ```

3. **Insufficient Resources**:
   ```bash
   # Check Docker resources
   docker system df
   docker system prune -a  # Clean up unused resources
   ```

#### Database Connection Issues
1. **Database Not Ready**:
   ```bash
   # Check database logs
   docker compose logs postgres
   
   # Restart database
   docker compose restart postgres
   ```

2. **Connection String Issues**:
   ```bash
   # Test database connectivity
   docker compose exec backend python -c "from app.database_config import get_database; print('DB OK')"
   ```

#### AI Models Not Working
1. **Model Not Downloaded**:
   ```bash
   # Check available models
   docker compose exec ollama ollama list
   
   # Download missing models
   docker compose exec ollama ollama pull qwen2:1.5b
   ```

2. **Performance Issues**:
   ```bash
   # Check Ollama logs
   docker compose logs ollama
   
   # Increase memory allocation
   # Edit .env: OLLAMA_MEMORY_LIMIT=8G
   ```

#### Knowledge Base Issues
1. **Vector Database Problems**:
   ```bash
   # Check Qdrant status
   curl http://localhost:6335/collections
   
   # Restart vector database
   docker compose restart qdrant
   ```

2. **Upload Failures**:
   - Check file size limits (default 10MB)
   - Verify supported file formats
   - Check available disk space

### 8.2 Performance Issues

#### Slow AI Responses
1. **Model Optimization**:
   - Use smaller models for faster responses (qwen2:0.5b)
   - Enable GPU acceleration if available
   - Increase Ollama memory allocation

2. **Database Optimization**:
   ```bash
   # Database maintenance
   docker compose exec postgres psql -U docsmait_user -d docsmait -c "VACUUM ANALYZE;"
   ```

#### Memory Issues
1. **Container Resource Limits**:
   ```bash
   # Monitor resource usage
   docker stats
   
   # Adjust limits in .env
   BACKEND_MEMORY_LIMIT=4G
   OLLAMA_MEMORY_LIMIT=8G
   ```

### 8.3 Data Recovery

#### Backup Creation
```bash
# Database backup
docker compose exec postgres pg_dump -U docsmait_user docsmait > backup.sql

# Vector database backup
docker compose exec qdrant mkdir -p /backup
docker compose cp qdrant:/qdrant/storage /backup/qdrant_backup
```

#### Restore from Backup
```bash
# Restore database
docker compose exec postgres psql -U docsmait_user docsmait < backup.sql

# Restore vector database
docker compose cp /backup/qdrant_backup qdrant:/qdrant/storage
docker compose restart qdrant
```

---

## 9. API Reference

### 9.1 Authentication API

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

#### Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 9.2 Knowledge Base API

#### Upload Document
```http
POST /kb/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

collection_name: "my-collection"
file: @document.pdf
```

#### Query Knowledge Base
```http
POST /kb/chat
Authorization: Bearer {token}
Content-Type: application/json

{
  "message": "What are the safety requirements?",
  "collection_name": "safety-docs"
}
```

### 9.3 Template API

#### Create Template
```http
POST /templates
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Safety Report",
  "description": "Standard safety report template",
  "document_type": "Process Documents",
  "content": "# Safety Report\n\n## Overview\n...",
  "tags": ["safety", "reports"]
}
```

#### List Templates
```http
GET /templates?status=active&document_type=Process Documents
Authorization: Bearer {token}
```

---

## 10. Backup & Migration

### 10.1 Regular Backups

#### Automated Backup Script
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/docsmait_$DATE"

mkdir -p $BACKUP_DIR

# Database backup
docker compose exec postgres pg_dump -U docsmait_user docsmait > $BACKUP_DIR/database.sql

# Vector database backup
docker compose cp qdrant:/qdrant/storage $BACKUP_DIR/qdrant/

# Configuration backup
cp .env $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
```

#### Schedule with Cron
```bash
# Add to crontab (crontab -e)
0 2 * * * /path/to/backup.sh  # Daily at 2 AM
```

### 10.2 Migration Between Environments

#### Export Configuration
```bash
# Create migration package
docker compose exec backend python -c "
from app.database_config import get_database
from app.db_models import *
import json

db = get_database()
session = db.get_db_session()

# Export all templates
templates = session.query(Template).all()
template_data = []
for t in templates:
    template_data.append({
        'name': t.name,
        'description': t.description,
        'document_type': t.document_type,
        'content': t.content,
        'tags': t.tags,
        'version': t.version
    })

with open('/app/export_templates.json', 'w') as f:
    json.dump(template_data, f, indent=2)
"
```

#### Import to New Environment
```bash
# Import templates
docker compose exec backend python -c "
import json
from app.database_config import get_database
from app.db_models import *

with open('/app/export_templates.json') as f:
    templates = json.load(f)

db = get_database()
session = db.get_db_session()

for t_data in templates:
    template = Template(**t_data)
    template.created_by = 1  # Admin user
    session.add(template)

session.commit()
"
```

---

## 11. De-installation

### 11.1 Complete Removal

#### Stop and Remove Services
```bash
# Stop all services
docker compose down

# Remove all containers, networks, and volumes
docker compose down --volumes --remove-orphans

# Remove all Docker images
docker compose down --rmi all --volumes --remove-orphans
```

#### Clean Up System Resources
```bash
# Remove unused Docker resources
docker system prune -a --volumes

# Remove Docsmait directory
cd ..
rm -rf docsmait/
```

### 11.2 Partial Removal

#### Keep Data, Remove Application
```bash
# Stop services but keep volumes
docker compose down

# Remove only application images
docker rmi docsmait-backend docsmait-frontend
```

#### Data Export Before Removal
```bash
# Export all data before removal
./backup.sh

# Verify backup
ls -la /backups/
```

---

## 12. Support

### 12.1 Documentation Resources
- **User Manual**: This document
- **API Documentation**: http://localhost:8001/docs
- **Configuration Guide**: Environment variable reference
- **Troubleshooting Guide**: Common issues and solutions

### 12.2 Community Support
- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Community Q&A and best practices
- **Wiki**: Community-contributed documentation
- **Examples**: Sample configurations and use cases

### 12.3 Professional Support
- **Enterprise Support**: SLA-backed support packages
- **Training Services**: User and administrator training
- **Consulting Services**: Implementation and customization
- **Managed Hosting**: Cloud-hosted Docsmait instances

### 12.4 Contributing
- **Bug Reports**: Use GitHub issue tracker
- **Feature Requests**: Describe use cases and requirements  
- **Code Contributions**: Follow contribution guidelines
- **Documentation**: Help improve user documentation

---

## Appendix A: System Architecture

### Component Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │     FastAPI     │    │   PostgreSQL    │
│   Frontend      │◄──►│    Backend      │◄──►│   Database      │
│   (Port 8501)   │    │   (Port 8000)   │    │   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲
                                │
                ┌───────────────┼───────────────┐
                │               │               │
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │     Qdrant      │ │     Ollama      │ │     Docker      │
    │ Vector Database │ │  LLM Service    │ │  Orchestration  │
    │  (Port 6333)    │ │ (Port 11434)    │ │                 │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Data Flow
1. **User Interface**: Streamlit frontend provides web interface
2. **API Layer**: FastAPI handles business logic and data processing
3. **Database**: PostgreSQL stores structured data (users, documents, metadata)
4. **Vector Database**: Qdrant stores document embeddings for semantic search
5. **AI Engine**: Ollama provides LLM inference for chat and content generation

---

## Appendix B: Compliance Mapping

### ISO 13485:2016 Compliance
- **Document Control** (4.2.3): Template management and version control
- **Management Review** (5.6): Audit management and reporting
- **Risk Management** (7.1): Integrated risk assessment tools
- **Design Controls** (7.3): Requirements and verification management

### FDA 21 CFR Part 820 Mapping
- **Design Controls** (820.30): Requirements traceability
- **Document Controls** (820.40): Document management system  
- **Corrective and Preventive Actions** (820.100): CAPA workflow
- **Quality System Record** (820.186): Audit trail maintenance

---

**End of User Manual**

*For the most current version of this manual, please visit the Docsmait documentation repository.*