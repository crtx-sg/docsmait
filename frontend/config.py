# frontend/config.py
"""
Frontend Configuration Constants

This file contains configuration constants used by the frontend application.
Environment variables override default values.
"""

import os

# Backend Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

# Knowledge Base Configuration
DEFAULT_COLLECTION_NAME = os.getenv("DEFAULT_COLLECTION_NAME", "knowledge_base")

# UI Configuration
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "120"))
DEFAULT_MAX_RESPONSE_LENGTH = int(os.getenv("DEFAULT_MAX_RESPONSE_LENGTH", "2000"))
DEFAULT_CONTEXT_WINDOW = int(os.getenv("DEFAULT_CONTEXT_WINDOW", "4000"))

# Interactive Table Configuration
DATAFRAME_HEIGHT = int(os.getenv("DATAFRAME_HEIGHT", "400"))
DATAFRAME_SELECTION_MODE = os.getenv("DATAFRAME_SELECTION_MODE", "single-row")
TABLE_PAGE_SIZE = int(os.getenv("TABLE_PAGE_SIZE", "20"))
TABLE_REFRESH_INTERVAL = int(os.getenv("TABLE_REFRESH_INTERVAL", "30"))  # seconds

# Form Configuration
FORM_VALIDATION_DELAY = int(os.getenv("FORM_VALIDATION_DELAY", "500"))  # milliseconds
TEXTAREA_HEIGHT = int(os.getenv("TEXTAREA_HEIGHT", "100"))
FORM_AUTOSAVE_INTERVAL = int(os.getenv("FORM_AUTOSAVE_INTERVAL", "60"))  # seconds

# Export Configuration
DEFAULT_EXPORT_FORMAT = os.getenv("DEFAULT_EXPORT_FORMAT", "csv")
EXPORT_BATCH_SIZE = int(os.getenv("EXPORT_BATCH_SIZE", "1000"))
MAX_EXPORT_RECORDS = int(os.getenv("MAX_EXPORT_RECORDS", "10000"))

# Model Configuration
DEFAULT_MODELS = os.getenv("DEFAULT_MODELS", "qwen2:7b,qwen2:1.5b,qwen2:0.5b").split(",")
DEFAULT_EMBEDDING_MODELS = os.getenv("DEFAULT_EMBEDDING_MODELS", "nomic-embed-text:latest,nomic-embed-text").split(",")

# Compliance Configuration
DEFAULT_COMPLIANCE_STANDARDS = os.getenv("DEFAULT_COMPLIANCE_STANDARDS", "ISO 13485:2016,ISO 14971:2019,IEC 62304:2006,FDA 21 CFR Part 820").split(",")
DEFAULT_COMPLIANCE_STANDARD = os.getenv("DEFAULT_COMPLIANCE_STANDARD", "ISO 13485:2016")

# File Processing Configuration  
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
SUPPORTED_FILE_EXTENSIONS = os.getenv("SUPPORTED_FILE_EXTENSIONS", ".txt,.pdf,.docx,.md,.py,.js,.html,.css,.json,.yaml,.yml").split(",")

# Domain Specific Configuration
AUTOMOTIVE_SIL_LEVELS = ["ASIL A", "ASIL B", "ASIL C", "ASIL D"]
INDUSTRIAL_SIL_LEVELS = ["SIL 1", "SIL 2", "SIL 3", "SIL 4"] 
AVIATION_DAL_LEVELS = ["DAL A", "DAL B", "DAL C", "DAL D", "DAL E"]

# Design Record Configuration
DEFAULT_RISK_LEVELS = ["low", "medium", "high", "critical"]
DEFAULT_SEVERITY_LEVELS = ["negligible", "minor", "serious", "critical", "catastrophic"]
DEFAULT_PROBABILITY_LEVELS = ["improbable", "remote", "occasional", "probable", "frequent"]
DEFAULT_VERIFICATION_METHODS = ["test", "inspection", "analysis", "demonstration"]
DEFAULT_REQUIREMENT_CATEGORIES = ["functional", "performance", "safety", "usability", "interface", "design", "implementation"]
DEFAULT_PRIORITY_LEVELS = ["low", "medium", "high", "critical"]

# Records Management Configuration
DEFAULT_APPROVAL_STATUSES = ["pending", "approved", "conditional", "rejected"]
DEFAULT_SUPPLIER_RATINGS = ["not_assessed", "poor", "fair", "good", "excellent"]
DEFAULT_STOCK_STATUSES = ["in_stock", "quarantined", "expired", "disposed", "on_order"]
DEFAULT_EQUIPMENT_STATUSES = ["calibrated", "due", "overdue", "out_of_service"]
DEFAULT_INVESTIGATION_STATUSES = ["open", "in_progress", "completed", "closed"]
DEFAULT_NC_SEVERITIES = ["critical", "major", "minor"]
DEFAULT_NC_DISPOSITIONS = ["use_as_is", "rework", "scrap", "return"]

# Compliance Standards
MEDICAL_DEVICE_STANDARDS = ["ISO 13485:2016", "ISO 14971:2019", "IEC 62304:2006", "FDA 21 CFR Part 820"]
AUTOMOTIVE_STANDARDS = ["ISO 26262", "ASPICE", "MISRA C"] 
INDUSTRIAL_STANDARDS = ["IEC 61508", "IEC 61511", "DO-178C"]
AVIATION_STANDARDS = ["DO-178C", "DO-254", "ARP4754A"]

# User Management Configuration
MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
PASSWORD_COMPLEXITY_REQUIRED = os.getenv("PASSWORD_COMPLEXITY_REQUIRED", "false").lower() == "true"
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))

# Training System Configuration
DEFAULT_TRAINING_DOCUMENT_TYPES = [
    "Planning Documents", "Process Documents", "Specifications", "Records",
    "Templates", "Policies", "Manuals", "SOPs", "Work Instructions", 
    "Quality Plans", "Risk Assessments", "Test Reports", "Audit Reports"
]
TRAINING_PASS_PERCENTAGE = int(os.getenv("TRAINING_PASS_PERCENTAGE", "80"))
DEFAULT_ASSESSMENT_QUESTIONS = int(os.getenv("DEFAULT_ASSESSMENT_QUESTIONS", "20"))
MIN_ASSESSMENT_QUESTIONS = int(os.getenv("MIN_ASSESSMENT_QUESTIONS", "5"))
MAX_ASSESSMENT_QUESTIONS = int(os.getenv("MAX_ASSESSMENT_QUESTIONS", "50"))

# Download and Export Configuration
MARKDOWN_TRUNCATE_LENGTH = int(os.getenv("MARKDOWN_TRUNCATE_LENGTH", "200"))
CSV_ENCODING = os.getenv("CSV_ENCODING", "utf-8")
EXPORT_FILENAME_FORMAT = os.getenv("EXPORT_FILENAME_FORMAT", "%Y%m%d_%H%M%S")

# UI Element Heights and Sizes
TEXT_AREA_SMALL_HEIGHT = int(os.getenv("TEXT_AREA_SMALL_HEIGHT", "80"))
TEXT_AREA_MEDIUM_HEIGHT = int(os.getenv("TEXT_AREA_MEDIUM_HEIGHT", "100"))
TEXT_AREA_LARGE_HEIGHT = int(os.getenv("TEXT_AREA_LARGE_HEIGHT", "150"))
DATAFRAME_DISPLAY_HEIGHT = int(os.getenv("DATAFRAME_DISPLAY_HEIGHT", "300"))
EDITOR_HEIGHT = int(os.getenv("EDITOR_HEIGHT", "400"))

# CSS and Styling Configuration
COMPACT_FONT_SIZE = int(os.getenv("COMPACT_FONT_SIZE", "14"))
COMPACT_PADDING = os.getenv("COMPACT_PADDING", "0.25rem 0.5rem")
COMPACT_MARGIN = os.getenv("COMPACT_MARGIN", "0.5rem")
TAB_GAP = os.getenv("TAB_GAP", "8px")