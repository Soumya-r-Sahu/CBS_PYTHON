"""
UPI Payment Configuration Module.

Provides configuration settings for UPI payment processing.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)


class UpiConfig:
    """Singleton configuration class for UPI payment module"""
    
    _instance = None
    _config = {}
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(UpiConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from file or environment variables"""
        try:
            # First try to load from config file
            config_path = os.environ.get('UPI_CONFIG_PATH', 'config/upi_config.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self._config = json.load(f)
                logger.info(f"Loaded UPI config from {config_path}")
            else:
                # Fall back to environment variables
                logger.info("Config file not found, using environment variables")
                
                # Determine environment
                env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
                is_production = env_str == "production"
                is_test = env_str == "test"
                
                # Set environment-specific settings
                if is_production:
                    data_dir = "upi/transactions"
                    is_mock_mode = False
                    validation_strict = True
                    max_transaction_limit = 100000  # Higher limit in production
                elif is_test:
                    data_dir = "upi/transactions/test"
                    is_mock_mode = True  # Use mock UPI server in test
                    validation_strict = False
                    max_transaction_limit = 10000  # Lower limit in test
                else:  # development
                    data_dir = "upi/transactions/development"
                    is_mock_mode = True  # Use mock UPI server in development
                    validation_strict = False
                    max_transaction_limit = 50000  # Medium limit in development
                
                self._config = {
                    'ENVIRONMENT': env_str,
                    'DATA_DIR': os.environ.get('UPI_DATA_DIR', data_dir),
                    'HOST': os.environ.get('UPI_HOST', 'localhost'),
                    'PORT': int(os.environ.get('UPI_PORT', '5000')),
                    'DEBUG': os.environ.get('UPI_DEBUG', 'false').lower() == 'true',
                    'USE_MOCK': is_mock_mode,
                    'VALIDATION_STRICT': validation_strict,
                    'MAX_TRANSACTION_LIMIT': max_transaction_limit,
                    'TIMEOUT_SECONDS': int(os.environ.get('UPI_TIMEOUT', '30')),
                    'NOTIFICATION_ENABLED': os.environ.get('UPI_NOTIFICATION_ENABLED', 'true').lower() == 'true',
                    'PSP_ID': os.environ.get('UPI_PSP_ID', 'SBIN'),  # SBI UPI PSP ID
                    'MERCHANT_CODE': os.environ.get('UPI_MERCHANT_CODE', 'SBIBANK'),
                    'API_VERSION': os.environ.get('UPI_API_VERSION', '2.0'),
                    'GATEWAY_URL': os.environ.get('UPI_GATEWAY_URL', 'https://api.upi.npci.org.in')
                }
        except Exception as e:
            logger.error(f"Error loading UPI config: {str(e)}")
            # Use default values
            self._config = {
                'ENVIRONMENT': 'development',
                'DATA_DIR': 'upi/transactions/development',
                'HOST': 'localhost',
                'PORT': 5000,
                'DEBUG': True,
                'USE_MOCK': True,
                'VALIDATION_STRICT': False,
                'MAX_TRANSACTION_LIMIT': 50000,
                'TIMEOUT_SECONDS': 30,
                'NOTIFICATION_ENABLED': True,
                'PSP_ID': 'SBIN',
                'MERCHANT_CODE': 'SBIBANK',
                'API_VERSION': '2.0',
                'GATEWAY_URL': 'https://api.upi.npci.org.in'
            }
    
    def get(self, key: str, default=None) -> Any:
        """Get configuration value by key"""
        return self._config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return dict(self._config)


# Create singleton instance
upi_config = UpiConfig()
