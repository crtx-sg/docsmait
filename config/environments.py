#!/usr/bin/env python3
"""
Docsmait Environment Configuration

This module provides centralized configuration management for different environments
(development, testing, production). All hardcoded values should be moved here.
"""

import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BaseConfig:
    """Base configuration class with common settings"""
    
    # === Database Configuration ===
    DB_USER: str = os.getenv("DB_USER", "docsmait_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "docsmait_password")
    DB_NAME: str = os.getenv("DB_NAME", "docsmait")
    
    # === Service Configuration ===
    BACKEND_SERVICE_NAME: str = os.getenv("BACKEND_SERVICE_NAME", "docsmait_backend")
    FRONTEND_SERVICE_NAME: str = os.getenv("FRONTEND_SERVICE_NAME", "docsmait_frontend")
    POSTGRES_SERVICE_NAME: str = os.getenv("POSTGRES_SERVICE_NAME", "docsmait_postgres")
    QDRANT_SERVICE_NAME: str = os.getenv("QDRANT_SERVICE_NAME", "docsmait_qdrant")
    OLLAMA_SERVICE_NAME: str = os.getenv("OLLAMA_SERVICE_NAME", "ollama")
    
    # === Container Paths ===
    BACKEND_UPLOAD_PATH: str = "/app/uploads"
    BACKEND_TEMPLATE_PATH: str = "/app/templates"
    FRONTEND_UPLOAD_PATH: str = "/app/uploads"
    QDRANT_STORAGE_PATH: str = "/qdrant/storage"
    
    # === Backup Configuration ===
    DEFAULT_BACKUP_PATH: str = os.getenv("DEFAULT_BACKUP_PATH", "/tmp/docsmait_backup")
    BACKUP_COMPONENTS: List[str] = ["postgres", "qdrant", "configuration", "filesystem"]
    
    # === Timeout Configuration ===
    KB_REQUEST_TIMEOUT: int = int(os.getenv("KB_REQUEST_TIMEOUT", "10"))
    KB_LONG_REQUEST_TIMEOUT: int = int(os.getenv("KB_LONG_REQUEST_TIMEOUT", "30"))
    KB_CHAT_REQUEST_TIMEOUT: int = int(os.getenv("KB_CHAT_REQUEST_TIMEOUT", "30"))
    PDF_GENERATION_TIMEOUT: int = int(os.getenv("PDF_GENERATION_TIMEOUT", "30"))
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "120"))
    
    # === Performance Limits ===
    MAX_CHAT_RESPONSE_LENGTH: int = int(os.getenv("MAX_CHAT_RESPONSE_LENGTH", "5000"))
    MAX_CHAT_RESPONSES_PER_SESSION: int = int(os.getenv("MAX_CHAT_RESPONSES_PER_SESSION", "20"))
    DEFAULT_CHUNK_SIZE: int = int(os.getenv("DEFAULT_CHUNK_SIZE", "1000"))
    DEFAULT_MAX_RESPONSE_LENGTH: int = int(os.getenv("DEFAULT_MAX_RESPONSE_LENGTH", "2000"))
    DEFAULT_CONTEXT_WINDOW: int = int(os.getenv("DEFAULT_CONTEXT_WINDOW", "4000"))
    
    # === Performance Thresholds ===
    PERFORMANCE_EXCELLENT_THRESHOLD: int = 1000  # ms
    PERFORMANCE_GOOD_THRESHOLD: int = 3000       # ms
    PERFORMANCE_POOR_THRESHOLD: int = 5000       # ms
    
    # === File Configuration ===
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    SUPPORTED_FILE_EXTENSIONS: List[str] = os.getenv(
        "SUPPORTED_FILE_EXTENSIONS", 
        ".txt,.pdf,.docx,.md,.py,.js,.html,.css,.json,.yaml,.yml"
    ).split(",")
    
    # === Security Configuration ===
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    MIN_PASSWORD_LENGTH: int = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    
    # === Directory Configuration ===
    TEMP_DIR_PATTERNS: List[str] = ['/tmp', '/var/tmp']
    LOG_FILE_PATTERNS: List[str] = ['docsmait_*.log', '*.log']
    
    # === Export Configuration ===
    DEFAULT_EXPORT_FORMAT: str = os.getenv("DEFAULT_EXPORT_FORMAT", "csv")
    EXPORT_BATCH_SIZE: int = int(os.getenv("EXPORT_BATCH_SIZE", "1000"))
    MAX_EXPORT_RECORDS: int = int(os.getenv("MAX_EXPORT_RECORDS", "10000"))
    MARKDOWN_TRUNCATE_LENGTH: int = int(os.getenv("MARKDOWN_TRUNCATE_LENGTH", "200"))
    CSV_ENCODING: str = os.getenv("CSV_ENCODING", "utf-8")
    EXPORT_FILENAME_FORMAT: str = os.getenv("EXPORT_FILENAME_FORMAT", "%Y%m%d_%H%M%S")


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    
    # === Host System URLs (for development) ===
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5433")  # External port for host access
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "localhost")
    BACKEND_PORT: str = os.getenv("BACKEND_PORT", "8001")  # External port for host access
    FRONTEND_HOST: str = os.getenv("FRONTEND_HOST", "localhost")
    FRONTEND_PORT: str = os.getenv("FRONTEND_PORT", "8501")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: str = os.getenv("QDRANT_PORT", "6335")   # External port for host access
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "localhost")
    OLLAMA_PORT: str = os.getenv("OLLAMA_PORT", "11434")
    
    # === Constructed URLs ===
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property 
    def backend_url(self) -> str:
        return f"http://{self.BACKEND_HOST}:{self.BACKEND_PORT}"
    
    @property
    def frontend_url(self) -> str:
        return f"http://{self.FRONTEND_HOST}:{self.FRONTEND_PORT}"
        
    @property
    def qdrant_url(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
        
    @property
    def ollama_url(self) -> str:
        return f"http://{self.OLLAMA_HOST}:{self.OLLAMA_PORT}"


class DockerConfig(BaseConfig):
    """Docker/Container environment configuration"""
    
    # === Internal Docker Network URLs ===
    DB_HOST: str = os.getenv("DB_HOST", "docsmait_postgres")
    DB_PORT: str = os.getenv("DB_PORT", "5432")  # Internal port
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "backend") 
    BACKEND_PORT: str = os.getenv("BACKEND_PORT", "8000")   # Internal port
    FRONTEND_HOST: str = os.getenv("FRONTEND_HOST", "frontend")
    FRONTEND_PORT: str = os.getenv("FRONTEND_PORT", "8501")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: str = os.getenv("QDRANT_PORT", "6333")     # Internal port
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "ollama")
    OLLAMA_PORT: str = os.getenv("OLLAMA_PORT", "11434")
    
    # === Constructed URLs ===
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property 
    def backend_url(self) -> str:
        return f"http://{self.BACKEND_HOST}:{self.BACKEND_PORT}"
    
    @property
    def frontend_url(self) -> str:
        return f"http://{self.FRONTEND_HOST}:{self.FRONTEND_PORT}"
        
    @property
    def qdrant_url(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
        
    @property
    def ollama_url(self) -> str:
        return f"http://{self.OLLAMA_HOST}:{self.OLLAMA_PORT}"


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    
    # === Test Environment URLs ===
    DB_HOST: str = os.getenv("TEST_DB_HOST", "localhost")
    DB_PORT: str = os.getenv("TEST_DB_PORT", "5433")
    BACKEND_HOST: str = os.getenv("TEST_BACKEND_HOST", "localhost")
    BACKEND_PORT: str = os.getenv("TEST_BACKEND_PORT", "8001")
    FRONTEND_HOST: str = os.getenv("TEST_FRONTEND_HOST", "localhost") 
    FRONTEND_PORT: str = os.getenv("TEST_FRONTEND_PORT", "8501")
    
    # Override for testing
    MAX_CHAT_RESPONSE_LENGTH: int = 1000
    MAX_CHAT_RESPONSES_PER_SESSION: int = 5
    DEFAULT_TIMEOUT: int = 30
    
    # === Constructed URLs ===
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property 
    def backend_url(self) -> str:
        return f"http://{self.BACKEND_HOST}:{self.BACKEND_PORT}"
    
    @property
    def frontend_url(self) -> str:
        return f"http://{self.FRONTEND_HOST}:{self.FRONTEND_PORT}"


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    
    # === Production URLs (will be overridden by environment variables) ===
    DB_HOST: str = os.getenv("DB_HOST", "docsmait_postgres")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "backend")
    BACKEND_PORT: str = os.getenv("BACKEND_PORT", "8000")
    FRONTEND_HOST: str = os.getenv("FRONTEND_HOST", "frontend")
    FRONTEND_PORT: str = os.getenv("FRONTEND_PORT", "8501")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: str = os.getenv("QDRANT_PORT", "6333")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "ollama")
    OLLAMA_PORT: str = os.getenv("OLLAMA_PORT", "11434")
    
    # Enhanced security for production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "3"))
    
    # === Constructed URLs ===
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property 
    def backend_url(self) -> str:
        return f"http://{self.BACKEND_HOST}:{self.BACKEND_PORT}"
    
    @property
    def frontend_url(self) -> str:
        return f"http://{self.FRONTEND_HOST}:{self.FRONTEND_PORT}"
        
    @property
    def qdrant_url(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
        
    @property
    def ollama_url(self) -> str:
        return f"http://{self.OLLAMA_HOST}:{self.OLLAMA_PORT}"


# === Configuration Factory ===
def get_config() -> BaseConfig:
    """Get the appropriate configuration based on environment"""
    env = os.getenv("DOCSMAIT_ENV", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    elif env == "docker":
        return DockerConfig()
    else:  # development
        return DevelopmentConfig()


# === Global Configuration Instance ===
config = get_config()