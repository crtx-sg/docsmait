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
   - [6.7 Design Record Management](#67-design-record-management)
   - [6.8 Records Management](#68-records-management)
   - [6.9 Audit Management](#69-audit-management)
   - [6.10 Training System](#610-training-system)
   - [6.11 AI Configuration](#611-ai-configuration)
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

1. **Password Requirements**:
   - Minimum 8 characters length (configurable)
   - Strong password recommendations
   - Password complexity validation

2. **Admin Password Reset**:
   - **Access**: Only super admins can reset user passwords
   - **Security**: Admins cannot reset their own passwords
   - **Process**:
     1. Go to **Settings** → **User Management** 
     2. Navigate to **"🔐 Reset User Password"** section
     3. Select user from dropdown (excludes current admin)
     4. Enter new password (minimum 8 characters)
     5. Confirm new password
     6. Click **"🔐 Reset Password"**
     7. Securely communicate new password to user

3. **Security Features**:
   - Password confirmation validation
   - User role identification in selection
   - Secure communication guidance
   - Success confirmation with next steps
   - Automatic UI refresh after successful reset

4. **Best Practices**:
   - Communicate passwords securely (email, in-person, secure messaging)
   - Encourage users to change password after reset
   - Password resets are logged for security auditing
   - Use strong, unique passwords for each reset

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

#### Backend Services Architecture

The knowledge base is powered by multiple integrated backend services that automatically build and maintain a searchable knowledge repository:

**Core Knowledge Base Service** (`backend/app/kb_service_pg.py`):
- **Purpose**: Central hub for all knowledge base operations using hybrid PostgreSQL + Qdrant vector database
- **Functions**: Document indexing, RAG-based querying, semantic search, collection management
- **Technology Stack**: PostgreSQL for metadata, Qdrant for vector embeddings, Ollama for LLM processing

**Integrated Backend Services**:

1. **Documents Service** (`documents_service.py`):
   - **Purpose**: Automatically indexes approved documents into project-specific collections
   - **KB Communication**: Adds documents to knowledge base when status changes to "approved"
   - **Collection Naming**: `project_name.replace(' ', '_').lower()`

2. **Templates Service** (`templates_service_pg.py`): 
   - **Purpose**: Manages document templates and indexes approved templates by document type
   - **KB Communication**: Creates collections for different template types (policies, procedures, etc.)
   - **Collection Naming**: `document_type.replace(' ', '_').lower()`

3. **Audit Service** (`audit_service.py`):
   - **Purpose**: Indexes closed audit findings to build organizational knowledge
   - **KB Communication**: Adds resolved findings to audit-specific collections

4. **AI Service** (`ai_service.py`):
   - **Purpose**: Provides RAG-powered chat and content generation using Ollama LLM
   - **KB Communication**: Queries knowledge base for context in AI responses

5. **Training System**:
   - **Purpose**: Generates learning content and assessments from knowledge base
   - **KB Communication**: Extracts content from multiple collections to create training materials

#### Database Architecture

**PostgreSQL Tables**:
- **KBCollection**: Collection metadata (id, name, description, created_by, document_count, total_size_bytes, tags, is_default)
- **KBDocument**: Document metadata only (id, filename, content_type, size_bytes, collection_name, chunk_count, upload_date, status)
- **KBQuery**: Query logging (id, query_text, collection_name, response_time_ms, timestamp)
- **KBConfig**: System configuration (key, value, updated_at)
- **KBDocumentTag**: Document tagging system (id, document_id, tag_name, tag_value)

**Qdrant Vector Database**:
- Stores document chunks as vectors with metadata payloads
- Each vector point contains: document_id, filename, chunk_index, text, collection
- Uses cosine distance for similarity calculations

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

3. **Automatic Collection Creation**:
   - **Project Collections**: Created automatically when documents are approved in projects
   - **Template Collections**: Created by document type when templates are approved
   - **Audit Collections**: Created for closed audit findings

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

3. **Automatic Processing**:
   - Documents are automatically added to knowledge base when approved
   - Templates are indexed when approved
   - Audit findings are added when closed
   - All processing is transparent to users

4. **RAG Implementation**:
   - **Embedding Generation**: Query text → Vector embedding (Ollama)
   - **Similarity Search**: Search Qdrant for relevant document chunks
   - **Context Assembly**: Combine retrieved chunks into context
   - **LLM Response**: Generate response using context + query (Ollama)
   - **Logging**: Store query metrics in PostgreSQL

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

3. **Performance Optimization**:
   - Configurable similarity search limits
   - Response time tracking
   - Chunk size optimization
   - Connection pooling for databases

#### Search Optimization
- **Embedding Models**: Optimized for technical documents (nomic-embed-text)
- **Chunk Optimization**: Intelligent text segmentation (default 1000 characters)
- **Semantic Search**: Finds conceptually related content
- **Hybrid Search**: Combines keyword and semantic matching
- **RAG Configuration**: 5 similar chunks retrieved by default

#### API Endpoints

**Core Endpoints**:
- `POST /kb/upload` - Upload documents
- `POST /kb/add_text` - Add text content
- `POST /kb/chat` - RAG-based chat
- `GET /kb/stats` - Statistics
- `POST /kb/reset` - Reset collections
- `POST /kb/collections` - Create collection
- `GET /kb/collections` - List collections
- `GET /kb/collections/{name}` - Get collection details
- `DELETE /kb/documents/{id}` - Delete document

The knowledge base automatically builds from approved organizational content to support compliance, training, and AI-assisted document workflows.

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

### 6.7 Design Record Management

Comprehensive design record system supporting lifecycle documentation for regulated industries with full traceability and compliance features.

#### Design Record Components

**Design Record** provides a complete lifecycle documentation system with the following modules:

1. **Requirements Management**:
   - **Interactive Tables**: st.dataframe with single-row selection for editing
   - **Full Editing**: Click any requirement to edit all fields in a comprehensive form
   - **Traceability Fields**: Parent requirements, child requirements, dependencies
   - **Verification Methods**: Test, inspection, analysis, demonstration
   - **Risk Level Integration**: Low, medium, high risk classification
   - **Compliance Standards**: Link to applicable regulatory standards

2. **Hazards & Risk Analysis**:
   - **Selectable Risk Tables**: Click to select and edit hazard details
   - **Risk Assessment**: Severity level, likelihood, and risk rating matrices
   - **Safety Integrity**: ASIL, SIL, DAL, Medical Risk Class support
   - **Mitigation Tracking**: Current controls and residual risk management
   - **Context Information**: Operational context and triggering conditions
   - **Stakeholder Impact**: Affected stakeholders and use error potential

3. **FMEA Analysis**:
   - **Failure Mode Management**: Design FMEA, Process FMEA, System FMEA, Software FMEA
   - **Element Analysis**: Element ID, function, and performance standards
   - **Hierarchy Levels**: Component, assembly, subsystem, system analysis
   - **Team Management**: FMEA team members and review status
   - **Analysis Levels**: Multiple analysis depth levels

4. **Design Artifacts**:
   - **Design Documentation**: Specifications, architecture, interfaces, detailed design
   - **Implementation Tracking**: Technology stack and design patterns
   - **Architecture Management**: Diagrams and interface definitions
   - **Safety Measures**: Safety barriers and fail-safe behaviors

5. **Test Artifacts**:
   - **Comprehensive Testing**: Unit, integration, system, safety, performance, security, clinical, usability, biocompatibility
   - **Execution Tracking**: Test status, results, and execution details
   - **Coverage Metrics**: Requirements coverage percentages
   - **Test Environment**: Environment specifications and configurations

6. **Traceability Management**:
   - **Requirements to Hazards**: Interactive traceability matrix
   - **Selectable Mapping**: Click to edit traceability relationships
   - **Multi-select Linking**: Link requirements to multiple hazards
   - **Rationale Documentation**: Traceability reasoning and justification
   - **Cross-references**: Bidirectional traceability links

7. **Compliance Management**:
   - **Standards Tracking**: ISO 13485, ISO 14971, IEC 62304, ISO 26262, FDA 21 CFR Part 820
   - **Compliance Status**: Compliant, partially compliant, non-compliant, not assessed
   - **Evidence Management**: Compliance evidence and references
   - **Review Tracking**: Last review dates and next review planning

8. **Post-Market Surveillance**:
   - **Adverse Events**: Event tracking with severity and investigation status
   - **Field Actions**: Corrective actions and effectiveness assessment
   - **Regulatory Reporting**: FDA and Notified Body notification tracking

#### Modern Interface Features

1. **Interactive Data Tables**:
   - **st.dataframe Implementation**: Modern table interface with selection
   - **Single-row Selection**: Click any row to select for editing
   - **Comprehensive Forms**: Full editing capability for all fields
   - **Real-time Updates**: Immediate data refresh after changes
   - **Consistent Heights**: 400px tables for optimal visibility

2. **Enhanced Export Capabilities**:
   - **Multiple Formats**: CSV, Excel, PDF, JSON, **Markdown**
   - **Markdown Tables**: Professional markdown table format for documentation
   - **Report Types**: Complete Design Record, Requirements Traceability, Risk Management Summary, FMEA Analysis, Compliance Evidence, Test Execution Summary, Post-Market Surveillance, Regulatory Submission Package
   - **Filtered Exports**: Date range and status filtering
   - **Metadata Inclusion**: Complete audit trail in exports

3. **Knowledge Base Integration**:
   - **Intelligent Updates**: Design record data integration with knowledge base
   - **Project Summaries**: Automated project data aggregation
   - **Multi-endpoint Support**: Robust API endpoint detection
   - **Graceful Degradation**: Simulated success when backend unavailable

#### Multi-Domain Support

1. **Medical Devices (ISO 13485/14971)**:
   - **Risk Management**: ISO 14971 compliant risk analysis
   - **Design Controls**: FDA 21 CFR Part 820 compliance
   - **Clinical Evaluation**: Efficacy and safety documentation
   - **Post-Market Surveillance**: Ongoing monitoring and reporting

2. **Automotive (ISO 26262)**:
   - **ASIL Levels**: A, B, C, D functional safety classification
   - **Functional Safety**: Safety goals and requirements management
   - **Hazard Analysis**: HAZOP integration and analysis
   - **V-Model**: Complete requirements to verification traceability

3. **Industrial (IEC 61508)**:
   - **SIL Levels**: 1, 2, 3, 4 safety integrity classification
   - **Systematic Capability**: SC ratings and assessments
   - **Hardware Fault Tolerance**: Redundancy planning and analysis
   - **Software Safety**: SIL-rated software development lifecycle

4. **Aviation (DO-178C)**:
   - **DAL Levels**: A, B, C, D, E design assurance classification
   - **Software Considerations**: Airworthiness requirements compliance
   - **Certification Basis**: Compliance demonstration and evidence
   - **Configuration Management**: Change control and traceability

#### Workflow Benefits
- **Streamlined Editing**: No more expanding/collapsing - direct table selection
- **Comprehensive Forms**: All fields editable in logical groupings
- **Visual Consistency**: Uniform interface across all record types
- **Professional Export**: Publication-ready markdown documentation
- **Audit Trail**: Complete change history and version control

### 6.8 Records Management

Comprehensive ISO 13485 compliant records management system for regulatory compliance and quality assurance.

#### Records Categories

**Records Management** provides structured tracking of all quality and compliance records with interactive editing capabilities:

1. **Supplier Management**:
   - **Interactive Supplier Tables**: Click to select and edit supplier details
   - **Performance Tracking**: Performance ratings, quality ratings, on-time delivery rates
   - **Risk Assessment**: Risk level classification and audit scheduling
   - **Certification Management**: Certification status and contract details
   - **Contact Management**: Complete supplier contact information
   - **Compliance Status**: Approval status tracking (Pending, Approved, Conditional, Rejected)

2. **Parts & Inventory**:
   - **Inventory Tables**: Selectable parts with comprehensive editing
   - **UDI Tracking**: Unique Device Identification and lot/serial number management
   - **Stock Management**: Current stock, minimum levels, and location tracking
   - **Expiration Management**: Expiration dates and received dates
   - **Status Control**: In Stock, Quarantined, Expired, Disposed status tracking
   - **Cost Tracking**: Unit costs and inventory valuations

3. **Lab Equipment**:
   - **Equipment Tables**: Calibration and maintenance tracking
   - **Calibration Management**: Last calibration, next calibration, frequency tracking
   - **Status Monitoring**: Calibrated, Due, Overdue, Out of Service status
   - **Technician Assignment**: Calibration technician and responsibility tracking
   - **Standards Documentation**: Calibration standards and compliance notes
   - **Results Recording**: Calibration results and adjustment tracking

4. **Customer Complaints**:
   - **Complaint Tables**: Complaint tracking with MDR reportability
   - **Investigation Management**: Investigation status and root cause analysis
   - **Product Traceability**: Product ID, lot number, and serial number linking
   - **Response Tracking**: Response dates and corrective action management
   - **MDR Compliance**: Medical Device Reporting compliance tracking
   - **Resolution Documentation**: Complete complaint resolution workflow

5. **Non-Conformances**:
   - **NC Tables**: Non-conformance tracking and management
   - **Severity Classification**: Critical, Major, Minor non-conformance levels
   - **Risk Assessment**: Risk level determination and impact analysis
   - **Disposition Management**: Use As Is, Rework, Scrap, Return decisions
   - **CAPA Integration**: Corrective and Preventive Action linkage
   - **Status Tracking**: Open, In Progress, Closed status management

#### Interface Features

1. **Modern Table Interface**:
   - **2:3 Width Ratio**: Optimized layout with 2:3 ratio between dataframe and add form
   - **st.dataframe Implementation**: Professional table interface with selection
   - **Single-row Selection**: Click any row for comprehensive editing
   - **Consistent Heights**: 400px tables for optimal data visibility
   - **Real-time Updates**: Immediate refresh after data changes

2. **Comprehensive Editing**:
   - **Full Field Access**: All table columns and related fields editable
   - **Form Validation**: Data type validation and required field checking
   - **Dropdown Controls**: Standardized values for consistency
   - **Date Management**: Proper date field handling and validation
   - **Status Workflows**: Controlled status transitions and approvals

3. **Filtering and Search**:
   - **Advanced Filters**: Status, category, date range filtering
   - **Search Capability**: Text search across all record fields
   - **Quick Access**: Streamlined record location and selection

#### Export & Reporting

**Dedicated Export Tab** provides comprehensive data export functionality for all record categories:

1. **Export Categories**:
   - **🏢 Supplier Management**: Complete supplier data with performance metrics
   - **📦 Parts & Inventory**: Inventory data with UDI and stock information
   - **🔬 Lab Equipment**: Calibration records and equipment status
   - **😟 Customer Complaints**: Complaint data with investigation details
   - **⚠️ Non-Conformances**: NC records with CAPA linkage

2. **Export Formats**:
   - **CSV Format**: Structured data suitable for Excel, databases, and analysis
   - **Markdown Format**: Human-readable reports with detailed formatting
   - **Automatic Timestamping**: All exports include timestamp in filename
   - **Version Control**: Timestamped filenames prevent overwrites

3. **Export Features**:
   - **Category Selection**: Choose specific record type to export
   - **Format Selection**: Select CSV or Markdown format
   - **Complete Data**: All fields and metadata included
   - **Text Truncation**: Long text fields truncated in Markdown for readability
   - **Download Management**: Direct browser download with proper MIME types

4. **Export Process**:
   1. Go to **Records** → **📥 Export** tab
   2. Select record category from dropdown
   3. Choose export format (CSV/Markdown)
   4. Click **"📥 Export [Category] ([Format])"**
   5. File downloads automatically with timestamped filename

#### Compliance Features
- **ISO 13485 Alignment**: Full compliance with quality management requirements
- **FDA 21 CFR Part 820**: Design controls and record keeping compliance
- **Audit Trail**: Complete change history and version tracking
- **Document Control**: Controlled record creation and approval processes
- **Regulatory Reporting**: Automated compliance report generation

### 6.9 Audit Management

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

**Enhanced Reporting System** with comprehensive export capabilities:

1. **Report Generation**:
   - **Audit Selection**: Choose specific audit from dropdown list
   - **Format Options**: CSV and Markdown export formats
   - **Comprehensive Data**: Complete audit, findings, and corrective actions
   - **Standardized Reports**: ISO-compliant audit report templates

2. **Report Formats**:
   - **CSV Format**: Structured data with all audit details, findings, and corrective actions
     - **Audit Details**: Audit metadata, scope, standards, and team information
     - **Findings Data**: Complete findings with descriptions, evidence, and severity
     - **Corrective Actions**: Linked CAPA items with responsible parties and due dates
     - **Data Analysis**: Suitable for Excel analysis and database import

   - **Markdown Format**: Professional, human-readable audit reports
     - **Executive Summary**: Audit overview with key metrics and findings count
     - **Detailed Findings**: Structured findings with evidence and root cause analysis
     - **Corrective Actions**: Organized action items with assignments and timelines
     - **Performance Analysis**: Trend analysis and compliance assessment

3. **Report Features**:
   - **Complete Coverage**: All audit data including header, findings, and actions
   - **Timestamped Files**: Automatic filename generation with audit number and timestamp
   - **Direct Download**: Browser-based download with proper file types
   - **Empty Audit Support**: Handles audits with no findings gracefully

4. **Report Access**:
   1. Go to **Audit Management** → **Reports** tab
   2. Select audit from **"Select Audit for Report"** dropdown
   3. Choose report format (CSV or Markdown)
   4. Click **"📥 Download Audit Report ([Format])"**
   5. File downloads automatically as `audit_report_[audit_number]_[timestamp].[ext]`

5. **Legacy Features**:
   - **Executive Summary**: High-level findings and recommendations
   - **Detailed Analysis**: Comprehensive evidence documentation
   - **Action Tracking**: Corrective action progress monitoring
   - **Trend Analysis**: Historical audit data analysis

#### Compliance Features
- **Regulatory Requirements**: Built-in compliance checklists
- **Documentation Standards**: Audit trail requirements
- **Training Records**: Auditor qualifications tracking
- **Certification Support**: External audit preparation

### 6.10 Training System

Comprehensive learning and assessment platform leveraging the knowledge base for continuous education and skill development.

#### Learning Content Generation

1. **Topic Selection**:
   - **Document Types**: Planning Documents, Process Documents, Specifications, Records, Templates, Policies, Manuals, SOPs, Work Instructions, Quality Plans, Risk Assessments, Test Reports, Audit Reports
   - **Multi-Topic Learning**: Select multiple topics for comprehensive learning
   - **Knowledge Base Integration**: Content generated from uploaded documents and templates

2. **Learning Content Features**:
   - **AI-Generated Content**: Comprehensive learning materials from knowledge base
   - **Source Document Tracking**: References to source documents for deeper learning
   - **Structured Format**: Well-organized content with clear sections and examples

#### Assessment System

1. **Assessment Configuration**:
   - **Question Range**: 5-50 questions per assessment (default: 20)
   - **True/False Format**: Simple, clear question format
   - **Pass Threshold**: 80% score required to pass (configurable)
   - **Topic-Based**: Questions generated from selected learning topics

2. **Assessment Features**:
   - **Immediate Feedback**: Results displayed immediately after submission
   - **Detailed Analysis**: Question-by-question review with correct answers
   - **Performance Tracking**: Progress tracking across multiple assessments
   - **Pass/Fail Indicator**: Clear success/failure indication with improvement guidance

#### Training Results & Analytics

1. **Performance Metrics**:
   - **Total Assessments**: Complete assessment history
   - **Average Score**: Overall performance tracking
   - **Pass Rate**: Success rate calculation
   - **Recent Trends**: Performance improvement/decline analysis

2. **Training Reports**:
   - **CSV Export**: Structured data for analysis and record-keeping
   - **Markdown Reports**: Human-readable comprehensive reports
   - **Assessment History**: Complete record with dates, scores, and outcomes
   - **Performance Analysis**: Trends and document type performance breakdown

3. **Report Features**:
   - **Always Available**: Download functionality available even with no assessments
   - **Timestamped Files**: Automatic filename generation with timestamps
   - **User-Specific**: Individual training records per user
   - **Comprehensive Data**: Includes summary metrics, detailed history, and analysis

#### Training Workflow

1. **Learning Phase**:
   - Select document types for learning
   - Generate comprehensive learning content
   - Review AI-generated materials with source references
   - Access structured learning with examples and explanations

2. **Assessment Phase**:
   - Configure assessment parameters (questions, topics)
   - Take True/False assessments
   - Receive immediate feedback and results
   - Review detailed question analysis

3. **Progress Tracking**:
   - Monitor performance across assessments
   - Track improvement over time
   - Analyze performance by document type
   - Generate reports for compliance and records

### 6.11 AI Configuration

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

## 10. System Management

### 10.1 Data Management

#### Data Reset and Cleanup

**Complete System Reset**:
```bash
# Stop all services
docker compose down

# Remove all data volumes (WARNING: This deletes ALL data)
docker volume prune -f
docker system prune -f

# Restart services (will reinitialize empty databases)
docker compose up -d
```

**Selective Data Reset**:
```bash
# Reset only PostgreSQL database
docker compose down
docker volume rm docsmait_postgres_data
docker compose up -d

# Reset only Vector database
docker compose down  
docker volume rm docsmait_qdrant_storage
docker compose up -d

# Reset only Ollama models
docker compose down
docker volume rm docsmait_ollama_data
docker compose up -d
```

#### Template Management

**Bulk Template Upload**:
```bash
# 1. Prepare templates in JSON format
cat > templates.json << 'EOF'
[
  {
    "name": "SOP Template",
    "description": "Standard Operating Procedure Template",
    "document_type": "SOP",
    "content": "# SOP: [Title]\n\n## Purpose\n\n## Scope\n\n## Procedure\n\n",
    "tags": ["sop", "procedure"],
    "version": "1.0"
  }
]
EOF

# 2. Copy templates to container
docker cp templates.json docsmait-backend:/app/

# 3. Import templates
docker compose exec backend python -c "
import json
from app.database_config import get_database
from app.db_models import Template

with open('/app/templates.json') as f:
    templates = json.load(f)

db = get_database()
session = db.get_db_session()

for t_data in templates:
    template = Template(**t_data)
    template.created_by = 1  # Admin user
    session.add(template)
    
session.commit()
print(f'Imported {len(templates)} templates')
"
```

**Template Export for Backup**:
```bash
# Export all templates
docker compose exec backend python -c "
from app.database_config import get_database
from app.db_models import Template
import json

db = get_database()
session = db.get_db_session()

templates = session.query(Template).all()
template_data = []
for t in templates:
    template_data.append({
        'name': t.name,
        'description': t.description,
        'document_type': t.document_type,
        'content': t.content,
        'tags': t.tags,
        'version': t.version,
        'status': t.status
    })

with open('/app/templates_backup.json', 'w') as f:
    json.dump(template_data, f, indent=2)
    
print(f'Exported {len(template_data)} templates')
"

# Copy backup file to host
docker cp docsmait-backend:/app/templates_backup.json ./
```

### 10.2 Backup & Migration

#### Comprehensive Backup System

**Complete System Backup Script**:
```bash
#!/bin/bash
# comprehensive_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/docsmait_$DATE"

echo "Starting comprehensive backup..."
mkdir -p $BACKUP_DIR

# 1. Database backup (PostgreSQL)
echo "Backing up PostgreSQL database..."
docker compose exec -T postgres pg_dump -U docsmait_user docsmait > $BACKUP_DIR/database.sql

# 2. Vector database backup (Qdrant)
echo "Backing up Qdrant vector database..."
docker compose cp qdrant:/qdrant/storage $BACKUP_DIR/qdrant/

# 3. Ollama models backup
echo "Backing up Ollama models..."
docker compose cp ollama:/root/.ollama $BACKUP_DIR/ollama/

# 4. Configuration backup
echo "Backing up configuration..."
cp .env $BACKUP_DIR/ 2>/dev/null || echo "Warning: .env file not found"
cp docker-compose.yml $BACKUP_DIR/
cp docker-compose.override.yml $BACKUP_DIR/ 2>/dev/null || echo "Override file not found"

# 5. Template backup
echo "Backing up templates..."
docker compose exec -T backend python -c "
from app.database_config import get_database
from app.db_models import Template
import json

db = get_database()
session = db.get_db_session()

templates = session.query(Template).all()
template_data = []
for t in templates:
    template_data.append({
        'name': t.name,
        'description': t.description,
        'document_type': t.document_type,
        'content': t.content,
        'tags': t.tags,
        'version': t.version,
        'status': t.status
    })

with open('/app/templates_backup.json', 'w') as f:
    json.dump(template_data, f, indent=2)
    
print(f'Exported {len(template_data)} templates')
" && docker cp docsmait-backend:/app/templates_backup.json $BACKUP_DIR/

# 6. Create backup metadata
echo "Creating backup metadata..."
cat > $BACKUP_DIR/backup_info.txt << EOF
Docsmait Backup Information
==========================
Backup Date: $(date)
Backup Directory: $BACKUP_DIR
System: $(uname -a)
Docker Compose Version: $(docker compose version --short)

Contents:
- database.sql: PostgreSQL database dump
- qdrant/: Vector database storage
- ollama/: AI models and data
- templates_backup.json: Template export
- .env: Environment configuration
- docker-compose.yml: Service configuration

Restore Command:
./restore.sh $BACKUP_DIR
EOF

# 7. Create compressed archive
echo "Creating compressed archive..."
cd /backups
tar -czf "docsmait_backup_$DATE.tar.gz" "docsmait_$DATE/"

echo "Backup completed successfully!"
echo "Backup location: $BACKUP_DIR"
echo "Archive: /backups/docsmait_backup_$DATE.tar.gz"
echo "Size: $(du -sh $BACKUP_DIR | cut -f1)"
```

**System Restore Script**:
```bash
#!/bin/bash
# restore.sh

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_directory>"
    echo "Example: $0 /backups/docsmait_20240315_143022"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory $BACKUP_DIR does not exist"
    exit 1
fi

echo "Starting system restore from: $BACKUP_DIR"
echo "WARNING: This will overwrite existing data!"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 1
fi

# Stop services
echo "Stopping services..."
docker compose down

# 1. Restore PostgreSQL database
if [ -f "$BACKUP_DIR/database.sql" ]; then
    echo "Restoring PostgreSQL database..."
    docker compose up -d postgres
    sleep 10  # Wait for postgres to start
    docker compose exec -T postgres psql -U docsmait_user -d docsmait -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    docker compose exec -T postgres psql -U docsmait_user -d docsmait < "$BACKUP_DIR/database.sql"
    docker compose down
fi

# 2. Restore Qdrant vector database
if [ -d "$BACKUP_DIR/qdrant" ]; then
    echo "Restoring Qdrant vector database..."
    docker volume rm docsmait_qdrant_storage 2>/dev/null || true
    docker compose up -d qdrant
    sleep 5
    docker cp "$BACKUP_DIR/qdrant/." qdrant:/qdrant/storage/
    docker compose down
fi

# 3. Restore Ollama models
if [ -d "$BACKUP_DIR/ollama" ]; then
    echo "Restoring Ollama models..."
    docker volume rm docsmait_ollama_data 2>/dev/null || true
    docker compose up -d ollama
    sleep 5
    docker cp "$BACKUP_DIR/ollama/." ollama:/root/.ollama/
    docker compose down
fi

# 4. Restore configuration files
echo "Restoring configuration..."
[ -f "$BACKUP_DIR/.env" ] && cp "$BACKUP_DIR/.env" ./
[ -f "$BACKUP_DIR/docker-compose.yml" ] && cp "$BACKUP_DIR/docker-compose.yml" ./
[ -f "$BACKUP_DIR/docker-compose.override.yml" ] && cp "$BACKUP_DIR/docker-compose.override.yml" ./

# 5. Start all services
echo "Starting all services..."
docker compose up -d

# 6. Wait for services and restore templates
echo "Waiting for services to start..."
sleep 30

if [ -f "$BACKUP_DIR/templates_backup.json" ]; then
    echo "Restoring templates..."
    docker cp "$BACKUP_DIR/templates_backup.json" docsmait-backend:/app/
    docker compose exec backend python -c "
import json
from app.database_config import get_database
from app.db_models import Template

with open('/app/templates_backup.json') as f:
    templates = json.load(f)

db = get_database()
session = db.get_db_session()

for t_data in templates:
    template = Template(**t_data)
    template.created_by = 1  # Admin user
    session.add(template)
    
session.commit()
print(f'Restored {len(templates)} templates')
"
fi

echo "Restore completed successfully!"
echo "Services should be available at:"
echo "- Frontend: http://localhost:8501"
echo "- Backend API: http://localhost:8001"
```

#### Automated Backup Scheduling
```bash
# Add to crontab (crontab -e)
0 2 * * * /path/to/comprehensive_backup.sh  # Daily at 2 AM
0 14 * * 0 /path/to/comprehensive_backup.sh  # Weekly on Sunday at 2 PM

# Make scripts executable
chmod +x /path/to/comprehensive_backup.sh
chmod +x /path/to/restore.sh
```

### 10.3 Migration Between Environments

#### Full Environment Migration
```bash
# 1. Create backup on source environment
./comprehensive_backup.sh

# 2. Transfer backup to target environment
scp /backups/docsmait_backup_*.tar.gz user@target-server:/backups/

# 3. Extract and restore on target
cd /backups
tar -xzf docsmait_backup_*.tar.gz
./restore.sh /backups/docsmait_*
```

#### Selective Migration (Templates Only)
```bash
# Export templates from source
docker compose exec backend python -c "
from app.database_config import get_database
from app.db_models import Template
import json

db = get_database()
session = db.get_db_session()

templates = session.query(Template).all()
template_data = []
for t in templates:
    template_data.append({
        'name': t.name,
        'description': t.description,
        'document_type': t.document_type,
        'content': t.content,
        'tags': t.tags,
        'version': t.version,
        'status': t.status
    })

with open('/app/migration_templates.json', 'w') as f:
    json.dump(template_data, f, indent=2)
"

# Copy to target environment
docker cp docsmait-backend:/app/migration_templates.json ./
scp migration_templates.json user@target-server:~/

# Import on target environment
docker cp migration_templates.json docsmait-backend:/app/
docker compose exec backend python -c "
import json
from app.database_config import get_database
from app.db_models import Template

with open('/app/migration_templates.json') as f:
    templates = json.load(f)

db = get_database()
session = db.get_db_session()

for t_data in templates:
    template = Template(**t_data)
    template.created_by = 1  # Admin user
    session.add(template)

session.commit()
print(f'Migrated {len(templates)} templates')
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