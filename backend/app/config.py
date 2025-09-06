# backend/app/config.py
"""
Docsmait Backend Configuration File

This file provides backend-specific configuration by extending the centralized
configuration system. All hardcoded values have been moved to config/environments.py

DEPRECATED: This file is maintained for backward compatibility.
New code should use config.environments instead.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Import centralized configuration
try:
    # Add parent directory to path to import config module
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(parent_dir)
    from config.environments import config as env_config
except ImportError:
    # Fallback for development/testing when config module isn't available
    env_config = None

class Config:
    """Main configuration class for Docsmait application"""
    
    def __getattribute__(self, name):
        """Delegate to centralized config when available, fallback to local definitions"""
        # First check if centralized config is available and has the attribute
        if env_config and hasattr(env_config, name):
            return getattr(env_config, name)
        # Otherwise use the local definition
        return super().__getattribute__(name)
    
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
        if env_config and hasattr(env_config, 'database_url'):
            return env_config.database_url
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
    
    # === Chat Response Limits ===
    MAX_CHAT_RESPONSES_PER_SESSION: int = int(os.getenv("MAX_CHAT_RESPONSES_PER_SESSION", "20"))
    MAX_CHAT_RESPONSE_LENGTH: int = int(os.getenv("MAX_CHAT_RESPONSE_LENGTH", "5000"))
    
    # === KB Service Configuration ===
    KB_TEXT_PREVIEW_LENGTH: int = int(os.getenv("KB_TEXT_PREVIEW_LENGTH", "200"))
    KB_ERROR_MSG_QUERY_NONE: str = os.getenv("KB_ERROR_MSG_QUERY_NONE", "Error: Query cannot be None")
    KB_ERROR_MSG_QUERY_EMPTY: str = os.getenv("KB_ERROR_MSG_QUERY_EMPTY", "Error: Query cannot be empty")
    KB_MAX_ASSESSMENT_QUESTIONS: int = int(os.getenv("KB_MAX_ASSESSMENT_QUESTIONS", "20"))
    KB_AI_MAX_TOKENS: int = int(os.getenv("KB_AI_MAX_TOKENS", "2000"))
    KB_OVERVIEW_QUERY_LIMIT: int = int(os.getenv("KB_OVERVIEW_QUERY_LIMIT", "20"))
    
    # === Activity Logging Configuration ===
    ACTIVITY_LOG_RETENTION_DAYS: int = int(os.getenv("ACTIVITY_LOG_RETENTION_DAYS", "365"))
    LOG_IP_ADDRESSES: bool = os.getenv("LOG_IP_ADDRESSES", "true").lower() == "true"
    LOG_USER_AGENTS: bool = os.getenv("LOG_USER_AGENTS", "true").lower() == "true"
    ACTIVITY_LOG_BATCH_SIZE: int = int(os.getenv("ACTIVITY_LOG_BATCH_SIZE", "1000"))
    
    # === Design Record Configuration ===
    DEFAULT_RISK_LEVELS: list = ["low", "medium", "high", "critical"]
    DEFAULT_SEVERITY_LEVELS: list = ["negligible", "minor", "serious", "critical", "catastrophic"]
    DEFAULT_PROBABILITY_LEVELS: list = ["improbable", "remote", "occasional", "probable", "frequent"]
    DEFAULT_VERIFICATION_METHODS: list = ["test", "inspection", "analysis", "demonstration"]
    REQUIREMENT_ID_PREFIX: str = os.getenv("REQUIREMENT_ID_PREFIX", "REQ")
    HAZARD_ID_PREFIX: str = os.getenv("HAZARD_ID_PREFIX", "HAZ")
    
    # === Records Management Configuration ===
    SUPPLIER_ID_PREFIX: str = os.getenv("SUPPLIER_ID_PREFIX", "SUP")
    PART_NUMBER_PREFIX: str = os.getenv("PART_NUMBER_PREFIX", "PRT")
    EQUIPMENT_ID_PREFIX: str = os.getenv("EQUIPMENT_ID_PREFIX", "EQP")
    COMPLAINT_ID_PREFIX: str = os.getenv("COMPLAINT_ID_PREFIX", "COMP")
    NC_ID_PREFIX: str = os.getenv("NC_ID_PREFIX", "NC")
    DEFAULT_CALIBRATION_FREQUENCY_DAYS: int = int(os.getenv("DEFAULT_CALIBRATION_FREQUENCY_DAYS", "365"))
    
    # === Export Configuration ===
    DEFAULT_EXPORT_FORMAT: str = os.getenv("DEFAULT_EXPORT_FORMAT", "csv")
    EXPORT_BATCH_SIZE: int = int(os.getenv("EXPORT_BATCH_SIZE", "1000"))
    MAX_EXPORT_RECORDS: int = int(os.getenv("MAX_EXPORT_RECORDS", "10000"))
    EXPORT_TIMEOUT_SECONDS: int = int(os.getenv("EXPORT_TIMEOUT_SECONDS", "300"))
    
    # === Compliance Standards ===
    MEDICAL_DEVICE_STANDARDS: list = ["ISO 13485:2016", "ISO 14971:2019", "IEC 62304:2006", "FDA 21 CFR Part 820"]
    AUTOMOTIVE_STANDARDS: list = ["ISO 26262", "ASPICE", "MISRA C"]
    INDUSTRIAL_STANDARDS: list = ["IEC 61508", "IEC 61511", "DO-178C"]
    AVIATION_STANDARDS: list = ["DO-178C", "DO-254", "ARP4754A"]
    
    
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
    
    # === File System Configuration ===
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp")
    LOG_DIR: str = os.getenv("LOG_DIR", "/app/logs")
    CONFIG_DIR: str = os.getenv("CONFIG_DIR", "/app/config")
    BACKUP_DIR: str = os.getenv("BACKUP_DIR", "/tmp/docsmait_backup")
    RESTORE_DIR: str = os.getenv("RESTORE_DIR", "/tmp/docsmait_restore")
    
    # === UI Configuration ===
    # Form element heights
    TEXTAREA_SMALL_HEIGHT: int = int(os.getenv("TEXTAREA_SMALL_HEIGHT", "80"))
    TEXTAREA_MEDIUM_HEIGHT: int = int(os.getenv("TEXTAREA_MEDIUM_HEIGHT", "100"))
    TEXTAREA_LARGE_HEIGHT: int = int(os.getenv("TEXTAREA_LARGE_HEIGHT", "150"))
    EDITOR_HEIGHT: int = int(os.getenv("EDITOR_HEIGHT", "400"))
    
    # Pagination and limits
    ACTIVITY_LOG_PAGE_SIZES: list = [25, 50, 100, 200]
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "25"))
    MAX_PREVIEW_LENGTH: int = int(os.getenv("MAX_PREVIEW_LENGTH", "1000"))
    
    # === Timeout Configuration ===
    AI_REQUEST_TIMEOUT: int = int(os.getenv("AI_REQUEST_TIMEOUT", "180"))
    API_REQUEST_TIMEOUT: int = int(os.getenv("API_REQUEST_TIMEOUT", "30"))
    DEFAULT_REQUEST_TIMEOUT: int = int(os.getenv("DEFAULT_REQUEST_TIMEOUT", "10"))
    
    # === Issue Management Configuration ===
    ISSUE_TYPES: list = ["Bug", "Feature", "Enhancement", "Task", "Documentation"]
    ISSUE_PRIORITIES: list = ["High", "Medium", "Low"]
    ISSUE_SEVERITIES: list = ["Critical", "Major", "Minor"]
    ISSUE_STATUSES: list = ["open", "in_progress", "closed", "resolved"]
    
    # === Review Workflow Configuration ===
    REVIEW_STATUSES: list = ["pending", "approved", "rejected", "needs_review"]
    TEMPLATE_STATUSES: list = ["active", "draft", "request_review", "approved"]
    
    # === Numeric Input Ranges ===
    SEVERITY_RATING_MIN: int = int(os.getenv("SEVERITY_RATING_MIN", "1"))
    SEVERITY_RATING_MAX: int = int(os.getenv("SEVERITY_RATING_MAX", "10"))
    OCCURRENCE_RATING_MIN: int = int(os.getenv("OCCURRENCE_RATING_MIN", "1"))
    OCCURRENCE_RATING_MAX: int = int(os.getenv("OCCURRENCE_RATING_MAX", "10"))
    DETECTION_RATING_MIN: int = int(os.getenv("DETECTION_RATING_MIN", "1"))
    DETECTION_RATING_MAX: int = int(os.getenv("DETECTION_RATING_MAX", "10"))
    
    # === Database Connection Strings for Scripts ===
    LOCAL_DATABASE_URL: str = os.getenv("LOCAL_DATABASE_URL", "postgresql://docsmait_user:docsmait_password@localhost:5433/docsmait")
    DOCKER_DATABASE_URL: str = os.getenv("DOCKER_DATABASE_URL", "postgresql://docsmait_user:docsmait_password@docsmait_postgres:5432/docsmait")
    
    # === Company Information ===
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "Docsmait")
    COMPANY_WEBSITE: str = os.getenv("COMPANY_WEBSITE", "https://coherentix.com/")
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@docsmait.com")
    
    # === Thread and Performance Configuration ===
    THREAD_JOIN_TIMEOUT: int = int(os.getenv("THREAD_JOIN_TIMEOUT", "30"))
    SEARCH_LIMIT_MIN: int = int(os.getenv("SEARCH_LIMIT_MIN", "3"))

# Create global config instance
config = Config()