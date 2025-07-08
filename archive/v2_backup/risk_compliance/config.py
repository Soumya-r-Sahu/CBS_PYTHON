"""
Configuration utilities for risk compliance modules

This module provides configuration management for risk compliance components,
with graceful fallbacks to ensure the system works even if the main configuration
is not available.
"""

import os
import logging
import json
from typing import Dict, Any

# Initialize logger
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "audit_trail": {
        "storage_type": "file",
        "log_directory": "logs/audit",
        "mongodb_uri": "mongodb://localhost:27017/",
    },
    "fraud_detection": {
        "enable_rules": True,
        "enable_ml": False,
        "production_thresholds": {
            "transaction_amount": 10000,
            "velocity_threshold": 5,
            "velocity_window_minutes": 60,
            "location_change_km": 500,
            "location_change_hours": 24
        },
        "test_thresholds": {
            "transaction_amount": 5000,
            "velocity_threshold": 3
        },
        "development_thresholds": {
            "transaction_amount": 1000,
            "velocity_threshold": 2
        }
    },
    "regulatory_reporting": {
        "report_directory": "reports/regulatory"
    },
    "risk_scoring": {
        "customer_risk_weights": {},
        "account_risk_weights": {},
        "transaction_risk_weights": {},
        "loan_risk_weights": {}
    }
}

# Environment
ENVIRONMENT = os.environ.get("CBS_ENVIRONMENT", "DEVELOPMENT").upper()
if ENVIRONMENT not in ["DEVELOPMENT", "TEST", "PRODUCTION"]:
    logger.warning(f"Unknown environment: {ENVIRONMENT}. Falling back to DEVELOPMENT")
    ENVIRONMENT = "DEVELOPMENT"

# Configuration cache
_config_cache = {}


def get_environment() -> str:
    """Get the current environment"""
    return ENVIRONMENT


def get_config(module_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific module
    
    Args:
        module_name (str): Name of the module (e.g., "audit_trail")
        
    Returns:
        Dict: Configuration dictionary
    """
    # Return from cache if available
    if module_name in _config_cache:
        return _config_cache[module_name]
    
    # Try to get from main config first
    try:
        # Try to import the main config without modifying sys.path
        from config import get_config as main_get_config
        
        # Get config from main system
        config = main_get_config(module_name)
        logger.debug(f"Using main system configuration for {module_name}")
        
    except (ImportError, AttributeError):
        # Fall back to config file in risk-compliance directory
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "risk_compliance_config.json"
        )
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    all_config = json.load(f)
                config = all_config.get(module_name, {})
                logger.debug(f"Using risk compliance config file for {module_name}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error loading config file: {str(e)}")
                config = {}
        else:
            config = {}
    
    # Fall back to defaults
    if not config and module_name in DEFAULT_CONFIG:
        logger.warning(f"Using default configuration for {module_name}")
        config = DEFAULT_CONFIG[module_name]
    
    # Cache the config
    _config_cache[module_name] = config
    
    return config


def reset_config_cache():
    """Reset the configuration cache"""
    global _config_cache
    _config_cache = {}
