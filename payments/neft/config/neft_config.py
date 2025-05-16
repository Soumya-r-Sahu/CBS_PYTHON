"""
NEFT Configuration - Core Banking System

This module provides configuration settings for the NEFT payment system.
"""
import os
from typing import Dict, Any
import logging

# Configure logger
logger = logging.getLogger(__name__)


class NEFTConfig:
    """Configuration singleton for NEFT payment system."""
    _instance = None
    
    def __new__(cls):
        """Ensure only one instance of NEFTConfig exists."""
        if cls._instance is None:
            cls._instance = super(NEFTConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from environment or defaults."""
        # Default configuration
        self._config = {
            # Batch configuration
            "batch_enabled": True,
            "batch_time_intervals": [
                "00:30", "01:30", "02:30", "03:30", "04:30", "05:30",
                "06:30", "07:30", "08:30", "09:30", "10:30", "11:30",
                "12:30", "13:30", "14:30", "15:30", "16:30", "17:30", 
                "18:30", "19:30", "20:30", "21:30", "22:30", "23:30"
            ],
            "max_transactions_per_batch": 10000,
            "hold_time_minutes": 10,  # Hold time before processing batch
            
            # Transaction limits
            "min_transaction_amount": 1.0,
            "max_transaction_amount": 2500000.0,  # 25 lakhs as per RBI guideline
            "max_daily_amount": 10000000.0,  # 1 crore per day (aggregate)
            
            # Bank codes and settings
            "bank_ifsc_code": "ABCD0123456",  # Bank's IFSC code
            "neft_enabled": True,
            
            # Timeout and retry settings
            "connection_timeout_seconds": 30,
            "request_timeout_seconds": 60,
            "max_retries": 3,
            "retry_interval_seconds": 5,
            
            # Service URLs
            "rbi_neft_service_url": "https://api.rbi.org.in/neft",
            "mock_mode": os.environ.get("ENVIRONMENT", "development") != "production",
            
            # Compliance and audit
            "retain_transaction_days": 180,  # Store NEFT transaction records for 180 days
            "enable_detailed_logging": True
        }
        
        # Override defaults with environment variables
        for key in self._config.keys():
            env_key = f"NEFT_{key.upper()}"
            if env_key in os.environ:
                env_value = os.environ[env_key]
                # Type conversion
                if isinstance(self._config[key], bool):
                    self._config[key] = env_value.lower() == 'true'
                elif isinstance(self._config[key], int):
                    self._config[key] = int(env_value)
                elif isinstance(self._config[key], float):
                    self._config[key] = float(env_value)
                elif isinstance(self._config[key], list):
                    self._config[key] = env_value.split(',')
                else:
                    self._config[key] = env_value
        
        logger.info(f"NEFT configuration loaded, mock_mode={self._config['mock_mode']}")
    
    def get(self, key: str, default=None) -> Any:
        """Get configuration value by key."""
        return self._config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()


# Create a singleton instance for import
neft_config = NEFTConfig()
