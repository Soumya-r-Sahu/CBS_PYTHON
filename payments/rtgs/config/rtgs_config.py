"""
RTGS Payment Configuration - Core Banking System

This module provides configuration settings for RTGS payments.
"""
import os
import logging
from typing import Dict, Any

# Configure logger
logger = logging.getLogger(__name__)


class RTGSConfig:
    """Configuration manager for RTGS module."""
    _instance = None
    
    def __new__(cls):
        """Ensure only one instance of RTGSConfig exists."""
        if cls._instance is None:
            cls._instance = super(RTGSConfig, cls).__new__(cls)
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
            "minimum_amount": 200000.0,  # ₹2,00,000 (RTGS minimum amount per RBI guidelines)
            "maximum_amount": 100000000.0,  # ₹10 crores
            "daily_limit_per_customer": 50000000.0,  # ₹5 crores
            
            # Timing windows (RTGS operates 24x7 as per RBI guidelines from Dec 2020)
            "service_hours": "24x7",  # 24x7 operations
            "processing_delay_seconds": 60,  # Processing delay in seconds
            
            # Connection settings
            "api_endpoint": os.getenv(
                "RTGS_API_ENDPOINT", 
                "https://api.rbi.org.in/rtgs/v1" if self.environment == "production" else "https://api-uat.rbi.org.in/rtgs/v1"
            ),
            "api_timeout_seconds": 30,
            
            # Authentication
            "api_key": os.getenv("RTGS_API_KEY", ""),
            "api_secret": os.getenv("RTGS_API_SECRET", ""),
            "certificate_path": os.getenv("RTGS_CERTIFICATE_PATH", ""),
            
            # Database settings
            "db_collection": "rtgs_transactions",
            "history_collection": "rtgs_history",
            
            # Notification settings
            "enable_sms_notifications": True,
            "enable_email_notifications": True,
        }
        
        # Override with environment-specific settings
        if self.environment == "development":
            self.config.update({
                "mock_mode": True,
                "processing_delay_seconds": 5,  # Faster processing for development
            })
        elif self.environment == "testing":
            self.config.update({
                "mock_mode": True,
                "db_collection": "rtgs_transactions_test",
                "history_collection": "rtgs_history_test",
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
rtgs_config = RTGSConfig()
