# Docsm<u>ai</u>t - AI-Powered Document & Compliance Management System

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)
[![Streamlit](https://img.shields.io/badge/frontend-streamlit-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/backend-fastapi-green.svg)](https://fastapi.tiangolo.com/)

## 🚀 Overview

Docsmait is a comprehensive AI-powered document and compliance management system designed for regulated industries including medical devices, automotive, and industrial sectors. It provides end-to-end lifecycle management with built-in compliance tracking, risk management, and intelligent knowledge base capabilities.

### ✨ Key Features

- 🏥 **Medical Device Compliance** - ISO 13485, ISO 14971, IEC 62304, FDA 21 CFR Part 820
- 🚗 **Automotive Standards** - ISO 26262, ASIL safety integrity levels  
- 🏭 **Industrial Safety** - SIL levels, IEC 61508 compliance
- 🤖 **AI-Powered Knowledge Base** - Semantic search, automated content generation
- 📋 **Requirements Management** - Full traceability matrix with impact analysis
- ⚠️ **Risk & Hazard Analysis** - FMEA, risk assessment, mitigation tracking
- 🧪 **Test Management** - Test planning, execution, and validation protocols
- 📊 **Audit & Compliance** - Complete audit trails and compliance reporting
- 🎓 **Training System** - AI-generated learning content and assessments
- 📄 **Template Management** - Pre-built and custom document templates

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Databases     │
│   Streamlit     │◄──►│    FastAPI      │◄──►│   PostgreSQL    │
│   Port: 8501    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   AI Services   │    │  Vector Store   │
                       │    Ollama       │    │     Qdrant      │
                       │  Port: 11434    │    │   Port: 6333    │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose** (v2.0+)
- **8GB+ RAM** recommended  
- **5GB+ free disk space**

### 1. Clone Repository

```bash
git clone <repository-url>
cd docsmait
```

### 2. Environment Setup

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your settings
```

### 3. Deploy with Docker

```bash
# Start all services
docker-compose up -d

# Check service status  
docker-compose ps
```

### 4. Access Application

- **Web Interface**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Vector Database**: http://localhost:6333

### 5. Initial Setup

1. Navigate to http://localhost:8501/pages/Auth.py
2. Create admin account (first user gets admin privileges)
3. Start creating projects and managing documents

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [INSTALL.md](INSTALL.md) | Comprehensive installation guide |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Detailed functional requirements |
| [TEST_CASES.md](TEST_CASES.md) | Test cases and scenarios |
| [docs/USER_MANUAL.md](docs/USER_MANUAL.md) | Complete user manual |

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# AI Services  
OLLAMA_BASE_URL=http://ollama:11434
GENERAL_PURPOSE_LLM=qwen2:7b
EMBEDDING_MODEL=nomic-embed-text:latest

# Security
JWT_SECRET_KEY=your-secure-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Vector Database
QDRANT_URL=http://qdrant:6333
```

## 📋 System Modules

### 🏠 Home Dashboard
- Personal activity tracking
- Project health overview  
- Key performance indicators
- System-wide analytics

### 📋 Projects Management
- Multi-project organization
- Team member management
- Progress tracking and reporting
- Timeline and milestone management

### 🔬 Design Record System
- **Requirements Management**: Comprehensive requirements with unique IDs, priority levels, verification methods
- **Risk Analysis**: Hazard identification, FMEA, risk mitigation with safety integrity levels (ASIL, SIL, DAL)
- **Design Artifacts**: Specifications, architecture, interfaces, detailed design documentation
- **Test Management**: Unit, integration, system, safety, clinical, biocompatibility testing
- **Traceability Matrix**: Interactive requirements-to-hazards traceability with rationale documentation
- **Compliance Tracking**: ISO 13485, ISO 14971, IEC 62304, ISO 26262, FDA 21 CFR Part 820
- **Post-Market Surveillance**: Adverse events, field actions, regulatory reporting
- **Interactive Interface**: st.dataframe tables with single-row selection and comprehensive editing
- **Professional Exports**: Markdown, CSV, Excel, PDF, JSON formats with filtered reporting

### 📋 ISO 13485 Records Management
- **Supplier Management**: Performance tracking, quality ratings, risk assessment, certification status
- **Parts & Inventory**: UDI tracking, lot/serial numbers, expiration management, stock control
- **Lab Equipment**: Calibration tracking, maintenance schedules, technician assignments
- **Customer Complaints**: MDR reportability, investigation management, root cause analysis
- **Non-Conformances**: CAPA integration, severity classification, disposition management
- **2:3 Interface Layout**: Optimized dataframe to form ratio for efficient data entry
- **Advanced Filtering**: Status, category, date range filtering with comprehensive search

### 📊 Activity Logging & Audit Trail
- **Comprehensive Tracking**: All user actions logged with timestamps and details
- **Audit Compliance**: Tamper-proof logs with 5+ year retention for regulatory requirements
- **Export Capabilities**: CSV export for external audit purposes
- **Security Tracking**: IP addresses and user agents captured for security analysis
- **Project Correlation**: Activity linking across different modules and projects

### 📄 Template Management  
- Pre-built industry templates
- Custom template creation
- Version control and approval workflows
- Two-column editing interface

### 📁 Document Management
- Centralized document repository
- Version control and change tracking
- Approval workflows and reviews
- Advanced search and categorization

### 💻 Code Management
- Source code repository integration
- Code review and approval processes
- Quality metrics and static analysis
- Traceability to requirements

### 🔍 Review System
- Structured peer review workflows
- Multi-level approval processes
- Complete audit trail
- Automated notifications

### 📊 Audit & Compliance
- Complete activity logging
- Compliance monitoring dashboards
- Audit preparation tools
- Evidence collection and reporting

### 🎓 Training System
- AI-powered learning content generation
- Automated assessment creation
- Progress tracking and analytics
- Knowledge base integration

### 📚 Knowledge Base
- AI-powered semantic search
- Automated content vectorization
- Cross-referencing and relationships
- Integration with all system modules

## 🛠️ Development

### Technology Stack

- **Frontend**: Streamlit, Python
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **AI/ML**: Ollama, Qdrant Vector DB
- **Authentication**: JWT tokens, bcrypt
- **Deployment**: Docker, Docker Compose

### Development Setup

```bash
# Backend development
cd backend  
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend development  
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

### API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧹 Maintenance

### System Cleanup

```bash
cd scripts

# Preview cleanup operations (safe)
python cleanup_system.py --dry-run

# Run maintenance tasks
python maintenance_tasks.py --all --verbose

# System reset (CAUTION!)
python reset_system.py --keep-admin --confirm
```

### Backup & Restore

```bash
# Create full backup
python backup.py --full --compress

# Restore from backup  
python restore.py --backup-file backup_20240101_120000.tar.gz
```

## 🏥 Industry Compliance

### Medical Devices
- **ISO 13485:2016** - Quality Management Systems
- **ISO 14971:2019** - Risk Management  
- **IEC 62304:2006** - Medical Device Software
- **FDA 21 CFR Part 820** - Quality System Regulation

### Automotive  
- **ISO 26262** - Functional Safety
- **ASIL A/B/C/D** - Automotive Safety Integrity Levels

### Industrial
- **IEC 61508** - Functional Safety  
- **SIL 1/2/3/4** - Safety Integrity Levels

## 🔐 Security

- JWT-based authentication
- Role-based access control (RBAC)
- Secure password hashing (bcrypt)
- API rate limiting and validation
- Comprehensive audit logging
- Data encryption at rest and in transit

## 📊 Performance

### Recommended Specifications

| Environment | CPU | RAM | Storage | Users |
|-------------|-----|-----|---------|-------|
| Development | 2 cores | 4GB | 20GB | 1-2 |
| Small Team | 4 cores | 8GB | 100GB | 5-10 |
| Enterprise | 8+ cores | 16GB+ | 500GB+ | 50+ |

### Scalability Features

- Horizontal scaling with Docker Swarm/Kubernetes
- Database connection pooling
- Caching layer for frequent queries
- Async API operations
- Vector database optimization

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Code Standards

- Python: PEP 8, type hints, docstrings
- FastAPI: Async/await patterns, Pydantic models
- Streamlit: Component-based architecture
- Database: SQLAlchemy ORM, migration scripts
- Testing: Pytest, 80%+ coverage target

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [Installation Guide](INSTALL.md)
- [User Manual](docs/USER_MANUAL.md)  
- [API Documentation](http://localhost:8000/docs)
- [Architecture Guide](ARCHITECTURE.md)

### Troubleshooting

Common issues and solutions:

1. **Services won't start**: Check Docker daemon and port availability
2. **Database connection failed**: Verify PostgreSQL service and credentials
3. **AI models not loading**: Check Ollama service and model downloads
4. **Frontend errors**: Review browser console and service logs

```bash
# View service logs
docker-compose logs -f [service-name]

# Restart services
docker-compose restart

# Health check
curl http://localhost:8000/health
```

### Getting Help

1. Check existing documentation
2. Review troubleshooting section  
3. Search existing issues
4. Create detailed issue with logs
5. Contact system administrator

---

## 🏢 About

Docsmait is developed by **[Coherentix Labs](https://www.coherentix.com)** for organizations requiring comprehensive document management and regulatory compliance in highly regulated industries.

**Built for**: Medical Device Companies, Automotive Manufacturers, Industrial Safety Organizations, Regulatory Affairs Teams, Quality Assurance Departments

---

### 🎯 Getting Started Checklist

- [ ] Clone repository and review documentation
- [ ] Configure environment variables (.env)
- [ ] Deploy with Docker Compose
- [ ] Create admin account
- [ ] Import existing documents and templates
- [ ] Configure compliance standards
- [ ] Set up user roles and permissions
- [ ] Train team on system usage
- [ ] Establish backup and maintenance procedures

**Ready to transform your document and compliance management?** Start with our [Installation Guide](INSTALL.md)!