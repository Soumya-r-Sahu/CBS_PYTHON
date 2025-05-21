"""
Centralized Configuration Manager for Core Banking System

This module provides a unified approach to configuration management
throughout the Core Banking System. It consolidates previously duplicated logic and
ensures consistent configuration handling across all modules.

Features:
---------
- Singleton pattern ensures consistent configuration across modules
- Environment-aware configuration loading
- Graceful fallbacks for missing configuration
- Support for nested configuration keys
- Default values for missing configuration

Usage:
------
from utils.config_manager import config_manager

# Get a configuration value with a default
db_url = config_manager.get("database.url", "sqlite:///database/cbs.db")

# Get a nested configuration
jwt_config = config_manager.get("security.jwt")

# Get an environment-specific configuration
timeout = config_manager.get_for_env("api.timeout", 30)
"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Import singleton decorator
from utils.design_patterns import singleton

# Initialize logger
logger = logging.getLogger(__name__)

@singleton
class ConfigManager:
    """
    Centralized Configuration Manager implementing singleton pattern.
    Ensures consistent configuration throughout the application.
    """
    
    def __init__(self):
        """Initialize the configuration manager"""
        self.config = {}
        self.environment = self._get_environment()
        self._load_default_config()
        self._load_environment_config()
        logger.info(f"Configuration manager initialized for environment: {self.environment}")
    
    def _get_environment(self) -> str:
        """Get the current environment name"""
        return os.environ.get("CBS_ENVIRONMENT", "development").lower()
    
    def _load_default_config(self) -> None:
        """Load default configuration"""
        # Default configuration as a fallback
        self.config = {
            "database": {
                "url": os.environ.get('CBS_DATABASE_URL', "sqlite:///database/cbs.db"),
                "pool_size": 10,
                "max_overflow": 20,
                "timeout": 30
            },
            "security": {
                # Use secure random key generation if no env var
                "secret_key": os.environ.get('CBS_SECRET_KEY', None),
                "allowed_hosts": os.environ.get('CBS_ALLOWED_HOSTS', "localhost,127.0.0.1").split(','),
                "jwt": {
                    "algorithm": "HS256",
                    "access_token_expire_minutes": int(os.environ.get('CBS_JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 30)),
                    "refresh_token_expire_days": int(os.environ.get('CBS_JWT_REFRESH_TOKEN_EXPIRE_DAYS', 7)),
                }
            },
            "api": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False,
                "timeout": 30
            },
            "logging": {
                "level": "INFO",
                "file": "logs/cbs.log",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        # If secret key not provided, generate one
        if self.config["security"]["secret_key"] is None:
            import secrets
            self.config["security"]["secret_key"] = secrets.token_hex(32)
            logger.warning("Using auto-generated secret key. Set CBS_SECRET_KEY environment variable in production.")
    
    def _load_environment_config(self) -> None:
        """Load environment-specific configuration"""
        config_paths = [
            Path(f"config/{self.environment}.yaml"),
            Path(f"config/{self.environment}.json"),
            Path(f"config.{self.environment}.yaml"),
            Path(f"config.{self.environment}.json")
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    if config_path.suffix == '.yaml':
                        with open(config_path, 'r') as file:
                            env_config = yaml.safe_load(file)
                    else:  # .json
                        with open(config_path, 'r') as file:
                            env_config = json.load(file)
                    
                    # Update the config with environment-specific values
                    self._update_nested_dict(self.config, env_config)
                    logger.info(f"Loaded environment config from {config_path}")
                    break
                except Exception as e:
                    logger.error(f"Error loading config from {config_path}: {e}")
    
    def _update_nested_dict(self, d: Dict, u: Dict) -> Dict:
        """Update a nested dictionary with another nested dictionary"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: The configuration key (can be nested using dot notation)
            default: Default value if key not found
            
        Returns:
            The configuration value or default
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return default
        
        return config
    
    def get_for_env(self, key: str, default: Any = None) -> Any:
        """
        Get an environment-specific configuration value.
        
        Args:
            key: The configuration key (can be nested using dot notation)
            default: Default value if key not found
            
        Returns:
            The environment-specific configuration value or default
        """
        env_key = f"{self.environment}.{key}"
        # Try environment-specific key first, then fall back to general key
        return self.get(env_key, self.get(key, default))
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key (can be nested using dot notation)
            value: The value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.debug(f"Configuration set: {key} = {value}")

# Create a singleton instance for easy import
config_manager = ConfigManager()

# Convenience functions for backward compatibility
def get_config(key: str = None, default: Any = None) -> Any:
    """Get a configuration value or the entire config if key is None"""
    if key is None:
        return config_manager.config
    return config_manager.get(key, default)

def get_environment() -> str:
    """Get the current environment name"""
    return config_manager.environment

def is_production() -> bool:
    """Check if the current environment is production"""
    return config_manager.environment == 'production'

def is_development() -> bool:
    """Check if the current environment is development"""
    return config_manager.environment == 'development'

def is_testing() -> bool:
    """Check if the current environment is testing"""
    return config_manager.environment == 'testing'
