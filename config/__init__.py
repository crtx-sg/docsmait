"""
Docsmait Configuration Package

Centralized configuration management for the Docsmait application.
Provides environment-specific configurations and eliminates hardcoded values.
"""

from .environments import (
    BaseConfig,
    DevelopmentConfig, 
    DockerConfig,
    TestingConfig,
    ProductionConfig,
    get_config,
    config
)

__all__ = [
    'BaseConfig',
    'DevelopmentConfig',
    'DockerConfig', 
    'TestingConfig',
    'ProductionConfig',
    'get_config',
    'config'
]