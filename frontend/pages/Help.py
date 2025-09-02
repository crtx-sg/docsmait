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
        - Compliance tracking and evidence management
        
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
        """)
    
    st.markdown("### 🚀 Quick Start Guide")
    st.markdown("""
    1. **Start with Projects**: Navigate to Projects and create your first project
    2. **Set up Design Record**: Use Design Record to manage requirements and risks
    3. **Create Templates**: Set up document templates for consistency
    4. **Upload Documents**: Add your existing documents to the system
    5. **Enable Reviews**: Set up review workflows for quality control
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

# Templates Tab
with help_tabs[3]:
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
with help_tabs[4]:
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
with help_tabs[5]:
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
with help_tabs[6]:
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
with help_tabs[7]:
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
with help_tabs[8]:
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
with help_tabs[9]:
    st.markdown("## 📚 Knowledge Base")
    
    st.markdown("### Overview")
    st.markdown("""
    The Knowledge Base module provides a centralized repository for organizational 
    knowledge, best practices, and reference materials.
    """)
    
    st.markdown("### 🎯 Key Features")
    st.markdown("""
    - **Knowledge Articles**: Create and manage knowledge articles
    - **Search Capabilities**: Powerful search and filtering
    - **Categories**: Organize knowledge by topics and domains
    - **Version Control**: Track knowledge article versions
    - **User Contributions**: Allow user-generated content
    """)
    
    st.markdown("### 📖 Knowledge Types")
    st.markdown("""
    - **Best Practices**: Documented procedures and guidelines
    - **Technical Reference**: Technical specifications and standards
    - **Troubleshooting**: Problem resolution guides
    - **Process Documentation**: Standard operating procedures
    - **Regulatory Guidance**: Regulatory requirements and interpretations
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

st.info("💡 **Tip**: Use the search functionality in each module to quickly find specific items, and check the notifications panel for important updates and pending tasks.")