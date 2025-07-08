"""
Digital Channels Module Registry

This module implements the Module Registry Interface for the Digital Channels module.
It registers the Digital Channels module, its API endpoints, feature flags, and configurations
with the Admin module.
"""
from typing import Dict, List, Any, Optional
import os
import sys
import logging
import json
import psutil
from datetime import datetime

# Add the parent directory to sys.path to import the integration interfaces
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from integration_interfaces.api.base_module_registry import BaseModuleRegistry
from integration_interfaces.api.admin_client import AdminIntegrationClient

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


logger = logging.getLogger(__name__)

class DigitalChannelsModuleRegistry(BaseModuleRegistry):
    """Digital Channels module registry implementation."""
    
    def __init__(self):
        """Initialize the Digital Channels module registry."""
        super().__init__(
            module_id="digital_channels",
            module_name="Digital Channels Module",
            version="1.0.0",
            description="Digital banking channels including Internet Banking, Mobile Banking, and ATM services."
        )
        self.set_dependencies(["core_banking"])
    
    def get_api_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get all API endpoints for the Digital Channels module.
        
        Returns:
            List of API endpoint dictionaries
        """
        return [
            # Internet Banking Endpoints
            {
                "path": "/api/v1/digital/internet/login",
                "method": "POST",
                "description": "Login to Internet Banking",
                "auth_required": False,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/digital/internet/dashboard",
                "method": "GET",
                "description": "Get Internet Banking dashboard",
                "auth_required": True,
                "rate_limit": 300
            },
            {
                "path": "/api/v1/digital/internet/accounts",
                "method": "GET",
                "description": "Get accounts for Internet Banking",
                "auth_required": True,
                "rate_limit": 300
            },
            {
                "path": "/api/v1/digital/internet/transactions",
                "method": "GET",
                "description": "Get transactions for Internet Banking",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/digital/internet/beneficiaries",
                "method": "GET",
                "description": "Get beneficiaries for Internet Banking",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/digital/internet/beneficiaries",
                "method": "POST",
                "description": "Add beneficiary for Internet Banking",
                "auth_required": True,
                "rate_limit": 100
            },
            
            # Mobile Banking Endpoints
            {
                "path": "/api/v1/digital/mobile/login",
                "method": "POST",
                "description": "Login to Mobile Banking",
                "auth_required": False,
                "rate_limit": 500
            },
            {
                "path": "/api/v1/digital/mobile/dashboard",
                "method": "GET",
                "description": "Get Mobile Banking dashboard",
                "auth_required": True,
                "rate_limit": 500
            },
            {
                "path": "/api/v1/digital/mobile/accounts",
                "method": "GET",
                "description": "Get accounts for Mobile Banking",
                "auth_required": True,
                "rate_limit": 500
            },
            {
                "path": "/api/v1/digital/mobile/transactions",
                "method": "GET",
                "description": "Get transactions for Mobile Banking",
                "auth_required": True,
                "rate_limit": 300
            },
            {
                "path": "/api/v1/digital/mobile/beneficiaries",
                "method": "GET",
                "description": "Get beneficiaries for Mobile Banking",
                "auth_required": True,
                "rate_limit": 300
            },
            {
                "path": "/api/v1/digital/mobile/beneficiaries",
                "method": "POST",
                "description": "Add beneficiary for Mobile Banking",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/digital/mobile/quick-pay",
                "method": "POST",
                "description": "Quick payment for Mobile Banking",
                "auth_required": True,
                "rate_limit": 300
            },
            
            # ATM Endpoints
            {
                "path": "/api/v1/digital/atm/validate-card",
                "method": "POST",
                "description": "Validate ATM card",
                "auth_required": True,
                "rate_limit": 1000
            },
            {
                "path": "/api/v1/digital/atm/balance",
                "method": "GET",
                "description": "Get balance for ATM",
                "auth_required": True,
                "rate_limit": 1000
            },
            {
                "path": "/api/v1/digital/atm/withdraw",
                "method": "POST",
                "description": "Withdraw from ATM",
                "auth_required": True,
                "rate_limit": 1000
            },
            {
                "path": "/api/v1/digital/atm/mini-statement",
                "method": "GET",
                "description": "Get mini statement from ATM",
                "auth_required": True,
                "rate_limit": 500
            },
            {
                "path": "/api/v1/digital/atm/pin-change",
                "method": "POST",
                "description": "Change PIN for ATM",
                "auth_required": True,
                "rate_limit": 200
            }
        ]
    
    def get_feature_flags(self) -> List[Dict[str, Any]]:
        """
        Get all feature flags for the Digital Channels module.
        
        Returns:
            List of feature flag dictionaries
        """
        return [
            {
                "name": "enable_internet_banking",
                "description": "Enable Internet Banking services",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/digital/internet/login",
                    "/api/v1/digital/internet/dashboard",
                    "/api/v1/digital/internet/accounts",
                    "/api/v1/digital/internet/transactions",
                    "/api/v1/digital/internet/beneficiaries"
                ]
            },
            {
                "name": "enable_mobile_banking",
                "description": "Enable Mobile Banking services",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/digital/mobile/login",
                    "/api/v1/digital/mobile/dashboard",
                    "/api/v1/digital/mobile/accounts",
                    "/api/v1/digital/mobile/transactions",
                    "/api/v1/digital/mobile/beneficiaries",
                    "/api/v1/digital/mobile/quick-pay"
                ]
            },
            {
                "name": "enable_atm_services",
                "description": "Enable ATM services",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/digital/atm/validate-card",
                    "/api/v1/digital/atm/balance",
                    "/api/v1/digital/atm/withdraw",
                    "/api/v1/digital/atm/mini-statement",
                    "/api/v1/digital/atm/pin-change"
                ]
            },
            {
                "name": "biometric_authentication",
                "description": "Enable biometric authentication for mobile banking",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/digital/mobile/login"
                ]
            },
            {
                "name": "quick_balance_check",
                "description": "Enable quick balance check without full login",
                "enabled": False,
                "affects_endpoints": [
                    "/api/v1/digital/mobile/accounts"
                ]
            },
            {
                "name": "cardless_withdrawal",
                "description": "Enable cardless withdrawal from ATMs",
                "enabled": False,
                "affects_endpoints": [
                    "/api/v1/digital/atm/withdraw"
                ]
            }
        ]
    
    def get_configurations(self) -> List[Dict[str, Any]]:
        """
        Get all configurations for the Digital Channels module.
        
        Returns:
            List of configuration dictionaries
        """
        return [
            {
                "key": "session_timeout",
                "value": 15,
                "type": "security",
                "description": "Session timeout in minutes for digital channels",
                "is_sensitive": False,
                "allowed_values": [5, 10, 15, 30, 60]
            },
            {
                "key": "max_failed_attempts",
                "value": 3,
                "type": "security",
                "description": "Maximum number of failed login attempts before locking",
                "is_sensitive": False,
                "allowed_values": [3, 5, 10]
            },
            {
                "key": "mobile_daily_limit",
                "value": 50000.0,
                "type": "module",
                "description": "Daily transaction limit for mobile banking",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "internet_daily_limit",
                "value": 100000.0,
                "type": "module",
                "description": "Daily transaction limit for internet banking",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "atm_daily_limit",
                "value": 25000.0,
                "type": "module",
                "description": "Daily withdrawal limit for ATM",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "require_otp",
                "value": True,
                "type": "security",
                "description": "Require OTP for high-value transactions",
                "is_sensitive": False,
                "allowed_values": [True, False]
            },
            {
                "key": "high_value_threshold",
                "value": 10000.0,
                "type": "module",
                "description": "Threshold for high-value transactions",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "maintenance_window",
                "value": {
                    "enabled": False,
                    "start": "23:00",
                    "end": "01:00",
                    "message": "System is under maintenance. Please try again later."
                },
                "type": "module",
                "description": "Maintenance window for digital channels",
                "is_sensitive": False,
                "allowed_values": None
            }
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check for the Digital Channels module.
        
        Returns:
            Dictionary with health check results
        """
        alerts = []
        status = "healthy"
        
        # Get CPU and memory usage for this process
        process = psutil.Process(os.getpid())
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # Check if any resources are over threshold
        if cpu_percent > 80:
            alerts.append("High CPU usage detected")
            status = "warning"
        
        if memory_percent > 80:
            alerts.append("High memory usage detected")
            status = "warning"
        
        # Mock channel status
        channels = {
            "internet_banking": "available",
            "mobile_banking": "available",
            "atm_switch": "available"
        }
        
        # Mock metrics
        active_sessions = {
            "internet_banking": 150,
            "mobile_banking": 325,
            "atm": 45
        }
        
        return {
            "status": status,
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_bytes": memory_info.rss,
                "memory_percent": memory_percent,
                "active_sessions": active_sessions
            },
            "details": {
                "channels": channels,
                "uptime": "18:45:10"  # Mock value
            },
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }


def register_with_admin():
    """Register the Digital Channels module with the Admin module."""
    try:
        # Create the module registry
        registry = DigitalChannelsModuleRegistry()
        
        # Create the admin client
        client = AdminIntegrationClient(
            module_id=registry.module_id,
            api_key="dummy-key"  # This should be securely stored and retrieved
        )
        
        # Register the module
        client.register_module(registry.get_module_info())
        
        # Register API endpoints
        client.register_api_endpoints(registry.get_api_endpoints())
        
        # Register feature flags
        client.register_feature_flags(registry.get_feature_flags())
        
        # Register configurations
        client.register_configurations(registry.get_configurations())
        
        # Send initial health metrics
        client.send_health_metrics(registry.health_check())
        
        logger.info(f"Successfully registered {registry.module_name} with Admin module")
        return True
    
    except Exception as e:
        logger.error(f"Failed to register with Admin module: {str(e)}")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Register with Admin module
    if register_with_admin():
        print("Successfully registered Digital Channels module with Admin module")
    else:
        print("Failed to register Digital Channels module with Admin module")
        sys.exit(1)
