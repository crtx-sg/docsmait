# Help - Docsmait Feature Documentation
import streamlit as st
from auth_utils import require_auth, setup_authenticated_sidebar

# Configure page
st.set_page_config(
    page_title="Docsmait - Help",
    page_icon="❓",
    layout="wide"
)

require_auth()
setup_authenticated_sidebar()

st.title("Help & Documentation 📚")

# Help navigation
help_tabs = st.tabs([
    "🏠 Getting Started", 
    "📋 Projects", 
    "🔬 Design Record", 
    "📋 Records Management",
    "📊 Activity Logs",
    "📄 Templates", 
    "📁 Documents", 
    "💻 Code", 
    "🔍 Reviews", 
    "📊 Audit", 
    "🎓 Training", 
    "📚 Knowledge Base"
])

# Getting Started Tab
with help_tabs[0]:
    st.markdown("## 🏠 Getting Started with Docsmait")
    
    st.markdown("### Welcome to Docsmait!")
    st.markdown("""
    Docsmait is a comprehensive AI-powered document, training, and compliance management system designed for 
    organizations working with regulated products, especially in medical device, automotive, and industrial sectors.
    """)
    
    st.markdown("### 🎯 Key Features Overview")
    feature_cols = st.columns(2)
    
    with feature_cols[0]:
        st.markdown("""
        **📋 Project Management**
        - Create and manage multiple projects
        - Track project timelines and milestones
        - Monitor project health metrics
        
        **🔬 Design Record System**
        - Requirements management with traceability
        - Risk and hazard analysis (FMEA)
        - Design artifacts and documentation
        - Test management and validation
        - Interactive traceability matrix
        - Compliance tracking and evidence management
        - Professional exports (Markdown, CSV, Excel, PDF, JSON)
        
        **📋 Records Management (ISO 13485)**
        - Supplier performance and quality tracking
        - Parts inventory with UDI and lot tracking
        - Lab equipment calibration management
        - Customer complaints and MDR reporting
        - Non-conformances with CAPA integration
        
        **📄 Template Management**
        - Pre-built document templates
        - Custom template creation
        - Version control and approval workflows
        """)
    
    with feature_cols[1]:
        st.markdown("""
        **📁 Document Management**
        - Centralized document repository
        - Version control and change tracking
        - Document approval workflows
        - Search and categorization
        
        **💻 Code Management**
        - Source code repository integration
        - Code review and approval processes
        - Version control and branching
        
        **🔍 Review System**
        - Peer review workflows
        - Approval tracking and signatures
        - Review history and audit trails
        
        **📊 Activity Logging & Audit Trail**
        - Comprehensive user activity tracking
        - Tamper-proof audit logs with 5+ year retention
        - IP address and user agent tracking
        - Export capabilities for external audits
        
        **🎯 Interactive Interface Features**
        - st.dataframe tables with single-row selection
        - Comprehensive editing forms for all fields
        - Real-time data updates
        - Consistent 400px table heights for optimal visibility
        """)
    
    st.markdown("### 🚀 Quick Start Guide")
    st.markdown("""
    1. **Start with Projects**: Navigate to Projects and create your first project
    2. **Set up Design Record**: Use Design Record to manage requirements and risks
    3. **Configure Records Management**: Set up suppliers, parts inventory, and lab equipment
    4. **Monitor Activity**: Use Activity Logs to track all system activities
    5. **Create Templates**: Set up document templates for consistency
    6. **Upload Documents**: Add your existing documents to the system
    7. **Enable Reviews**: Set up review workflows for quality control
    8. **Export Data**: Use the professional export features for regulatory submissions
    """)

# Projects Tab
with help_tabs[1]:
    st.markdown("## 📋 Projects Module")
    
    st.markdown("### Overview")
    st.markdown("""
    The Projects module is the central hub for organizing all your work. Each project contains 
    its own set of requirements, risks, documents, and deliverables.
    """)
    
    st.markdown("### 🎯 Key Features")
    st.markdown("""
    - **Project Creation**: Create new projects with custom settings
    - **Project Dashboard**: Monitor project health and progress
    - **Timeline Management**: Track milestones and deadlines
    - **Team Collaboration**: Assign team members and roles
    - **Progress Tracking**: Monitor completion status across all modules
    """)
    
    st.markdown("### 📖 How to Use")
    st.markdown("""
    1. **Create Project**: Click "New Project" and fill in project details
    2. **Configure Settings**: Set project parameters, standards, and team members
    3. **Monitor Progress**: Use the dashboard to track project health
    4. **View Timeline**: Check upcoming deadlines and milestones
    5. **Generate Reports**: Export project summaries and status reports
    """)

# Design Record Tab
with help_tabs[2]:
    st.markdown("## 🔬 Design Record System")
    
    st.markdown("### Overview")
    st.markdown("""
    The Design Record system provides comprehensive lifecycle management supporting 
    medical device, automotive, and industrial safety standards including ISO 13485, 
    ISO 14971, IEC 62304, and ISO 26262.
    """)
    
    design_subtabs = st.tabs([
        "📋 Requirements", 
        "⚠️ Hazards & Risks", 
        "🛠️ FMEA", 
        "🏗️ Design", 
        "🧪 Testing", 
        "📊 Traceability", 
        "📑 Compliance", 
        "📈 Post-Market"
    ])
    
    with design_subtabs[0]:
        st.markdown("### 📋 Requirements Management")
        st.markdown("""
        **Purpose**: Manage functional, safety, performance, and regulatory requirements
        
        **Key Features**:
        - Requirement creation and editing
        - Categorization by type and priority
        - Approval workflows and version control
        - Traceability to design and test items
        - Requirements analytics and reporting
        
        **Supported Types**: Functional, Safety, Performance, Usability, Security, Regulatory
        """)
    
    with design_subtabs[1]:
        st.markdown("### ⚠️ Hazards & Risk Management")
        st.markdown("""
        **Purpose**: Identify and manage safety hazards per ISO 14971 and related standards
        
        **Key Features**:
        - Hazard identification and analysis
        - Risk assessment with severity and probability
        - Risk control measures and mitigation
        - Medical device specific risk categories
        - ASIL/SIL safety integrity levels
        
        **Standards Supported**: ISO 14971, ISO 13485, ASIL (Automotive), SIL (Industrial)
        """)
    
    with design_subtabs[2]:
        st.markdown("### 🛠️ FMEA Analysis")
        st.markdown("""
        **Purpose**: Failure Mode and Effects Analysis per IEC 60812:2018
        
        **Key Features**:
        - Design, Process, System, and Software FMEA
        - RPN (Risk Priority Number) calculation
        - Corrective actions tracking
        - FMEA distribution analytics
        
        **FMEA Types**: Design FMEA (DFMEA), Process FMEA (PFMEA), System FMEA, Software FMEA
        """)
    
    with design_subtabs[3]:
        st.markdown("### 🏗️ Design Artifacts")
        st.markdown("""
        **Purpose**: Manage design documentation with safety measures
        
        **Key Features**:
        - Design document management
        - Safety measures configuration
        - Medical device design controls (FDA/ISO 13485)
        - Design input/output documentation
        - Design review and verification records
        """)
    
    with design_subtabs[4]:
        st.markdown("### 🧪 Test Artifacts")
        st.markdown("""
        **Purpose**: Comprehensive testing documentation and results
        
        **Key Features**:
        - Test case management and execution
        - Medical device testing (Clinical, Usability, Biocompatibility)
        - EMC and electrical safety testing
        - Test coverage analytics
        - Verification and validation protocols
        """)
    
    with design_subtabs[5]:
        st.markdown("### 📊 Traceability Matrix")
        st.markdown("""
        **Purpose**: Complete lifecycle traceability from requirements through post-market
        
        **Key Features**:
        - Requirements to hazards mapping
        - Bidirectional traceability
        - Impact analysis for changes
        - Coverage reporting and gap analysis
        - Traceability link creation and management
        """)
    
    with design_subtabs[6]:
        st.markdown("### 📑 Compliance Standards")
        st.markdown("""
        **Purpose**: Standards compliance tracking and audit evidence management
        
        **Key Features**:
        - Multi-standard compliance tracking
        - Audit findings management
        - Evidence documentation matrix
        - Compliance gap analysis
        - Regulatory submission support
        
        **Standards**: ISO 13485, ISO 14971, IEC 62304, ISO 26262, FDA 21 CFR Part 820
        """)
    
    with design_subtabs[7]:
        st.markdown("### 📈 Post-Market Surveillance")
        st.markdown("""
        **Purpose**: Post-market monitoring and adverse events tracking
        
        **Key Features**:
        - Adverse events management
        - Customer feedback tracking
        - Field safety corrective actions
        - Surveillance reports and regulatory notifications
        - Risk assessment updates based on field data
        - **NEW**: Update Knowledge Base function in Export tab
        - Comprehensive JSON payload generation for knowledge base integration
        
        **Modern Interface Features**:
        - Interactive st.dataframe tables with single-row selection
        - Consistent 400px table heights for optimal visibility
        - Real-time data updates after changes
        - Professional Markdown table export for documentation
        """)
    
    st.markdown("### 🧠 Export & Knowledge Base Integration")
    st.markdown("""
    **NEW FEATURE**: The Export tab now includes a powerful "Update Knowledge Base" function that:
    - Generates comprehensive JSON payloads including all report options
    - Integrates project data from requirements, hazards, FMEA, design, and test artifacts
    - Supports vectorization and embedding creation for AI-powered search
    - Enables cross-referencing and semantic search capabilities
    - Preserves data relationships and creates comprehensive knowledge graphs
    """)
    
    st.markdown("### 📊 Professional Export Capabilities")
    export_cols = st.columns(2)
    
    with export_cols[0]:
        st.markdown("""
        **Export Formats Available**:
        - **CSV**: Standard comma-separated values
        - **Excel**: Professional spreadsheet format
        - **PDF**: Print-ready documents
        - **JSON**: Structured data format
        - **Markdown**: Professional table format for documentation
        """)
    
    with export_cols[1]:
        st.markdown("""
        **Export Types**:
        - Complete Design Record
        - Requirements Traceability Report
        - Risk Management Summary
        - FMEA Analysis Report
        - Compliance Evidence Package
        - Test Execution Summary
        - Post-Market Surveillance Report
        - Regulatory Submission Package
        """)

# Records Management Tab
with help_tabs[3]:
    st.markdown("## 📋 Records Management (ISO 13485)")
    
    st.markdown("### Overview")
    st.markdown("""
    The Records Management module provides comprehensive ISO 13485 compliant record keeping 
    for medical device organizations including supplier management, parts inventory, 
    lab equipment, customer complaints, and non-conformances.
    """)
    
    records_subtabs = st.tabs([
        "🏭 Suppliers", 
        "📦 Parts & Inventory", 
        "🔬 Lab Equipment", 
        "📞 Customer Complaints", 
        "⚠️ Non-Conformances"
    ])
    
    with records_subtabs[0]:
        st.markdown("### 🏭 Supplier Management")
        st.markdown("""
        **Purpose**: Manage supplier qualification, performance tracking, and risk assessment
        
        **Key Features**:
        - Supplier contact information and certification tracking
        - Performance ratings (poor, fair, good, excellent)
        - Quality ratings and on-time delivery tracking
        - Risk level assessment (low, medium, high)
        - Approval status management (pending, approved, conditional, rejected)
        - Contract management and certification status
        
        **Interface Features**:
        - 2:3 width ratio between dataframe and add form
        - Professional table interface with st.dataframe selection
        - Comprehensive editing forms for all supplier data
        """)
    
    with records_subtabs[1]:
        st.markdown("### 📦 Parts & Inventory Management")
        st.markdown("""
        **Purpose**: Track parts inventory with UDI compliance and lot/serial number traceability
        
        **Key Features**:
        - UDI (Unique Device Identification) tracking
        - Lot number and serial number management
        - Expiration date and received date tracking
        - Current stock and minimum stock level management
        - Storage location tracking
        - Unit cost and inventory valuation
        - Status control (In Stock, Quarantined, Expired, Disposed)
        - Supplier linking for supply chain traceability
        
        **Compliance**: Supports FDA UDI requirements for medical device traceability
        """)
    
    with records_subtabs[2]:
        st.markdown("### 🔬 Lab Equipment & Calibration")
        st.markdown("""
        **Purpose**: Manage laboratory equipment calibration schedules and maintenance
        
        **Key Features**:
        - Equipment identification and location tracking
        - Calibration frequency and schedule management
        - Last calibration and next calibration due tracking
        - Calibration standards and compliance notes
        - Technician assignment and responsibility tracking
        - Calibration results and adjustments documentation
        - Status monitoring (Calibrated, Due, Overdue, Out of Service)
        
        **Standards**: Supports ISO 13485 calibration and maintenance requirements
        """)
    
    with records_subtabs[3]:
        st.markdown("### 📞 Customer Complaints Management")
        st.markdown("""
        **Purpose**: Handle customer complaints with MDR (Medical Device Reporting) compliance
        
        **Key Features**:
        - Customer complaint intake and tracking
        - Product identification with lot/serial numbers
        - MDR reportability assessment and tracking
        - Investigation status management (Open, In Progress, Completed, Closed)
        - Root cause analysis documentation
        - Corrective action planning and tracking
        - Response date and customer communication tracking
        - Severity classification for risk assessment
        
        **Regulatory**: Supports FDA MDR and EU MDR reporting requirements
        """)
    
    with records_subtabs[4]:
        st.markdown("### ⚠️ Non-Conformances Management")
        st.markdown("""
        **Purpose**: Track non-conformances with CAPA (Corrective and Preventive Action) integration
        
        **Key Features**:
        - Non-conformance identification and classification
        - Severity levels (Critical, Major, Minor)
        - Risk assessment and impact analysis
        - Disposition management (Use As Is, Rework, Scrap, Return)
        - CAPA system integration for systematic improvement
        - Status tracking (Open, In Progress, Closed)
        - Root cause analysis and corrective action documentation
        
        **Quality System**: Integrates with ISO 13485 quality management requirements
        """)
    
    st.markdown("### 💻 Interface Features")
    st.markdown("""
    **Modern Design**:
    - **2:3 Layout**: Optimized dataframe to form width ratio for efficient data entry
    - **Interactive Selection**: Click any row to select for editing
    - **Comprehensive Forms**: Full access to all table columns and fields
    - **Real-time Updates**: Immediate data refresh after changes
    - **Advanced Filtering**: Filter by status, category, date range with search functionality
    """)

# Activity Logs Tab
with help_tabs[4]:
    st.markdown("## 📊 Activity Logging & Audit Trail")
    
    st.markdown("### Overview")
    st.markdown("""
    The Activity Logging module provides comprehensive audit trail capabilities 
    with tamper-proof logging of all user activities for regulatory compliance 
    and security monitoring.
    """)
    
    st.markdown("### 🎯 Key Features")
    st.markdown("""
    - **Comprehensive Tracking**: Log all significant user actions with timestamps
    - **User Identification**: Track user ID, action type, and detailed descriptions
    - **Security Monitoring**: Capture IP addresses and user agents for security analysis
    - **Project Correlation**: Link activities to specific projects and modules
    - **Audit Compliance**: Tamper-proof logs with 5+ year retention for regulatory requirements
    - **Export Capabilities**: CSV export for external audit purposes
    - **Advanced Filtering**: Filter by user, project, action type, and date range
    - **Search Functionality**: Powerful search across all activity details
    """)
    
    st.markdown("### 📋 Activity Types Tracked")
    activity_cols = st.columns(2)
    
    with activity_cols[0]:
        st.markdown("""
        **Document Management**:
        - Document creation, updates, deletions
        - Version control actions
        - Document approvals and reviews
        - Template usage and modifications
        
        **Design Record Activities**:
        - Requirements creation and updates
        - Hazard analysis modifications
        - FMEA updates and revisions
        - Traceability link changes
        - Compliance status updates
        """)
    
    with activity_cols[1]:
        st.markdown("""
        **Records Management**:
        - Supplier updates and approvals
        - Parts inventory changes
        - Equipment calibration records
        - Customer complaint handling
        - Non-conformance processing
        
        **System Activities**:
        - User login/logout events
        - Configuration changes
        - Export operations
        - Knowledge base updates
        """)
    
    st.markdown("### 🔒 Security & Compliance")
    st.markdown("""
    - **Tamper-Proof**: Activity logs are immutable once created
    - **Retention Policy**: Configurable retention (default: 5+ years for regulatory compliance)
    - **Privacy Controls**: IP address and user agent logging can be configured
    - **Audit Export**: Generate audit reports for external compliance requirements
    - **Correlation**: Link related activities across different modules and projects
    - **Batch Processing**: Efficient handling of high-volume activity logging
    """)

# Templates Tab
with help_tabs[5]:
    st.markdown("## 📄 Templates Management")
    
    st.markdown("### Overview")
    st.markdown("""
    The Templates module provides pre-built document templates and allows creation 
    of custom templates to ensure consistency across your organization.
    """)
    
    st.markdown("### 🎯 Key Features")
    st.markdown("""
    - **Pre-built Templates**: Ready-to-use templates for common documents
    - **Custom Templates**: Create organization-specific templates
    - **Template Categories**: Organize templates by type and purpose
    - **Version Control**: Track template versions and changes
    - **Template Library**: Searchable template repository
    """)
    
    st.markdown("### 📖 Template Types")
    template_cols = st.columns(2)
    
    with template_cols[0]:
        st.markdown("""
        **📋 Requirements Documents**
        - System Requirements Specification
        - Software Requirements Specification
        - User Requirements Specification
        
        **⚠️ Risk Management**
        - Risk Management Plan
        - Risk Analysis Report
        - Hazard Analysis Document
        
        **🧪 Testing Documents**
        - Test Plan Template
        - Test Case Specification
        - Validation Protocol
        """)
    
    with template_cols[1]:
        st.markdown("""
        **🏗️ Design Documents**
        - Design Specification
        - Architecture Document
        - Interface Control Document
        
        **📑 Compliance Documents**
        - Technical File Template
        - Clinical Evaluation Report
        - Post-Market Surveillance Plan
        
        **📊 Reports**
        - Project Status Report
        - Audit Report Template
        - Management Review Report
        """)

# Documents Tab
with help_tabs[6]:
    st.markdown("## 📁 Document Management")
    
    st.markdown("### Overview")
    st.markdown("""
    The Documents module provides centralized document repository with version control, 
    approval workflows, and comprehensive search capabilities.
    """)
    
    st.markdown("### 🎯 Key Features")
    st.markdown("""
    - **Document Upload**: Support for multiple file formats
    - **Version Control**: Track document versions and changes
    - **Approval Workflows**: Route documents through approval processes
    - **Search & Filter**: Find documents quickly by metadata
    - **Access Control**: Manage document permissions and access
    - **Document Analytics**: Track usage and access patterns
    """)
    
    st.markdown("### 📖 Supported File Types")
    st.markdown("""
    - **Documents**: PDF, DOC, DOCX, TXT, RTF
    - **Spreadsheets**: XLS, XLSX, CSV
    - **Presentations**: PPT, PPTX
    - **Images**: PNG, JPG, GIF, BMP
    - **Archives**: ZIP, RAR, 7Z
    - **Technical**: CAD files, specifications
    """)

# Code Tab
with help_tabs[7]:
    st.markdown("## 💻 Code Management")
    
    st.markdown("### Overview")
    st.markdown("""
    The Code module integrates with version control systems to manage source code, 
    perform code reviews, and track code quality metrics.
    """)
    
    st.markdown("### 🎯 Key Features")
    st.markdown("""
    - **Repository Integration**: Connect with Git repositories
    - **Code Review**: Peer review workflows and approval processes
    - **Branch Management**: Track branches and merge requests
    - **Code Quality**: Static analysis and quality metrics
    - **Documentation**: Link code to requirements and design documents
    """)
    
    st.markdown("### 📖 Supported Workflows")
    st.markdown("""
    1. **Code Upload**: Upload code files or connect repositories
    2. **Code Review**: Create review requests and assign reviewers
    3. **Approval Process**: Track approvals and feedback
    4. **Quality Gates**: Enforce quality checks and standards
    5. **Traceability**: Link code to requirements and test cases
    """)

# Reviews Tab
with help_tabs[8]:
    st.markdown("## 🔍 Review System")
    
    st.markdown("### Overview")
    st.markdown("""
    The Review system provides structured peer review workflows for documents, 
    code, and design artifacts with approval tracking and audit trails.
    """)
    
    st.markdown("### 🎯 Key Features")
    st.markdown("""
    - **Review Workflows**: Customizable review and approval processes
    - **Reviewer Assignment**: Assign reviewers based on expertise
    - **Approval Tracking**: Track review status and approvals
    - **Review History**: Maintain complete audit trail
    - **Notification System**: Automated notifications for review requests
    """)
    
    st.markdown("### 📖 Review Types")
    st.markdown("""
    - **Document Reviews**: Technical documents, specifications, reports
    - **Design Reviews**: Architecture, design specifications, drawings
    - **Code Reviews**: Source code, scripts, configuration files
    - **Test Reviews**: Test plans, test cases, test results
    - **Compliance Reviews**: Regulatory submissions, audit responses
    """)

# Audit Tab
with help_tabs[9]:
    st.markdown("## 📊 Audit Module")
    
    st.markdown("### Overview")
    st.markdown("""
    The Audit module provides comprehensive audit trail capabilities, compliance 
    tracking, and audit preparation tools for regulatory compliance.
    """)
    
    st.markdown("### 🎯 Key Features")
    st.markdown("""
    - **Audit Trail**: Complete activity logging and tracking
    - **Compliance Monitoring**: Track compliance status across standards
    - **Audit Preparation**: Generate audit packages and evidence
    - **Finding Management**: Track and resolve audit findings
    - **Reporting**: Comprehensive audit reports and dashboards
    """)
    
    st.markdown("### 📖 Audit Capabilities")
    st.markdown("""
    - **Activity Logging**: Track all user actions and changes
    - **Document History**: Maintain complete document change history
    - **Access Logs**: Monitor user access and permissions
    - **Compliance Reports**: Generate compliance status reports
    - **Evidence Collection**: Gather evidence for regulatory submissions
    """)

# Training Tab
with help_tabs[10]:
    st.markdown("## 🎓 Training Module")
    
    st.markdown("### Overview")
    st.markdown("""
    The Training module provides learning management capabilities including 
    course creation, progress tracking, and certification management.
    """)
    
    st.markdown("### 🎯 Key Features")
    st.markdown("""
    - **AI-Powered Learning**: Generate learning content from Knowledge Base
    - **Assessment System**: Create and take True/False assessments  
    - **Progress Tracking**: Monitor learner progress and completion
    - **Results Analytics**: View detailed performance and improvement trends
    - **Knowledge Base Integration**: Leverage organizational knowledge for training
    - **Automated Content Generation**: AI-generated learning materials and questions
    """)
    
    st.markdown("### 📖 Training Types")
    st.markdown("""
    - **Onboarding**: New employee orientation and training
    - **Compliance Training**: Regulatory and quality training
    - **Technical Training**: Product and process specific training
    - **Safety Training**: Health and safety requirements
    - **Continuing Education**: Ongoing professional development
    """)

# Knowledge Base Tab
with help_tabs[11]:
    st.markdown("## 📚 Knowledge Base")
    
    st.markdown("### Overview")
    st.markdown("""
    The Knowledge Base module provides an AI-powered RAG (Retrieval Augmented Generation) system 
    that automatically builds a searchable organizational knowledge repository from approved documents, 
    templates, and audit findings.
    """)
    
    st.markdown("### 🎯 Backend Services Architecture")
    st.markdown("""
    **Core Knowledge Base Service** (`backend/app/kb_service_pg.py`):
    - **Purpose**: Central hub for all knowledge base operations using hybrid PostgreSQL + Qdrant vector database
    - **Functions**: Document indexing, RAG-based querying, semantic search, collection management
    - **Technology Stack**: PostgreSQL for metadata, Qdrant for vector embeddings, Ollama for LLM processing
    """)
    
    kb_subtabs = st.tabs([
        "🏗️ Architecture", 
        "🔄 Service Integration", 
        "🗄️ Database Design", 
        "🤖 RAG Implementation",
        "📊 API Endpoints"
    ])
    
    with kb_subtabs[0]:
        st.markdown("### 🏗️ Knowledge Base Architecture")
        st.markdown("""
        **Hybrid Database System**:
        - **PostgreSQL**: Stores document metadata, collections, query logs, and configuration
        - **Qdrant Vector Database**: Stores document chunks as vectors with metadata payloads
        - **Ollama**: Generates embeddings and provides LLM responses for RAG queries
        
        **Key Components**:
        - **Collections**: Organize documents by project, document type, or audit category
        - **Document Chunks**: Intelligent text segmentation (default 1000 characters)
        - **Vector Embeddings**: 768-dimensional vectors using nomic-embed-text model
        - **Similarity Search**: Cosine distance-based semantic search
        """)
    
    with kb_subtabs[1]:
        st.markdown("### 🔄 Integrated Services")
        st.markdown("""
        **Automatic Knowledge Base Integration**:
        
        **1. Documents Service** (`documents_service.py`):
        - **Purpose**: Automatically indexes approved documents into project-specific collections
        - **Collection Naming**: `project_name.replace(' ', '_').lower()`
        - **Trigger**: When document status changes to "approved"
        
        **2. Templates Service** (`templates_service_pg.py`):
        - **Purpose**: Indexes approved templates by document type
        - **Collection Naming**: `document_type.replace(' ', '_').lower()`
        - **Content**: Template content, metadata, and version information
        
        **3. Audit Service** (`audit_service.py`):
        - **Purpose**: Indexes closed audit findings to build organizational knowledge
        - **Collection**: "audit_findings" with finding details, root causes, and resolutions
        - **Trigger**: When audit findings are closed
        
        **4. AI Service** (`ai_service.py`):
        - **Purpose**: Provides RAG-powered chat and content generation
        - **Integration**: Queries knowledge base for context in AI responses
        
        **5. Training System**:
        - **Purpose**: Generates learning content and assessments from knowledge base
        - **Features**: Multi-collection content extraction for training materials
        """)
    
    with kb_subtabs[2]:
        st.markdown("### 🗄️ Database Schema")
        st.markdown("""
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
        """)
    
    with kb_subtabs[3]:
        st.markdown("### 🤖 RAG Implementation")
        st.markdown("""
        **RAG Query Workflow**:
        1. **Embedding Generation**: Query text → Vector embedding (Ollama)
        2. **Similarity Search**: Search Qdrant for relevant document chunks (5 chunks by default)
        3. **Context Assembly**: Combine retrieved chunks into context
        4. **LLM Response**: Generate response using context + query (Ollama qwen2:1.5b)
        5. **Logging**: Store query metrics in PostgreSQL
        
        **Performance Optimization**:
        - Configurable similarity search limits
        - Response time tracking
        - Chunk size optimization (1000 characters default)
        - Connection pooling for databases
        - Score threshold filtering (0.7 minimum)
        
        **Models Used**:
        - **Embedding Model**: nomic-embed-text (768 dimensions)
        - **Chat Model**: qwen2:1.5b (configurable)
        - **Context Window**: 4000 tokens (configurable)
        """)
    
    with kb_subtabs[4]:
        st.markdown("### 📊 API Endpoints")
        st.markdown("""
        **Core Endpoints**:
        - `POST /kb/upload` - Upload documents to collections
        - `POST /kb/add_text` - Add text content directly
        - `POST /kb/chat` - RAG-based chat with collections
        - `GET /kb/stats` - Collection and usage statistics
        - `POST /kb/reset` - Reset collections (admin only)
        - `POST /kb/collections` - Create new collection
        - `GET /kb/collections` - List all collections
        - `GET /kb/collections/{name}` - Get collection details
        - `DELETE /kb/documents/{id}` - Delete document from collection
        - `POST /kb/collections/{name}/set-default` - Set default collection
        
        **Training Integration**:
        - `POST /training/learn` - Generate learning content from KB
        - `POST /training/assess` - Generate assessments from KB content
        - `POST /training/submit` - Submit assessment answers
        """)
    
    st.markdown("### 🚀 Key Features")
    st.markdown("""
    - **Automatic Indexing**: Documents, templates, and audit findings automatically added to knowledge base
    - **Intelligent Search**: RAG-powered semantic search with source citations
    - **Multi-Collection Support**: Organize knowledge by projects, document types, and audit categories
    - **AI-Powered Chat**: Natural language querying with contextual responses
    - **Training Integration**: Generate learning content and assessments from organizational knowledge
    - **Performance Analytics**: Query logging, response time tracking, and usage statistics
    - **Hybrid Architecture**: Combines relational and vector databases for optimal performance
    """)
    
    st.markdown("### 📖 Automatic Collection Creation")
    st.markdown("""
    **Project Collections**: Created automatically when documents are approved in projects
    - Collection name format: `project_name.replace(' ', '_').lower()`
    - Contains: All approved project documents and their content
    
    **Template Collections**: Created by document type when templates are approved
    - Collection name format: `document_type.replace(' ', '_').lower()`
    - Contains: Approved templates for policies, procedures, reports, etc.
    
    **Audit Collections**: Created for closed audit findings
    - Collection name: "audit_findings"
    - Contains: Finding descriptions, root causes, corrective actions, and resolutions
    
    **Default Collection**: "knowledge_base" for general organizational knowledge
    """)
    
    st.markdown("### 🎯 Usage Benefits")
    st.markdown("""
    - **Organizational Memory**: Builds searchable knowledge from all approved content
    - **AI-Assisted Work**: Provides intelligent context for document creation and decision-making
    - **Training Automation**: Generates learning materials and assessments from existing knowledge
    - **Compliance Support**: Maintains searchable repository of compliance-related knowledge
    - **Cross-Project Learning**: Enables knowledge sharing across different projects and teams
    - **Audit Trail**: Complete logging of knowledge base queries and usage patterns
    """)

# Footer
st.markdown("---")
st.markdown("### 🤝 Need More Help?")

help_cols = st.columns([1, 1, 1])

with help_cols[0]:
    st.markdown("**📞 Contact Support**")
    st.markdown("- Email: support@docsmait.com")
    st.markdown("- Phone: +1-555-0123")
    st.markdown("- Hours: Mon-Fri 9AM-5PM")

with help_cols[1]:
    st.markdown("**📖 Documentation**")
    st.markdown("- User Manual: [Download PDF]")
    st.markdown("- API Documentation: [View Online]")
    st.markdown("- Video Tutorials: [Watch Now]")

with help_cols[2]:
    st.markdown("**🌐 Community**")
    st.markdown("- User Forum: [Join Discussion]")
    st.markdown("- Knowledge Base: [Browse Articles]")
    st.markdown("- Feature Requests: [Submit Ideas]")

st.markdown("---")
st.markdown("### 🆕 What's New in Docsmait")

new_features_cols = st.columns(2)

with new_features_cols[0]:
    st.markdown("""
    **🔬 Enhanced Design Record System**:
    - Interactive st.dataframe tables with single-row selection
    - Professional Markdown export for regulatory submissions
    - Comprehensive traceability matrix with rationale documentation
    - Real-time data updates and consistent 400px table heights
    
    **📋 New Records Management Module**:
    - Complete ISO 13485 compliant record keeping
    - Supplier performance and quality tracking
    - UDI-compliant parts inventory management
    - Lab equipment calibration tracking
    """)

with new_features_cols[1]:
    st.markdown("""
    **📊 Activity Logging & Audit Trail**:
    - Comprehensive user activity tracking
    - Tamper-proof audit logs with 5+ year retention
    - Export capabilities for external audits
    - IP address and user agent tracking for security
    
    **💻 Modern Interface Improvements**:
    - 2:3 width ratio layout for optimal data entry
    - Advanced filtering and search functionality
    - Multi-format export (CSV, Excel, PDF, JSON, Markdown)
    - Configuration-driven UI constants
    """)

st.info("💡 **Tip**: Use the search functionality in each module to quickly find specific items, check the new Activity Logs for comprehensive audit trails, and explore the enhanced export capabilities for professional regulatory documentation.")