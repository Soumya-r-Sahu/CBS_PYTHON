"""
API Logging Configuration - Core Banking System

This module defines configuration settings for API logging.
"""
import os
from typing import Dict, Any


class ApiLogConfig:
    """Configuration for API logging"""
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance exists"""
        if cls._instance is None:
            cls._instance = super(ApiLogConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from environment or defaults"""
        # Default configuration
        self._config = {
            "log_dir": os.environ.get("API_LOG_DIR", "logs/api"),
            "max_file_size_mb": int(os.environ.get("API_LOG_MAX_FILE_SIZE_MB", "10")),
            "rotation_count": int(os.environ.get("API_LOG_ROTATION_COUNT", "5")),
            "enable_db_logging": os.environ.get("API_LOG_ENABLE_DB", "False").lower() == "true",
            "db_connection_string": os.environ.get("API_LOG_DB_CONNECTION", ""),
            "sensitive_fields": os.environ.get("API_LOG_SENSITIVE_FIELDS", 
                                             "password,token,key,secret,auth,credential").split(","),
            "log_level": os.environ.get("API_LOG_LEVEL", "INFO"),
            "enable_request_body_logging": os.environ.get("API_LOG_REQUEST_BODY", "True").lower() == "true",
            "enable_response_body_logging": os.environ.get("API_LOG_RESPONSE_BODY", "True").lower() == "true",
            "max_body_size_kb": int(os.environ.get("API_LOG_MAX_BODY_SIZE_KB", "1024")),
            "store_days": int(os.environ.get("API_LOG_STORE_DAYS", "90")),
        }
        
        # Ensure log directory exists
        os.makedirs(self._config["log_dir"], exist_ok=True)
    
    def get(self, key: str, default=None) -> Any:
        """Get configuration value by key"""
        return self._config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self._config.copy()


# Create a config instance for import

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
api_log_config = ApiLogConfig()
