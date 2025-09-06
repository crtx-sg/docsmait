# Docsmait Fresh Installation Guide

This guide covers setting up Docsmait from scratch, ensuring the database and default users are properly configured.

## Quick Start (Docker)

### 1. Start the containers
```bash
docker compose up -d
```

### 2. Run the setup script
```bash
# Run the Docker setup script to initialize database and create admin user
docker exec docsmait_backend python setup_docker.py --skip-confirmation
```

### 3. Access the application
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Login**: Use email `admin@docsmait.com` with password `admin123`

## Detailed Setup Options

### Option 1: Automated Setup (Recommended)

Use the Docker setup script with custom options:

```bash
# Basic setup with defaults
docker exec docsmait_backend python setup_docker.py --skip-confirmation

# Custom admin credentials
docker exec docsmait_backend python setup_docker.py \
    --admin-username "myadmin" \
    --admin-email "admin@mycompany.com" \
    --admin-password "mypassword123" \
    --skip-confirmation

# Force recreate admin user if already exists
docker exec docsmait_backend python setup_docker.py --force-recreate --skip-confirmation
```

### Option 2: Manual Database Setup

If you prefer manual setup or troubleshooting:

```bash
# 1. Initialize database tables only
docker exec docsmait_backend python -c "from app.init_db import create_tables; create_tables()"

# 2. Create admin user manually
docker exec docsmait_backend python -c "
from app.init_db import create_default_admin_user
import os
os.environ['DEFAULT_ADMIN_USERNAME'] = 'admin'
os.environ['DEFAULT_ADMIN_EMAIL'] = 'admin@docsmait.com'
os.environ['DEFAULT_ADMIN_PASSWORD'] = 'admin123'
create_default_admin_user()
"
```

### Option 3: Create Additional Users

```bash
# Create a regular user
docker exec docsmait_backend python setup_docker.py --create-user "johndoe" "john@example.com" "password123"

# Create an admin user
docker exec docsmait_backend python setup_docker.py --create-admin "jane" "jane@example.com" "securepass"
```

## Verification

### Check Installation Status
```bash
# Verify database setup
docker exec docsmait_backend python setup_docker.py --verify-only

# Check what users exist
docker exec docsmait_backend python -c "
from app.database_config import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT id, username, email, is_admin FROM users'))
    for user in result.fetchall():
        print(f'ID: {user[0]}, User: {user[1]}, Email: {user[2]}, Admin: {user[3]}')
"
```

## Troubleshooting

### Database Connection Issues
```bash
# Check if containers are running
docker ps

# Check backend logs
docker logs docsmait_backend

# Check PostgreSQL logs
docker logs docsmait_postgres

# Restart containers if needed
docker compose restart
```

### Reset Everything (Nuclear Option)
```bash
# Stop containers and remove volumes
docker compose down -v

# Remove named volumes
docker volume rm docsmait_postgres_data docsmait_qdrant_data

# Start fresh
docker compose up -d

# Run setup
docker exec docsmait_backend python setup_docker.py --skip-confirmation
```

### Common Issues

1. **"relation users does not exist"**
   - Run: `docker exec docsmait_backend python setup_docker.py --skip-confirmation`

2. **"could not translate host name docsmait_postgres"**
   - Make sure you're running commands inside the Docker container
   - Use `docker exec docsmait_backend` prefix

3. **Login fails with "Incorrect email or password"**
   - Make sure to use EMAIL for login, not username
   - Default: email `admin@docsmait.com`, password `admin123`

4. **Tables exist but no admin user**
   - Run: `docker exec docsmait_backend python setup_docker.py --force-recreate --skip-confirmation`

## Environment Variables

You can customize the default admin user by setting environment variables:

```bash
# In docker-compose.yml or .env file
DEFAULT_ADMIN_USERNAME=myadmin
DEFAULT_ADMIN_EMAIL=admin@mycompany.com
DEFAULT_ADMIN_PASSWORD=mysecurepassword
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Change default passwords** immediately after first login
2. **Use strong passwords** in production environments
3. **Secure your database** with proper network configuration
4. **Regular backups** are recommended for production data
5. **Monitor access logs** for suspicious activity

## Default Credentials

After fresh installation:

| Field | Value |
|-------|-------|
| Username | admin |
| Email | admin@docsmait.com |
| Password | admin123 |
| Admin Rights | Yes (Super Admin) |

**Remember**: Login uses EMAIL, not username!

## Next Steps

After successful setup:

1. Login to the frontend at http://localhost:8501
2. Change the default admin password
3. Configure system settings (SMTP, AI models, etc.)
4. Create projects and start using Docsmait
5. Add additional users as needed

For ongoing administration, see the main documentation or use the setup script's user creation features.
