# backend/app/config.py
"""
Docsmait Configuration File

This file contains all configurable settings for the Docsmait application.
Settings can be overridden using environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Main configuration class for Docsmait application"""
    
    # === Database Configuration ===
    # Individual components for flexibility
    DB_USER: str = os.getenv("DB_USER", "docsmait_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "docsmait_password")
    DB_HOST: str = os.getenv("DB_HOST", "docsmait_postgres")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "docsmait")
    
    # Constructed URL (fallback to full URL for backward compatibility)
    @property
    def database_url(self) -> str:
        return os.getenv("DATABASE_URL", f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")
    
    # Keep old attribute for compatibility
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://docsmait_user:docsmait_password@docsmait_postgres:5432/docsmait")
    
    # === Authentication Configuration ===
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # === AI/LLM Configuration (moved to ai_config.py) ===
    # AI-specific configuration is now handled by ai_config.py
    # These are kept for backward compatibility only
    GENERAL_PURPOSE_LLM: str = os.getenv("GENERAL_PURPOSE_LLM", "qwen2:7b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    
    # === Vector Database Configuration ===
    VECTOR_DB: str = os.getenv("VECTOR_DB", "qdrant")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    
    # === Knowledge Base Configuration ===
    DEFAULT_CHUNK_SIZE: int = int(os.getenv("DEFAULT_CHUNK_SIZE", "1000"))
    DEFAULT_COLLECTION_NAME: str = os.getenv("DEFAULT_COLLECTION_NAME", "knowledge_base")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    SUPPORTED_FILE_TYPES: list = [
        "text/plain",
        "application/pdf", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
        "text/html"
    ]
    
    # === Vector Embedding Configuration ===
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))
    DEFAULT_EMBEDDING_MODEL: str = os.getenv("DEFAULT_EMBEDDING_MODEL", "nomic-embed-text")
    
    # === LLM Configuration ===
    DEFAULT_CHAT_MODEL: str = os.getenv("DEFAULT_CHAT_MODEL", "qwen2:1.5b")
    AI_TIMEOUT: int = int(os.getenv("AI_TIMEOUT", "120"))
    MAX_RESPONSE_LENGTH: int = int(os.getenv("MAX_RESPONSE_LENGTH", "2000"))
    AI_CONTEXT_WINDOW: int = int(os.getenv("AI_CONTEXT_WINDOW", "4000"))
    SHOW_PROMPT: bool = os.getenv("SHOW_PROMPT", "true").lower() == "true"
    AVAILABLE_MODELS: list = [
        os.getenv("MODEL_1", "qwen2:7b"),
        os.getenv("MODEL_2", "llama3:latest"),
        os.getenv("MODEL_3", "gemma:7b"),
        os.getenv("MODEL_4", "mistral:latest"),
        os.getenv("MODEL_5", "codellama:7b")
    ]
    
    # === RAG Configuration ===
    RAG_SIMILARITY_SEARCH_LIMIT: int = int(os.getenv("RAG_SIMILARITY_SEARCH_LIMIT", "5"))
    RAG_MIN_CHUNK_LENGTH: int = int(os.getenv("RAG_MIN_CHUNK_LENGTH", "50"))
    
    # === Usage Tracking Configuration ===
    TRACK_USAGE: bool = os.getenv("TRACK_USAGE", "true").lower() == "true"
    TRACK_FEEDBACK: bool = os.getenv("TRACK_FEEDBACK", "true").lower() == "true"
    LOG_PROMPTS: bool = os.getenv("LOG_PROMPTS", "true").lower() == "true"
    USAGE_RETENTION_DAYS: int = int(os.getenv("USAGE_RETENTION_DAYS", "90"))
    
    
    # === API Configuration ===
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "False").lower() == "true"
    
    # === Frontend Configuration ===
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8501")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://backend:8000")
    
    # === Logging Configuration ===
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "/app/logs/docsmait.log")

# Create global config instance
config = Config()