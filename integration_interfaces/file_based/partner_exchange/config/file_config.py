"""
Partner File Exchange Configuration - Core Banking System

This module defines configuration settings for partner file exchanges.
"""
import os
from pathlib import Path
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    "base_directory": "integration-interfaces/file-based/partner-exchange/data",
    "incoming_directory": "incoming",
    "outgoing_directory": "outgoing",
    "archive_directory": "archive",
    "error_directory": "error",
    "file_retention_days": 90,
    "supported_formats": ["csv", "json", "xml"],
    "default_encoding": "utf-8",
    "max_file_size_mb": 50,
    "auto_archive": True,
    "log_level": "INFO"
}


class PartnerFileConfig:
    """Configuration for partner file exchange processing"""
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance exists"""
        if cls._instance is None:
            cls._instance = super(PartnerFileConfig, cls).__new__(cls)
            cls._instance._config = DEFAULT_CONFIG.copy()
            cls._instance._load_environment_config()
            cls._instance._ensure_directories()
        return cls._instance
    
    def _load_environment_config(self):
        """Load configuration from environment variables"""
        env_prefix = "PARTNER_FILE_"
        for key in self._config.keys():
            env_var = f"{env_prefix}{key.upper()}"
            if env_var in os.environ:
                # Handle type conversion as needed
                if isinstance(self._config[key], bool):
                    self._config[key] = os.environ[env_var].lower() == 'true'
                elif isinstance(self._config[key], int):
                    self._config[key] = int(os.environ[env_var])
                elif isinstance(self._config[key], list):
                    self._config[key] = os.environ[env_var].split(',')
                else:
                    self._config[key] = os.environ[env_var]
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        base_dir = Path(self._config["base_directory"])
        subdirs = [
            self._config["incoming_directory"],
            self._config["outgoing_directory"],
            self._config["archive_directory"],
            self._config["error_directory"]
        ]
        
        for subdir in subdirs:
            dir_path = base_dir / subdir
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default=None) -> Any:
        """Get configuration value by key"""
        return self._config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self._config.copy()
    
    def get_path(self, dir_type: str) -> str:
        """Get full path for a directory type (incoming, outgoing, etc.)"""
        base = self._config["base_directory"]
        if dir_type not in ["incoming", "outgoing", "archive", "error"]:
            raise ValueError(f"Invalid directory type: {dir_type}")
        return os.path.join(base, self._config[f"{dir_type}_directory"])


# Create a config instance for import

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
partner_file_config = PartnerFileConfig()
