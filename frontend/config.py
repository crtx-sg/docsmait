# frontend/config.py
"""
Frontend Configuration Constants

This file contains configuration constants used by the frontend application.
Environment variables override default values.

DEPRECATED: This file is maintained for backward compatibility.
New code should use config.environments instead.
"""

import os
import sys

# Import centralized configuration
try:
    # Add parent directory to path to import config module
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(parent_dir)
    from config.environments import config as env_config
    # Use centralized config values when available
    BACKEND_URL = env_config.backend_url if env_config and hasattr(env_config, 'backend_url') else os.getenv("BACKEND_URL", "http://localhost:8001")
except ImportError:
    # Fallback for development/testing when config module isn't available
    env_config = None
    # Backend Configuration
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

# Use centralized config when available, otherwise fallback to environment variables
if env_config:
    DEFAULT_COLLECTION_NAME = getattr(env_config, 'DEFAULT_COLLECTION_NAME', os.getenv("DEFAULT_COLLECTION_NAME", "knowledge_base"))
    KB_REQUEST_TIMEOUT = getattr(env_config, 'KB_REQUEST_TIMEOUT', int(os.getenv("KB_REQUEST_TIMEOUT", "10")))
    KB_LONG_REQUEST_TIMEOUT = getattr(env_config, 'KB_LONG_REQUEST_TIMEOUT', int(os.getenv("KB_LONG_REQUEST_TIMEOUT", "30")))
    MAX_CHAT_RESPONSES_PER_SESSION = getattr(env_config, 'MAX_CHAT_RESPONSES_PER_SESSION', int(os.getenv("MAX_CHAT_RESPONSES_PER_SESSION", "20")))
    MAX_CHAT_RESPONSE_LENGTH = getattr(env_config, 'MAX_CHAT_RESPONSE_LENGTH', int(os.getenv("MAX_CHAT_RESPONSE_LENGTH", "5000")))
    KB_CHAT_REQUEST_TIMEOUT = getattr(env_config, 'KB_CHAT_REQUEST_TIMEOUT', int(os.getenv("KB_CHAT_REQUEST_TIMEOUT", "30")))
    PDF_GENERATION_TIMEOUT = getattr(env_config, 'PDF_GENERATION_TIMEOUT', int(os.getenv("PDF_GENERATION_TIMEOUT", "30")))
    DEFAULT_TIMEOUT = getattr(env_config, 'DEFAULT_TIMEOUT', int(os.getenv("DEFAULT_TIMEOUT", "120")))
    DEFAULT_MAX_RESPONSE_LENGTH = getattr(env_config, 'DEFAULT_MAX_RESPONSE_LENGTH', int(os.getenv("DEFAULT_MAX_RESPONSE_LENGTH", "2000")))
    DEFAULT_CONTEXT_WINDOW = getattr(env_config, 'DEFAULT_CONTEXT_WINDOW', int(os.getenv("DEFAULT_CONTEXT_WINDOW", "4000")))
else:
    # Fallback configuration
    DEFAULT_COLLECTION_NAME = os.getenv("DEFAULT_COLLECTION_NAME", "knowledge_base")
    KB_REQUEST_TIMEOUT = int(os.getenv("KB_REQUEST_TIMEOUT", "10"))  # KB API timeout in seconds
    KB_LONG_REQUEST_TIMEOUT = int(os.getenv("KB_LONG_REQUEST_TIMEOUT", "30"))  # Long operations timeout
    MAX_CHAT_RESPONSES_PER_SESSION = int(os.getenv("MAX_CHAT_RESPONSES_PER_SESSION", "20"))
    MAX_CHAT_RESPONSE_LENGTH = int(os.getenv("MAX_CHAT_RESPONSE_LENGTH", "5000"))
    KB_CHAT_REQUEST_TIMEOUT = int(os.getenv("KB_CHAT_REQUEST_TIMEOUT", "30"))  # KB chat API timeout
    PDF_GENERATION_TIMEOUT = int(os.getenv("PDF_GENERATION_TIMEOUT", "30"))   # PDF generation timeout
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

# Success Message Display Configuration
SUCCESS_MESSAGE_DISPLAY_DURATION = int(os.getenv("SUCCESS_MESSAGE_DISPLAY_DURATION", "5"))  # seconds

# Design Record Demo Data Configuration
DEMO_CLINICAL_STUDIES = [
    {"Study ID": "CS-001", "Title": "Primary Endpoint Study", "Status": "In Progress", "Participants": 150},
    {"Study ID": "CS-002", "Title": "Safety Follow-up Study", "Status": "Planning", "Participants": 75}
]

DEMO_ADVERSE_EVENTS = [
    {"Event ID": "AE-001", "Date": "2024-01-15", "Severity": "malfunction", "Description": "Device calibration error", "Status": "closed"},
    {"Event ID": "AE-002", "Date": "2024-02-03", "Severity": "near_miss", "Description": "Alarm delay noticed", "Status": "investigating"},
    {"Event ID": "AE-003", "Date": "2024-02-20", "Severity": "malfunction", "Description": "Software freeze during operation", "Status": "analyzed"}
]

DEMO_FIELD_ACTIONS = [
    {"Action ID": "FSA-001", "Type": "software_update", "Date": "2024-01-20", "Description": "Critical security patch", "Affected Products": "Model A v1.0-1.2", "Status": "Completed"},
    {"Action ID": "FSA-002", "Type": "field_safety_notice", "Date": "2024-02-10", "Description": "Updated user manual", "Affected Products": "All Models", "Status": "In Progress"}
]

DEMO_COMPLIANCE_STANDARDS = [
    {"Standard": "ISO 14971:2019", "Title": "Medical devices - Application of risk management to medical devices", "Status": "Applicable", "Compliance": "Compliant"},
    {"Standard": "IEC 62304:2006", "Title": "Medical device software - Software life cycle processes", "Status": "Applicable", "Compliance": "In Progress"},
    {"Standard": "ISO 13485:2016", "Title": "Medical devices - Quality management systems", "Status": "Applicable", "Compliance": "Compliant"}
]

# Demo Data for Standards Compliance
DEMO_STANDARDS_COMPLIANCE = [
    {"id": 1, "standard_id": "ISO 13485:2016", "version": "2016", "applicable_clauses": "4.2, 7.3, 8.5", "status": "compliant", "last_review": "2024-01-15", "standard_name": "Medical Devices QMS"},
    {"id": 2, "standard_id": "ISO 14971:2019", "version": "2019", "applicable_clauses": "4.3, 5.2, 7.1", "status": "partially_compliant", "last_review": "2024-02-01", "standard_name": "Medical Device Risk Management"},
    {"id": 3, "standard_id": "IEC 60812:2018", "version": "2018", "applicable_clauses": "All", "status": "compliant", "last_review": "2024-01-30", "standard_name": "FMEA Analysis"}
]

# Demo Data for Biocompatibility Testing
DEMO_BIOCOMPATIBILITY_TESTS = [
    {"Test": "Cytotoxicity", "Standard": "ISO 10993-5", "Status": "Pass", "Date": "2024-01-15"},
    {"Test": "Sensitization", "Standard": "ISO 10993-10", "Status": "Pass", "Date": "2024-01-20"},
    {"Test": "Irritation", "Standard": "ISO 10993-10", "Status": "In Progress", "Date": "TBD"}
]

# Demo Data for EMC/Safety Testing
DEMO_EMC_SAFETY_TESTS = [
    {"Test": "EMC Emissions", "Standard": "IEC 60601-1-2", "Status": "Pass", "Report": "EMC_001.pdf"},
    {"Test": "EMC Immunity", "Standard": "IEC 60601-1-2", "Status": "Pass", "Report": "EMC_002.pdf"},
    {"Test": "Electrical Safety", "Standard": "IEC 60601-1", "Status": "Pass", "Report": "ES_001.pdf"}
]