# backend/app/settings.py
"""
Legacy settings module - now imports from config.py
This file is kept for backward compatibility
"""
from .config import config

# Legacy compatibility - expose config as settings
settings = config

