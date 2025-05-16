"""
Core Banking System Configuration Module (LEGACY VERSION)

This module provides backward compatibility with the old configuration system.
It forwards all configuration settings from the new utils/config module.

This is a legacy module kept for backward compatibility only.
New code should use utils/config instead.
"""

import sys
import os
import warnings
from pathlib import Path

# Try to import from the new location
try:
    from utils.config import *
    
    # Issue a deprecation warning
    warnings.warn(
        "The app.config module is deprecated. "
        "Please use utils.config instead.",
        DeprecationWarning,
        stacklevel=2
    )
except ImportError:
    # If the new config isn't available, provide some basic fallback
    import json
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.warning("Could not import utils.config. Using fallback configuration.")
    
    # Default configuration values
    DATABASE_CONFIG = {
        "host": "localhost",
        "port": 5432,
        "database": "cbs_db",
        "user": "cbs_user",
        "password": "password"
    }
    
    # Environment settings
    ENVIRONMENT = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    DEBUG = os.environ.get("CBS_DEBUG", "False").lower() in ("true", "1", "yes")
    
    # Attempt to load configuration from a JSON file
    try:
        config_file = Path(__file__).parent.parent.parent / "utils" / "config" / "settings.json"
        if config_file.exists():
            with open(config_file, "r") as f:
                config_data = json.load(f)
                
                # Update the default values with the loaded configuration
                if "database" in config_data:
                    DATABASE_CONFIG.update(config_data["database"])
                
                # Load other configuration sections
                for key, value in config_data.items():
                    if key != "database":
                        globals()[key.upper()] = value
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")

# Make sure we have some essential configuration variables
if "APPLICATION_NAME" not in globals():
    APPLICATION_NAME = "Core Banking System"

if "VERSION" not in globals():
    VERSION = "1.0.0"
