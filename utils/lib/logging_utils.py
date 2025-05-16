"""
Logging Utilities for the Core Banking System

This module provides standardized logging functionalities
for the Core Banking System, including properly configured
loggers for different purposes.
"""

import os
import logging
try:
    import logging.handlers
except ImportError:
    # Create basic fallback if logging.handlers is not available
    # This is unlikely, but we'll handle it just in case
    class DummyHandler(logging.StreamHandler):
        def __init__(self, *args, **kwargs):
            super().__init__()
            
    # Add the handler to the logging module
    if not hasattr(logging, 'handlers'):
        logging.handlers = type('handlers', (), {})
    
    logging.handlers.RotatingFileHandler = DummyHandler
    logging.handlers.TimedRotatingFileHandler = DummyHandler
from pathlib import Path
from typing import Dict, Any, Optional

# Try to import from compatibility layer
# Note: Using compatibility layer after CBS structure implementation was rolled back
try:
    from app.config.compatibility import (
        is_production,
        is_development,
        is_testing,
        is_debug_enabled,
        get_log_level
    )
except ImportError:
    # Fallback if new structure not available
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    
    def is_production() -> bool:
        return env_str == "production"
        
    def is_development() -> bool:
        return env_str == "development"
        
    def is_testing() -> bool:
        return env_str == "test" or env_str == "testing"
        
    def is_debug_enabled() -> bool:
        return os.environ.get("CBS_DEBUG", "true").lower() in ("true", "1", "yes")
        
    def get_log_level() -> str:
        if is_debug_enabled():
            return "DEBUG"
        elif is_production():
            return "WARNING" 
        else:
            return "INFO"


# Set up logging directory
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
INFO_LOG_FILE = LOGS_DIR / "cbs.log"
ERROR_LOG_FILE = LOGS_DIR / "errors.log"
DEBUG_LOG_FILE = LOGS_DIR / "debug.log"
SECURITY_LOG_FILE = LOGS_DIR / "security.log"


def configure_root_logger() -> None:
    """
    Configure the root logger for the application.
    This sets up the main logging configuration used throughout the app.
    """
    # Get logging configuration
    config = _get_log_config()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config["level"])
    
    # Clear existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config["level"])
    console_handler.setFormatter(logging.Formatter(
        config["format"],
        config["datefmt"]
    ))
    
    # Create and configure file handler for all levels
    file_handler = logging.handlers.RotatingFileHandler(
        INFO_LOG_FILE, maxBytes=10485760, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(config["level"])
    file_handler.setFormatter(logging.Formatter(
        config["format"],
        config["datefmt"]
    ))
    
    # Create and configure file handler for errors only
    error_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE, maxBytes=10485760, backupCount=5, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        config["format"],
        config["datefmt"]
    ))
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Log startup message
    root_logger.info(f"Logging initialized in {os.environ.get('CBS_ENVIRONMENT', 'development').upper()} environment")


def _get_log_config() -> Dict[str, Any]:
    """
    Get logging configuration based on the current environment.
    
    Returns:
        dict: Logging configuration parameters
    """
    return {
        "level": getattr(logging, get_log_level()),
        "format": '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        "datefmt": '%Y-%m-%d %H:%M:%S',
    }


def get_info_logger(name: str) -> logging.Logger:
    """
    Get a properly configured logger for general information logging.
    
    Args:
        name: The name of the logger (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    config = _get_log_config()
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Set log level
    logger.setLevel(config["level"])
    
    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config["format"], config["datefmt"]))
    
    file_handler = logging.handlers.RotatingFileHandler(
        INFO_LOG_FILE, maxBytes=10485760, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(config["format"], config["datefmt"]))
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def get_error_logger(name: str) -> logging.Logger:
    """
    Get a properly configured logger for error logging.
    
    Args:
        name: The name of the logger (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(f"{name}.error")
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Set log level
    logger.setLevel(logging.ERROR)
    
    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    ))
    
    file_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE, maxBytes=10485760, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    ))
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def get_security_logger(name: str) -> logging.Logger:
    """
    Get a properly configured logger for security events.
    
    Args:
        name: The name of the logger (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(f"{name}.security")
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Security logs should always be captured regardless of environment
    logger.setLevel(logging.INFO)
    
    # Create handler
    file_handler = logging.handlers.RotatingFileHandler(
        SECURITY_LOG_FILE, maxBytes=10485760, backupCount=10, encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d',
        '%Y-%m-%d %H:%M:%S'
    ))
    
    # Add handler
    logger.addHandler(file_handler)
    
    return logger


def get_debug_logger(name: str) -> logging.Logger:
    """
    Get a properly configured logger for debug information.
    Only logs when debug mode is enabled.
    
    Args:
        name: The name of the logger (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(f"{name}.debug")
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Set debug level
    logger.setLevel(logging.DEBUG)
    
    # Only enable handlers if debug is enabled
    if is_debug_enabled():
        # Create handlers
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        ))
        
        file_handler = logging.handlers.RotatingFileHandler(
            DEBUG_LOG_FILE, maxBytes=10485760, backupCount=3, encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        ))
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger
