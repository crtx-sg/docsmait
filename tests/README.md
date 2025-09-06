# Docsmait Automated Test Suite

**Version**: 2.0  
**Created**: September 2025  
**Purpose**: Comprehensive automated testing for Docsmait application

---

## 📋 Test Suite Overview

This test suite provides comprehensive automated testing for all Docsmait functions:

- **API Endpoint Testing**: All backend REST APIs
- **Authentication Testing**: Login, signup, token validation
- **Database Operations**: CRUD operations, data integrity
- **Frontend Integration**: UI components and workflows
- **Knowledge Base**: AI/RAG functionality and KB chat integration
- **Export Functions**: PDF generation and document export
- **Performance Testing**: Load testing and response times
- **Security Testing**: Access controls and data validation

---

## 🚀 Quick Start

### Prerequisites
```bash
# Ensure Docsmait is running
docker compose ps

# Install test dependencies
pip install -r test-requirements.txt
```

### Run All Tests
```bash
# Run complete test suite
./run_all_tests.sh

# Run specific test categories
./run_tests.sh --category=api
./run_tests.sh --category=auth
./run_tests.sh --category=frontend
```

### View Results
```bash
# View latest test results
cat test_results/latest_run.log

# View test report
open test_results/test_report.html
```

---

## 📁 Test Structure

```
tests/
├── README.md                 # This file
├── requirements.txt          # Test dependencies
├── conftest.py              # Test configuration
├── run_all_tests.sh         # Main test runner
├── run_tests.sh             # Selective test runner
├── api/                     # API endpoint tests
├── auth/                    # Authentication tests
├── database/                # Database operation tests
├── frontend/                # Frontend integration tests
├── performance/             # Load and performance tests
├── security/                # Security and validation tests
├── integration/             # End-to-end integration tests
├── utils/                   # Test utilities and helpers
└── test_results/            # Test output and reports
```

---

## 🧪 Test Categories

### 1. API Tests (`/api/`)
- All REST endpoint functionality
- Request/response validation
- Error handling
- Rate limiting
- **NEW**: Knowledge Base chat endpoints (`/kb/query_with_context`)
  - Document context integration
  - AI/LLM query processing
  - Response validation and error handling

### 2. Authentication Tests (`/auth/`)
- User registration/login
- JWT token management
- Role-based access control
- Session management

### 3. Database Tests (`/database/`)
- CRUD operations
- Data integrity
- Migration testing
- Backup/restore

### 4. Frontend Tests (`/frontend/`)
- UI component testing
- User workflow testing
- Browser compatibility
- Responsive design
- **NEW**: Knowledge Base chat UI components
  - Chat interface availability and functionality
  - Mutually exclusive Live Preview vs KB Chat modes
  - Response area and interaction elements

### 5. Performance Tests (`/performance/`)
- Load testing
- Stress testing
- Response time validation
- Resource utilization

### 6. Security Tests (`/security/`)
- Input validation
- SQL injection prevention
- XSS protection
- Access control enforcement

### 7. Integration Tests (`/integration/`)
- End-to-end user workflows
- Multi-service interactions
- Data flow validation
- **NEW**: Knowledge Base chat integration workflows
  - Document creation with KB chat assistance
  - Document review with KB guidance
  - Multi-query chat sessions and error handling
  - Performance testing of KB chat features

---

## 📊 Test Execution

### Environment Setup
```bash
# Set test environment variables
export TEST_BACKEND_URL="http://localhost:8001"
export TEST_FRONTEND_URL="http://localhost:8501"
export TEST_DATABASE_URL="postgresql://docsmait_user:docsmait_password@localhost:5433/docsmait_test"
```

### Running Tests

#### Full Test Suite (Recommended)
```bash
./run_all_tests.sh
```

#### Category-Specific Tests
```bash
./run_tests.sh --category=api          # API tests only
./run_tests.sh --category=auth         # Authentication tests
./run_tests.sh --category=database     # Database tests
./run_tests.sh --category=frontend     # Frontend tests
./run_tests.sh --category=performance  # Performance tests
./run_tests.sh --category=security     # Security tests
./run_tests.sh --category=integration  # Integration tests
```

#### Individual Test Files
```bash
pytest api/test_authentication.py -v
pytest api/test_projects.py -v
pytest database/test_crud_operations.py -v
```

#### With Coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

---

## 📈 Test Results & Reporting

### Automated Reports
Tests automatically generate:
- **HTML Report**: `test_results/test_report.html`
- **JSON Results**: `test_results/results.json`  
- **Coverage Report**: `test_results/coverage_report.html`
- **Performance Metrics**: `test_results/performance_report.json`
- **Log Files**: `test_results/test_execution.log`

### Manual Result Checking
```bash
# Check test exit status
echo $?  # 0 = success, >0 = failures

# View summary
tail -20 test_results/test_execution.log

# Check failed tests
grep -i "failed\|error" test_results/test_execution.log

# Performance metrics
cat test_results/performance_metrics.json
```

---

## 🔧 Configuration

### Test Configuration (`conftest.py`)
```python
# Test database
TEST_DATABASE_URL = "postgresql://test_user:test_pass@localhost:5433/docsmait_test"

# Test user credentials  
TEST_USER_EMAIL = "test@docsmait.com"
TEST_USER_PASSWORD = "SecureTestPassword123!"

# API endpoints
BACKEND_BASE_URL = "http://localhost:8001"
FRONTEND_BASE_URL = "http://localhost:8501"

# Test timeouts
DEFAULT_TIMEOUT = 30
LOAD_TEST_DURATION = 300
```

### Environment Variables
```bash
# Required environment variables
export DOCSMAIT_TEST_MODE=true
export TEST_JWT_SECRET=test_secret_key_for_testing
export TEST_DB_URL=postgresql://test_user:test_pass@localhost:5433/docsmait_test
```

---

## 🚦 Continuous Integration

### GitHub Actions Integration
```yaml
# .github/workflows/test.yml
name: Docsmait Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      - name: Start services
        run: docker compose up -d
      - name: Run tests
        run: cd tests && ./run_all_tests.sh
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: tests/test_results/
```

---

## 🐛 Troubleshooting

### Common Issues

#### Tests Failing to Connect
```bash
# Check services are running
docker compose ps

# Verify API endpoint
curl http://localhost:8001/health

# Check database connection
docker exec docsmait_postgres pg_isready -U docsmait_user
```

#### Permission Issues
```bash
# Make scripts executable
chmod +x run_all_tests.sh
chmod +x run_tests.sh
```

#### Test Database Issues
```bash
# Reset test database
docker exec docsmait_postgres psql -U postgres -c "DROP DATABASE IF EXISTS docsmait_test;"
docker exec docsmait_postgres psql -U postgres -c "CREATE DATABASE docsmait_test OWNER docsmait_user;"
```

#### Frontend Tests Failing
```bash
# Check browser driver
which chromedriver
pip install selenium webdriver-manager
```

---

## 📚 Writing New Tests

### API Test Example
```python
# tests/api/test_new_endpoint.py
import pytest
import requests

def test_new_endpoint():
    response = requests.get(f"{BACKEND_BASE_URL}/new-endpoint")
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

### Database Test Example  
```python
# tests/database/test_new_model.py
import pytest
from app.models import NewModel

def test_create_new_model():
    model = NewModel(name="test")
    db.session.add(model)
    db.session.commit()
    assert model.id is not None
```

### Frontend Test Example
```python
# tests/frontend/test_new_page.py
import pytest
from selenium import webdriver

def test_new_page_loads():
    driver.get(f"{FRONTEND_BASE_URL}/new-page")
    assert "Expected Title" in driver.title
```

---

## 📋 Test Checklist

Before running tests, ensure:
- [ ] Docsmait services are running (`docker compose ps`)
- [ ] Test database is accessible
- [ ] Test user credentials are configured
- [ ] Required test dependencies are installed
- [ ] Adequate system resources (8GB+ RAM recommended)

---

## 📞 Support

For test suite issues:
1. Check test logs in `test_results/test_execution.log`
2. Verify service health with `docker compose ps`
3. Review test configuration in `conftest.py`
4. Check environment variables are set correctly

---

**🎯 Goal**: Achieve 95%+ test coverage and 100% critical path validation

*Last updated: September 2025*