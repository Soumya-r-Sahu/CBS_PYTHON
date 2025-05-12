# filepath: d:\vs code\github\CBS-python\app\config\config_loader.py
"""
Configuration Loader

IMPORTANT: This module now delegates to the main config.py file.
This class is kept for backward compatibility but now primarily serves
as an adapter between the old config format and the new centralized config.

For new code, import directly from the root config.py file.
"""

import os
import sys
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Add the parent directory to sys.path to ensure we can import from the root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the main config
import config

class ConfigLoader:
    """Configuration loader for the Core Banking System"""
    
    _instance = None
    _config = {}
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """Load configuration from the centralized config.py"""
        try:
            # Convert the config module's attributes to a dictionary
            for item in dir(config):
                if item.isupper() and not item.startswith('__'):
                    value = getattr(config, item)
                    self._config[item.lower()] = value
            
            # Special handling for nested configs
            for key in dir(config):
                if key.endswith('_CONFIG') and not key.startswith('__'):
                    config_dict = getattr(config, key)
                    if isinstance(config_dict, dict):
                        category = key.replace('_CONFIG', '').lower()
                        self._config[category] = config_dict
            
            logging.info("Configuration loaded successfully from centralized config")
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            raise
    
    def _override_from_env(self) -> None:
        """
        Method kept for backward compatibility.
        Environment variables are now handled in the main config.py.
        """
        pass  # No-op since environment variables are handled in config.py
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if k in value:
                    value = value[k]
                else:
                    # Special case for database config which may be accessed differently
                    if k == 'database' and 'database_config' in value:
                        value = value['database_config']
                    else:
                        return default
            return value
        except (KeyError, TypeError):
            return default
    
    def get_database_url(self) -> str:
        """Get the database URL with password masked for logging"""
        # Use the DATABASE_URL from the main config
        db_url = config.DATABASE_URL
        
        if db_url and '://' in db_url:
            parts = db_url.split('://')
            if '@' in parts[1]:
                auth, rest = parts[1].split('@', 1)
                if ':' in auth:
                    user = auth.split(':', 1)[0]
                    masked_url = f"{parts[0]}://{user}:****@{rest}"
                    return masked_url
        return db_url
    
    def get_database_config(self) -> dict:
        """Get the database configuration"""
        return config.DATABASE_CONFIG

# Create a singleton instance
config_loader = ConfigLoader()  # Use a different name to avoid conflicts with imported config
