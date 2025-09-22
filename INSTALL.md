# Docsmait Installation Guide

## 🚀 Quick Installation

This guide will help you quickly install and deploy Docsmait after cloning the repository.

### Prerequisites

Before starting, ensure you have the following installed:
- **Docker** and **Docker Compose** (v2.0+ recommended)
- **Git** for cloning the repository
- **8GB+ RAM** recommended for optimal performance
- **5GB+ free disk space** for containers and data

### 1. Clone Repository

```bash
git clone <repository-url>
cd docsmait
```

### 2. Environment Setup

Copy the environment template and configure:

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables (see Configuration section below)
nano .env  # or your preferred editor
```

### 3. Quick Start with Docker

```bash
# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs (optional)
docker compose logs -f
```

### 4. Database Initialization

After starting the services, you need to initialize the database. This will create the necessary tables and a default admin user.

```bash
docker exec docsmait_backend python -m app.init_db
```

This will output the credentials for the default admin user.

### 5. Access the Application

- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Qdrant Vector DB**: http://localhost:6335
- **PostgreSQL**: localhost:5433

### 6. Initial Setup

1. **Login as Admin**: Use the admin credentials from the previous step to log in.
2. **Navigate to**: http://localhost:8501/pages/Auth.py
3. **Sign up** with your admin credentials
4. **Access all features** with admin privileges

---

## ⚙️ Detailed Configuration

### Environment Variables (.env)

```bash
# === Database Configuration ===
DB_USER=docsmait_user
DB_PASSWORD=secure_password_here
DB_HOST=docsmait_postgres
DB_PORT=5432
DB_NAME=docsmait
DATABASE_URL=postgresql://docsmait_user:secure_password_here@docsmait_postgres:5432/docsmait

# === Authentication ===
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# === AI/LLM Configuration ===
OLLAMA_BASE_URL=http://ollama:11434
GENERAL_PURPOSE_LLM=qwen2:7b
EMBEDDING_MODEL=nomic-embed-text:latest
DEFAULT_CHAT_MODEL=qwen2:1.5b

# === Vector Database ===
QDRANT_URL=http://qdrant:6333
VECTOR_DB=qdrant

# === API Configuration ===
API_HOST=0.0.0.0
API_PORT=8000
BACKEND_URL=http://backend:8000
FRONTEND_URL=http://localhost:8501

# === Knowledge Base ===
DEFAULT_CHUNK_SIZE=1000
DEFAULT_COLLECTION_NAME=knowledge_base
MAX_FILE_SIZE_MB=10
EMBEDDING_DIMENSIONS=768

# === AI Settings ===
AI_TIMEOUT=120
MAX_RESPONSE_LENGTH=2000
AI_CONTEXT_WINDOW=4000
SHOW_PROMPT=true

# === Logging ===
LOG_LEVEL=INFO
LOG_FILE=/app/logs/docsmait.log

# === Usage Tracking ===
TRACK_USAGE=true
TRACK_FEEDBACK=true
LOG_PROMPTS=true
USAGE_RETENTION_DAYS=90

# === Activity Logging Configuration ===
ACTIVITY_LOG_RETENTION_DAYS=365
LOG_IP_ADDRESSES=true
LOG_USER_AGENTS=true
ACTIVITY_LOG_BATCH_SIZE=1000

# === Design Record Configuration ===
REQUIREMENT_ID_PREFIX=REQ
HAZARD_ID_PREFIX=HAZ

# === Records Management Configuration ===
SUPPLIER_ID_PREFIX=SUP
PART_NUMBER_PREFIX=PRT
EQUIPMENT_ID_PREFIX=EQP
COMPLAINT_ID_PREFIX=COMP
NC_ID_PREFIX=NC
DEFAULT_CALIBRATION_FREQUENCY_DAYS=365

# === Export Configuration ===
DEFAULT_EXPORT_FORMAT=csv
EXPORT_BATCH_SIZE=1000
MAX_EXPORT_RECORDS=10000
EXPORT_TIMEOUT_SECONDS=300

# === UI Configuration ===
DATAFRAME_HEIGHT=400
DATAFRAME_SELECTION_MODE=single-row
TABLE_PAGE_SIZE=20
```

---

## 🔧 Service Components

### Core Services

| Service | Purpose | Port | Health Check |
|---------|---------|------|--------------|
| **frontend** | Streamlit UI | 8501 | http://localhost:8501 |
| **backend** | FastAPI Server | 8000 | http://localhost:8000/health |
| **docsmait_postgres** | PostgreSQL DB | 5432 | `docker-compose logs postgres` |
| **qdrant** | Vector Database | 6333 | http://localhost:6333 |
| **ollama** | AI/LLM Service | 11434 | http://localhost:11434 |

### Service Dependencies

```
frontend → backend → postgres
                  → qdrant  
                  → ollama
```

---

## 📦 Installation Methods

### Method 1: Docker Compose (Recommended)

**Advantages**: 
- Single command deployment
- All dependencies included
- Isolated environment
- Easy updates

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Development with auto-reload
docker-compose -f docker-compose.dev.yml up -d
```

### Method 2: Manual Installation

**Prerequisites**:
- Python 3.9+
- PostgreSQL 13+
- Qdrant Vector Database
- Ollama (for AI features)

```bash
# Backend setup
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend setup (new terminal)
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

### Method 3: Kubernetes (Enterprise)

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n docsmait

# Access via ingress or port-forward
kubectl port-forward service/docsmait-frontend 8501:8501
```

---

## 🗃️ Database Setup

### Manual Database Setup

```bash
# Create database
createdb -U postgres docsmait

# Run migrations (from backend directory)
python -m app.init_db

# Verify tables
psql -U docsmait_user -d docsmait -c "\dt"
```

---

## 🤖 AI Models Setup

### Automatic Model Downloads

```bash
# Models are downloaded automatically on first use
# Default models included:
- qwen2:7b (General purpose)
- qwen2:1.5b (Fast responses) 
- nomic-embed-text:latest (Embeddings)
```

### Manual Model Management

```bash
# Pull specific models
docker exec -it docsmait-ollama-1 ollama pull qwen2:7b
docker exec -it docsmait-ollama-1 ollama pull llama3:latest

# List installed models
docker exec -it docsmait-ollama-1 ollama list

# Model configuration in .env:
GENERAL_PURPOSE_LLM=qwen2:7b
EMBEDDING_MODEL=nomic-embed-text:latest
```

---

## 🔐 Security Configuration

### SSL/TLS Setup

```bash
# Generate SSL certificates (production)
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365

# Update docker-compose.yml with SSL configuration
```

### Authentication Security

```bash
# Generate secure JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file
JWT_SECRET_KEY=your-generated-secret-key
```

### Database Security

```bash
# Change default passwords
DB_PASSWORD=your-secure-database-password

# Restrict database access
# Edit postgresql.conf for production deployment
```

---

## 📊 Health Checks & Monitoring

### Service Health Endpoints

```bash
# Backend API health
curl http://localhost:8000/health

# Database connection test  
curl http://localhost:8000/db/health

# AI service status
curl http://localhost:11434/api/tags

# Vector database status
curl http://localhost:6333/
```

### Monitoring Setup

```bash
# View all service logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Performance Monitoring

```bash
# Resource usage
docker stats

# Database performance
docker exec -it docsmait-postgres-1 psql -U docsmait_user -d docsmait -c "SELECT * FROM pg_stat_database;"

# Storage usage
docker exec -it docsmait-qdrant-1 du -sh /qdrant/storage
```

---

## 🧹 Maintenance & Housekeeping

### System Cleanup Scripts

```bash
# Run maintenance tasks
cd scripts
python maintenance_tasks.py --all --dry-run

# Clean up old data  
python cleanup_system.py --dry-run

# System reset (CAUTION!)
python reset_system.py --keep-admin --confirm
```

### Backup & Restore

```bash
# Create backup
cd scripts
python backup.py --full --compress

# Restore from backup
python restore.py --backup-file backup_20240101_120000.tar.gz
```

### Log Management

```bash
# Rotate logs
docker-compose exec backend logrotate /app/logs/docsmait.log

# Clean old logs (older than 30 days)
find logs/ -name "*.log.*" -mtime +30 -delete
```

---

## 🚀 Deployment Strategies

### Development Deployment

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Features enabled:
- Auto-reload on code changes  
- Debug mode enabled
- Verbose logging
- Development database
```

### Production Deployment

```bash
# Production configuration
docker-compose -f docker-compose.prod.yml up -d

# Features:
- Optimized containers
- SSL/TLS enabled
- Resource limits
- Persistent volumes
- Health checks
```

### High Availability Setup

```bash
# Multi-node deployment with Docker Swarm
docker swarm init
docker stack deploy -c docker-stack.yml docsmait

# Features:
- Load balancing
- Service replication
- Automatic failover  
- Rolling updates
```

---

## 🔧 Troubleshooting

### Common Issues

**Issue**: Frontend cannot connect to backend
```bash
# Solution: Check network connectivity
docker-compose logs backend
docker-compose exec frontend ping backend
```

**Issue**: Database connection failed
```bash
# Solution: Verify database service and credentials
docker-compose logs postgres
docker-compose exec postgres psql -U docsmait_user -d docsmait
```

**Issue**: AI models not loading
```bash
# Solution: Check Ollama service and pull models manually
docker-compose logs ollama
docker-compose exec ollama ollama pull qwen2:7b
```

**Issue**: Vector database connection error
```bash
# Solution: Check Qdrant service status
curl http://localhost:6333/health
docker-compose restart qdrant
```

### Performance Issues

**Slow response times**:
- Increase container memory limits
- Optimize database queries
- Check disk space
- Monitor CPU usage

**High memory usage**:
- Adjust AI model size
- Implement query caching
- Optimize vector embeddings
- Review log retention settings

### Recovery Procedures

```bash
# Complete service restart
docker-compose down && docker-compose up -d

# Database recovery
docker-compose exec postgres pg_dump docsmait > backup.sql
docker-compose down -v  # Remove volumes
docker-compose up -d
# Restore from backup.sql

# Reset to clean state
docker-compose down -v --remove-orphans
docker system prune -f
docker-compose up -d
```

---

## 📋 Post-Installation Checklist

- [ ] All services running (`docker-compose ps`)
- [ ] Frontend accessible at http://localhost:8501  
- [ ] Backend API accessible at http://localhost:8000/docs
- [ ] Admin user created successfully
- [ ] Database tables initialized
- [ ] AI models downloaded and working
- [ ] Vector database operational
- [ ] SSL certificates configured (production)
- [ ] Backup procedures tested
- [ ] Monitoring alerts configured
- [ ] Security settings reviewed
- [ ] Performance benchmarks recorded

---

## 🆘 Support & Documentation

### Quick Reference Links

- **API Documentation**: http://localhost:8000/docs
- **User Manual**: `/docs/USER_MANUAL.md`
- **Architecture Guide**: `/ARCHITECTURE.md` 
- **Development Guide**: `/docs/DEVELOPMENT.md`
- **System Requirements**: `/REQUIREMENTS.md`

### Getting Help

1. **Check Logs**: `docker-compose logs -f [service]`
2. **Health Checks**: Visit health endpoints listed above
3. **Documentation**: Review `/docs/` directory
4. **Issues**: Check troubleshooting section
5. **Support**: Contact system administrator

### Useful Commands

```bash
# Quick restart
docker-compose restart

# Update to latest images  
docker-compose pull && docker-compose up -d

# Backup before updates
cd scripts && python backup.py --full

# Monitor resource usage
watch docker stats

# Clean up unused resources
docker system prune -f
```

---

## 🔄 Updates & Upgrades

### Update Process

```bash
# 1. Backup current system
cd scripts && python backup.py --full

# 2. Pull latest code
git pull origin main

# 3. Update containers  
docker-compose pull
docker-compose up -d

# 4. Run database migrations (if needed)
docker-compose exec backend python -m app.migrate

# 5. Verify services
curl http://localhost:8000/health
```

### Version Compatibility

Check `CHANGELOG.md` for:
- Breaking changes
- Migration requirements  
- New features
- Deprecation notices

---

## 🔧 Troubleshooting

### Common Issues

#### Connection Refused Error
**Issue**: `HTTPConnectionPool(host='localhost', port=8000): Connection refused`

**Solution**:
```bash
# Check if all containers are running
docker compose ps

# Restart backend service
docker compose restart backend

# Check backend logs
docker compose logs backend

# Verify correct ports are used
curl http://localhost:8001/settings
```

#### SQLAlchemy Metadata Error
**Issue**: `Attribute name 'metadata' is reserved`

**Solution**: Already fixed in latest version. If you encounter this:
```bash
# Pull latest updates
git pull origin main
docker compose build backend
docker compose restart backend
```

#### Missing Activity Logs/Records in Sidebar
**Issue**: Navigation items not visible in frontend

**Solution**: Already fixed in latest version. Restart frontend:
```bash
docker compose restart frontend
```

#### Authentication/JWT Issues
**Issue**: Login failures or token errors

**Solution**:
```bash
# Check JWT secret is set
docker compose exec backend python -c "
import os
print('JWT_SECRET_KEY:', os.getenv('JWT_SECRET_KEY', 'NOT SET'))
"

# Generate new secret for production
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
docker compose restart backend
```

### Service Health Checks

```bash
# Check all services
docker compose ps

# Test backend API
curl http://localhost:8001/settings

# Test authentication endpoint  
curl -X POST "http://localhost:8001/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "test"}'

# Check export feature status
curl http://localhost:8001/projects/1/export-status
```

### Performance Tuning

```bash
# Check container resource usage
docker stats

# Scale services if needed
docker compose up -d --scale ollama=2

# Monitor logs for performance issues  
docker compose logs -f --tail=100
```

---

**🎉 Installation Complete!** 

Your Docsmait installation is now ready. Visit http://localhost:8501 to start using the application.

For additional help, refer to the documentation in the `/docs/` directory or contact your system administrator.