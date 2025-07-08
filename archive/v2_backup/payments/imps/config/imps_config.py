"""
IMPS Payment Configuration - Core Banking System

This module provides configuration settings for IMPS payments.
"""
import os
import logging
from typing import Dict, Any

# Configure logger
logger = logging.getLogger(__name__)


class IMPSConfig:
    """Configuration manager for IMPS module."""
    _instance = None
    
    def __new__(cls):
        """Ensure only one instance of IMPSConfig exists."""
        if cls._instance is None:
            cls._instance = super(IMPSConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize configuration settings."""
        # Environment (development, testing, production)
        self.environment = os.getenv("CBS_ENVIRONMENT", "development")
        
        # Core configuration settings
        self.config = {
            # Mock mode (for development/testing)
            "mock_mode": self.environment != "production",
            
            # Transaction limits
            "minimum_amount": 1.0,  # ₹1 (no real minimum)
            "maximum_amount": 500000.0,  # ₹5,00,000 per transaction limit
            "daily_limit_per_customer": 1000000.0,  # ₹10,00,000
            
            # Timing windows (IMPS operates 24x7)
            "service_hours": "24x7",
            
            # Connection settings
            "api_endpoint": os.getenv(
                "IMPS_API_ENDPOINT", 
                "https://api.npci.org.in/imps/v1" if self.environment == "production" else "https://api-uat.npci.org.in/imps/v1"
            ),
            "api_timeout_seconds": 30,
            
            # Authentication
            "api_key": os.getenv("IMPS_API_KEY", ""),
            "api_secret": os.getenv("IMPS_API_SECRET", ""),
            "merchant_id": os.getenv("IMPS_MERCHANT_ID", ""),
            "certificate_path": os.getenv("IMPS_CERTIFICATE_PATH", ""),
            
            # Bank settings
            "bank_ifsc_prefix": os.getenv("BANK_IFSC_PREFIX", "ABCD0"),  # First 5 characters of IFSC
            "bank_mmid": os.getenv("BANK_MMID", "9123456"),  # Bank MMID
            
            # Database settings
            "db_collection": "imps_transactions",
            "history_collection": "imps_history",
            
            # Notification settings
            "enable_sms_notifications": True,
            "enable_email_notifications": True,
            
            # Retry configuration
            "max_retry_attempts": 3,
            "retry_interval_seconds": 5
        }
        
        # Override with environment-specific settings
        if self.environment == "development":
            self.config.update({
                "mock_mode": True,
                "api_timeout_seconds": 10
            })
        elif self.environment == "testing":
            self.config.update({
                "mock_mode": True,
                "db_collection": "imps_transactions_test",
                "history_collection": "imps_history_test",
            })
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)


# Create singleton instance
imps_config = IMPSConfig()
