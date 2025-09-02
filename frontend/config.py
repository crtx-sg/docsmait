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