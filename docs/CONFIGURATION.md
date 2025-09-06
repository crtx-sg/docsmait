# Docsmait Configuration Guide

This document explains the configuration system for Docsmait, including environment-specific configurations and how to manage hardcoded values.

## Configuration Architecture

Docsmait uses a centralized configuration system to eliminate hardcoded values and provide environment-specific settings. The configuration is organized in the following structure:

```
config/
├── __init__.py           # Configuration package
└── environments.py       # Environment-specific configurations
```

## Environment Types

Docsmait supports different environment configurations:

### 1. Development Environment
- **Purpose**: Local development on host system
- **Database**: External port access (localhost:5433)
- **Services**: External port access for debugging
- **Usage**: `DOCSMAIT_ENV=development`

### 2. Docker Environment
- **Purpose**: Running within Docker containers
- **Database**: Internal Docker network (docsmait_postgres:5432)
- **Services**: Internal container networking
- **Usage**: `DOCSMAIT_ENV=docker`

### 3. Testing Environment
- **Purpose**: Automated testing and CI/CD
- **Database**: Test database with reduced timeouts
- **Services**: Configured for testing scenarios
- **Usage**: `DOCSMAIT_ENV=testing`

### 4. Production Environment
- **Purpose**: Production deployment
- **Database**: Production database settings
- **Services**: Enhanced security and performance settings
- **Usage**: `DOCSMAIT_ENV=production`

## Configuration Usage

### Importing Configuration

```python
# Import the centralized configuration
from config.environments import config

# Use configuration values
database_url = config.database_url
backend_url = config.backend_url
max_response_length = config.MAX_CHAT_RESPONSE_LENGTH
```

### Environment Variables

All configuration values can be overridden using environment variables:

```bash
# Set environment type
export DOCSMAIT_ENV=development

# Override specific values
export DB_HOST=localhost
export DB_PORT=5433
export BACKEND_URL=http://localhost:8001
```

## Key Configuration Categories

### Database Configuration
- **DB_USER**: Database username
- **DB_PASSWORD**: Database password
- **DB_HOST**: Database host (environment-specific)
- **DB_PORT**: Database port (environment-specific)
- **DB_NAME**: Database name

### Service Configuration
- **BACKEND_SERVICE_NAME**: Backend container name
- **POSTGRES_SERVICE_NAME**: PostgreSQL container name
- **QDRANT_SERVICE_NAME**: Qdrant vector database container name
- **OLLAMA_SERVICE_NAME**: Ollama AI service container name

### Network Configuration
- **BACKEND_HOST/PORT**: Backend service endpoints
- **FRONTEND_HOST/PORT**: Frontend service endpoints
- **QDRANT_HOST/PORT**: Qdrant service endpoints
- **OLLAMA_HOST/PORT**: Ollama service endpoints

### Performance Configuration
- **MAX_CHAT_RESPONSE_LENGTH**: Maximum length of AI responses
- **MAX_CHAT_RESPONSES_PER_SESSION**: Maximum responses per session
- **DEFAULT_TIMEOUT**: Default request timeout
- **KB_REQUEST_TIMEOUT**: Knowledge base request timeout

### Security Configuration
- **JWT_SECRET_KEY**: JWT token secret
- **ACCESS_TOKEN_EXPIRE_MINUTES**: Token expiration time
- **MIN_PASSWORD_LENGTH**: Minimum password length
- **MAX_LOGIN_ATTEMPTS**: Maximum login attempts

## Migration from Hardcoded Values

### Before (Hardcoded)
```python
# Hardcoded values in various files
BACKEND_URL = "http://localhost:8000"
DB_PASSWORD = "docsmait_password"
MAX_RESPONSE_LENGTH = 5000
```

### After (Centralized)
```python
# Centralized configuration
from config.environments import config

backend_url = config.backend_url
db_password = config.DB_PASSWORD
max_response_length = config.MAX_CHAT_RESPONSE_LENGTH
```

## Environment Setup

### Development Environment
```bash
# .env file
DOCSMAIT_ENV=development
DB_HOST=localhost
DB_PORT=5433
BACKEND_HOST=localhost
BACKEND_PORT=8001
QDRANT_HOST=localhost
QDRANT_PORT=6335
```

### Docker Environment
```bash
# .env file
DOCSMAIT_ENV=docker
DB_HOST=docsmait_postgres
DB_PORT=5432
BACKEND_HOST=backend
BACKEND_PORT=8000
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

### Production Environment
```bash
# .env file
DOCSMAIT_ENV=production
DB_HOST=your-production-db-host
DB_PASSWORD=your-secure-password
JWT_SECRET_KEY=your-secure-jwt-secret
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

## Configuration Validation

The configuration system includes validation and fallbacks:

1. **Environment Detection**: Automatically detects environment type
2. **Fallback Values**: Provides sensible defaults for all settings
3. **Import Fallbacks**: Graceful degradation when config module isn't available
4. **Type Validation**: Ensures configuration values are correct types

## Backward Compatibility

To ensure smooth migration, the system maintains backward compatibility:

- **Legacy Config Files**: Old config files still work with fallback mechanisms
- **Environment Variables**: All existing environment variables continue to work
- **API Compatibility**: No changes to existing APIs or interfaces

## Best Practices

### 1. Use Environment Variables
```bash
# Production secrets should always be environment variables
export JWT_SECRET_KEY="your-production-secret"
export DB_PASSWORD="your-production-password"
```

### 2. Environment-Specific Overrides
```python
# Override values for specific environments
if config.DOCSMAIT_ENV == 'production':
    # Additional production-specific logic
    pass
```

### 3. Import Pattern
```python
# Always import from centralized config
try:
    from config.environments import config
    backend_url = config.backend_url
except ImportError:
    # Fallback for testing/development
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8001")
```

### 4. Container Naming
Use consistent service names across all configurations:
- `docsmait_backend`
- `docsmait_frontend`
- `docsmait_postgres`
- `docsmait_qdrant`

## Troubleshooting

### Common Issues

1. **ImportError**: Config module not found
   - **Solution**: Ensure `config/` directory is in Python path
   - **Fallback**: Use environment variables directly

2. **Connection Refused**: Service not accessible
   - **Check**: Environment-specific host/port configuration
   - **Verify**: Docker network configuration

3. **Authentication Errors**: Invalid credentials
   - **Check**: Environment variables are properly set
   - **Verify**: Secrets are not committed to version control

### Debug Configuration

```python
from config.environments import config

print(f"Environment: {config.DOCSMAIT_ENV if hasattr(config, 'DOCSMAIT_ENV') else 'Not set'}")
print(f"Database URL: {config.database_url}")
print(f"Backend URL: {config.backend_url}")
print(f"Environment type: {type(config).__name__}")
```

## Security Considerations

1. **Never Commit Secrets**: Use `.env` files that are gitignored
2. **Rotate Secrets**: Regularly update JWT secrets and database passwords
3. **Environment Isolation**: Use different credentials for each environment
4. **Access Control**: Limit access to production configuration files

## Configuration Schema

The complete configuration schema is available in `config/environments.py`. Key configuration classes:

- `BaseConfig`: Common configuration for all environments
- `DevelopmentConfig`: Development-specific settings
- `DockerConfig`: Container-specific settings
- `TestingConfig`: Testing-specific settings
- `ProductionConfig`: Production-specific settings

For the complete list of available configuration options, see the `config/environments.py` file.