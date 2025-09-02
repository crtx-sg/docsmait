# Docker Debugging & Management Commands for Docsmait

**Generated**: September 2, 2025  
**Purpose**: Reference for debugging, inspection, and maintenance commands

---

## 📦 Docker Container Management

### Basic Container Operations
```bash
# List all containers with status
docker compose ps

# Show all containers (including stopped)
docker ps -a

# Check specific service status
docker compose ps backend
docker compose ps frontend

# Start/Stop/Restart specific services
docker compose start backend
docker compose stop frontend
docker compose restart backend

# Restart all services
docker compose restart

# Force recreate containers
docker compose up -d --force-recreate

# Remove and recreate specific service
docker compose down frontend
docker compose up -d frontend
```

### Container Inspection & Details
```bash
# Inspect container configuration
docker inspect docsmait_backend
docker inspect docsmait_frontend
docker inspect docsmait_postgres

# Show container resource usage
docker stats
docker stats docsmait_backend docsmait_frontend

# Show container processes
docker top docsmait_backend
docker top docsmait_postgres

# Show container port mappings
docker port docsmait_backend
docker port docsmait_frontend
```

---

## 📋 Container Logs & Debugging

### Log Access Commands
```bash
# View real-time logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs backend
docker compose logs frontend
docker compose logs postgres

# Follow logs with timestamps
docker compose logs -f --timestamps backend

# Show last N lines of logs
docker compose logs --tail=50 backend
docker compose logs --tail=100 frontend

# View logs since specific time
docker compose logs --since="2025-09-02T10:00:00" backend

# Export logs to file
docker compose logs backend > backend_debug.log
docker compose logs > all_services.log
```

### Container Shell Access
```bash
# Access backend container bash
docker exec -it docsmait_backend bash
docker exec -it docsmait_backend /bin/bash

# Access frontend container  
docker exec -it docsmait_frontend bash

# Access postgres container
docker exec -it docsmait_postgres bash

# Run commands without entering shell
docker exec docsmait_backend ls -la /app
docker exec docsmait_backend python --version
docker exec docsmait_backend pip list

# Check Python environment in backend
docker exec docsmait_backend python -c "import sys; print(sys.path)"
docker exec docsmait_backend python -c "import os; print(os.environ)"
```

---

## 🗄️ PostgreSQL Database Access & Management

### Database Connection Commands
```bash
# Connect to PostgreSQL as docsmait_user
docker exec -it docsmait_postgres psql -U docsmait_user -d docsmait

# Connect as postgres superuser
docker exec -it docsmait_postgres psql -U postgres

# Connect with specific database
docker exec -it docsmait_postgres psql -U docsmait_user -d docsmait

# Run SQL commands directly
docker exec -it docsmait_postgres psql -U docsmait_user -d docsmait -c "SELECT version();"
```

### Database Inspection Commands (inside psql)
```sql
-- List all databases
\l

-- Connect to docsmait database
\c docsmait

-- List all tables
\dt

-- List tables with details
\dt+

-- Describe table structure
\d users
\d projects
\d documents
\d activity_logs

-- List all schemas
\dn

-- List all indexes
\di

-- Show table sizes
\dt+

-- List all sequences
\ds

-- Show database size
SELECT pg_database_size('docsmait');

-- Show table row counts
SELECT schemaname,tablename,n_tup_ins,n_tup_upd,n_tup_del 
FROM pg_stat_user_tables;

-- Check active connections
SELECT * FROM pg_stat_activity WHERE datname = 'docsmait';
```

### Database Backup & Restore
```bash
# Create database backup
docker exec docsmait_postgres pg_dump -U docsmait_user -d docsmait > docsmait_backup.sql

# Create compressed backup
docker exec docsmait_postgres pg_dump -U docsmait_user -d docsmait | gzip > docsmait_backup.sql.gz

# Restore from backup
docker exec -i docsmait_postgres psql -U docsmait_user -d docsmait < docsmait_backup.sql

# Copy backup file into container and restore
docker cp docsmait_backup.sql docsmait_postgres:/tmp/
docker exec docsmait_postgres psql -U docsmait_user -d docsmait -f /tmp/docsmait_backup.sql
```

### Database Troubleshooting
```bash
# Check if database is accepting connections
docker exec docsmait_postgres pg_isready -U docsmait_user -d docsmait

# Check PostgreSQL configuration
docker exec docsmait_postgres cat /var/lib/postgresql/data/postgresql.conf

# View PostgreSQL logs
docker logs docsmait_postgres

# Check disk usage in database container
docker exec docsmait_postgres df -h

# Check database processes
docker exec docsmait_postgres ps aux
```

---

## 🔍 Application-Specific Debugging

### Backend API Testing
```bash
# Test basic API endpoints
curl -s http://localhost:8001/settings
curl -s http://localhost:8001/health
curl -s http://localhost:8001/projects/1/export-status

# Test authentication endpoint
curl -X POST "http://localhost:8001/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "test"}'

# Test API documentation access
curl -s http://localhost:8001/docs

# Check backend environment variables
docker exec docsmait_backend printenv | grep -E "(JWT|DATABASE|OLLAMA|QDRANT)"

# Test Python imports in backend
docker exec docsmait_backend python -c "import reportlab; print('reportlab:', reportlab.Version)"
docker exec docsmait_backend python -c "import sqlalchemy; print('sqlalchemy:', sqlalchemy.__version__)"
docker exec docsmait_backend python -c "import fastapi; print('fastapi:', fastapi.__version__)"
```

### Frontend Connectivity Testing  
```bash
# Test frontend to backend connectivity
docker exec docsmait_frontend python -c "
import requests
try:
    r = requests.get('http://backend:8000/settings')
    print('Backend connection:', r.status_code, r.json())
except Exception as e:
    print('Connection failed:', e)
"

# Check frontend environment variables
docker exec docsmait_frontend printenv | grep BACKEND

# Test frontend Python environment
docker exec docsmait_frontend python -c "import streamlit; print('streamlit:', streamlit.__version__)"
```

### Network & Service Discovery
```bash
# List Docker networks
docker network ls

# Inspect Docsmait network
docker network inspect docsmait_docsmait_network

# Check container network connectivity
docker exec docsmait_frontend ping backend
docker exec docsmait_backend ping postgres
docker exec docsmait_backend ping qdrant

# Test internal service URLs
docker exec docsmait_backend curl -s http://postgres:5432 || echo "Postgres not HTTP accessible"
docker exec docsmait_backend curl -s http://qdrant:6333/collections
docker exec docsmait_backend curl -s http://ollama:11434/api/tags
```

---

## 🧹 Housekeeping & Maintenance Commands

### Container Cleanup
```bash
# Remove stopped containers
docker container prune

# Remove unused images  
docker image prune

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Full system cleanup (use carefully!)
docker system prune -a

# Remove specific service and recreate
docker compose rm -f backend
docker compose up -d backend
```

### Build & Image Management
```bash
# Rebuild specific service
docker compose build backend
docker compose build frontend

# Rebuild without cache
docker compose build --no-cache backend

# Pull latest images
docker compose pull

# Show image sizes
docker images | grep docsmait

# Remove old images
docker rmi docsmait-backend:old
docker rmi docsmait-frontend:old
```

### Volume & Data Management
```bash
# List Docker volumes
docker volume ls

# Inspect specific volume
docker volume inspect docsmait_postgres_data
docker volume inspect docsmait_qdrant_data
docker volume inspect docsmait_ollama_data

# Show volume disk usage
docker system df

# Backup volume data
docker run --rm -v docsmait_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume data
docker run --rm -v docsmait_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

### Performance Monitoring
```bash
# Real-time container stats
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Show container resource limits
docker inspect docsmait_backend | grep -A 5 "Memory"
docker inspect docsmait_backend | grep -A 5 "CpuShares"

# Monitor container events
docker events --filter container=docsmait_backend

# Check container health status
docker inspect --format='{{.State.Health.Status}}' docsmait_postgres
docker inspect --format='{{json .State.Health}}' docsmait_postgres | jq
```

### Configuration & Environment Debugging
```bash
# Show effective Docker Compose configuration
docker compose config

# Validate docker-compose.yml syntax
docker compose config --quiet

# Show environment variables for service
docker compose config --format json | jq '.services.backend.environment'

# Check .env file loading
docker compose config | grep -A 10 environment

# Show all environment variables in container
docker exec docsmait_backend env | sort
```

---

## 🚨 Emergency Debugging Commands

### Service Recovery
```bash
# Hard restart all services
docker compose down
docker compose up -d

# Reset specific service
docker compose stop backend
docker compose rm -f backend  
docker compose up -d backend

# Check service dependencies
docker compose up -d --remove-orphans

# Force recreate with new images
docker compose down
docker compose up -d --force-recreate --build
```

### Data Recovery & Forensics
```bash
# Copy files from container
docker cp docsmait_backend:/app/logs ./backend_logs/
docker cp docsmait_postgres:/var/lib/postgresql/data ./postgres_data_backup/

# Copy files to container
docker cp local_file.txt docsmait_backend:/tmp/

# Create emergency database dump
docker exec docsmait_postgres pg_dumpall -U postgres > emergency_full_backup.sql

# Save container state as image
docker commit docsmait_backend docsmait-backend-debug:$(date +%Y%m%d)
```

### Port & Network Debugging
```bash
# Check port bindings
netstat -tlnp | grep -E "(8001|8501|5433|6335|11435)"

# Test port connectivity from host
nc -zv localhost 8001
nc -zv localhost 8501
nc -zv localhost 5433

# Check firewall (if applicable)
sudo ufw status | grep -E "(8001|8501)"

# Show all Docker port mappings
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

---

## 📝 Logging & Monitoring Scripts

### Automated Health Check
```bash
#!/bin/bash
# health_check.sh
echo "=== Docsmait Health Check ==="
echo "Services Status:"
docker compose ps

echo -e "\nAPI Endpoints:"
curl -s http://localhost:8001/settings && echo " ✓ Backend API"
curl -s http://localhost:8501 > /dev/null && echo " ✓ Frontend"

echo -e "\nDatabase Status:"
docker exec docsmait_postgres pg_isready -U docsmait_user -d docsmait && echo " ✓ PostgreSQL"

echo -e "\nResource Usage:"
docker stats --no-stream --format "{{.Name}}: CPU {{.CPUPerc}} | Memory {{.MemUsage}}"
```

### Log Collection Script
```bash
#!/bin/bash
# collect_logs.sh
LOG_DIR="./debug_logs_$(date +%Y%m%d_%H%M%S)"
mkdir -p $LOG_DIR

echo "Collecting logs to $LOG_DIR"
docker compose logs backend > $LOG_DIR/backend.log
docker compose logs frontend > $LOG_DIR/frontend.log  
docker compose logs postgres > $LOG_DIR/postgres.log
docker compose logs qdrant > $LOG_DIR/qdrant.log
docker compose logs ollama > $LOG_DIR/ollama.log

docker compose ps > $LOG_DIR/services_status.txt
docker stats --no-stream > $LOG_DIR/resource_usage.txt

echo "Logs collected in $LOG_DIR"
```

---

## 🔧 Most Frequently Used Commands

**Quick Reference for daily operations:**

```bash
# Check everything is running
docker compose ps

# View backend logs  
docker compose logs -f backend

# Restart backend after changes
docker compose restart backend

# Test API is working
curl -s http://localhost:8001/settings

# Access database
docker exec -it docsmait_postgres psql -U docsmait_user -d docsmait

# Check resource usage
docker stats --no-stream

# Emergency restart all
docker compose restart

# View all logs
docker compose logs -f --tail=50
```

---

**💡 Tips:**
- Use `docker compose logs -f` to follow logs in real-time during debugging
- Always check `docker compose ps` first to see service status  
- Use `docker exec -it container_name bash` for interactive debugging
- Keep regular backups with `pg_dump` before making changes
- Monitor resource usage with `docker stats` during heavy operations

---

*Last updated: September 2, 2025*  
*Generated during Docsmait deployment debugging session*