"""
Payment Module Registry

This module implements the Module Registry Interface for the Payments module.
It registers the Payments module, its API endpoints, feature flags, and configurations
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

logger = logging.getLogger(__name__)

class PaymentsModuleRegistry(BaseModuleRegistry):
    """Payments module registry implementation."""
    
    def __init__(self):
        """Initialize the Payments module registry."""
        super().__init__(
            module_id="payments",
            module_name="Payments Module",
            version="1.0.0",
            description="Core payment processing services including NEFT, RTGS, IMPS, and UPI."
        )
        self.set_dependencies(["core_banking"])
    
    def get_api_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get all API endpoints for the Payments module.
        
        Returns:
            List of API endpoint dictionaries
        """
        return [
            # NEFT Endpoints
            {
                "path": "/api/v1/payments/neft/transfer",
                "method": "POST",
                "description": "Initiate a NEFT transfer",
                "auth_required": True,
                "rate_limit": 300
            },
            {
                "path": "/api/v1/payments/neft/status/{reference_id}",
                "method": "GET",
                "description": "Check NEFT transfer status",
                "auth_required": True,
                "rate_limit": 1000
            },
            {
                "path": "/api/v1/payments/neft/history",
                "method": "GET",
                "description": "Get NEFT transfer history",
                "auth_required": True,
                "rate_limit": 100
            },
            
            # RTGS Endpoints
            {
                "path": "/api/v1/payments/rtgs/transfer",
                "method": "POST",
                "description": "Initiate a RTGS transfer",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/payments/rtgs/status/{reference_id}",
                "method": "GET",
                "description": "Check RTGS transfer status",
                "auth_required": True,
                "rate_limit": 1000
            },
            {
                "path": "/api/v1/payments/rtgs/history",
                "method": "GET",
                "description": "Get RTGS transfer history",
                "auth_required": True,
                "rate_limit": 100
            },
            
            # IMPS Endpoints
            {
                "path": "/api/v1/payments/imps/transfer",
                "method": "POST",
                "description": "Initiate an IMPS transfer",
                "auth_required": True,
                "rate_limit": 500
            },
            {
                "path": "/api/v1/payments/imps/status/{reference_id}",
                "method": "GET",
                "description": "Check IMPS transfer status",
                "auth_required": True,
                "rate_limit": 1000
            },
            {
                "path": "/api/v1/payments/imps/history",
                "method": "GET",
                "description": "Get IMPS transfer history",
                "auth_required": True,
                "rate_limit": 100
            },
            
            # UPI Endpoints
            {
                "path": "/api/v1/payments/upi/transfer",
                "method": "POST",
                "description": "Initiate a UPI transfer",
                "auth_required": True,
                "rate_limit": 1000
            },
            {
                "path": "/api/v1/payments/upi/status/{reference_id}",
                "method": "GET",
                "description": "Check UPI transfer status",
                "auth_required": True,
                "rate_limit": 2000
            },
            {
                "path": "/api/v1/payments/upi/history",
                "method": "GET",
                "description": "Get UPI transfer history",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/payments/upi/qr/generate",
                "method": "POST",
                "description": "Generate UPI QR code",
                "auth_required": True,
                "rate_limit": 500
            }
        ]
    
    def get_feature_flags(self) -> List[Dict[str, Any]]:
        """
        Get all feature flags for the Payments module.
        
        Returns:
            List of feature flag dictionaries
        """
        return [
            {
                "name": "enable_neft",
                "description": "Enable NEFT transfers",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/payments/neft/transfer",
                    "/api/v1/payments/neft/status/{reference_id}",
                    "/api/v1/payments/neft/history"
                ]
            },
            {
                "name": "enable_rtgs",
                "description": "Enable RTGS transfers",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/payments/rtgs/transfer",
                    "/api/v1/payments/rtgs/status/{reference_id}",
                    "/api/v1/payments/rtgs/history"
                ]
            },
            {
                "name": "enable_imps",
                "description": "Enable IMPS transfers",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/payments/imps/transfer",
                    "/api/v1/payments/imps/status/{reference_id}",
                    "/api/v1/payments/imps/history"
                ]
            },
            {
                "name": "enable_upi",
                "description": "Enable UPI transfers",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/payments/upi/transfer",
                    "/api/v1/payments/upi/status/{reference_id}",
                    "/api/v1/payments/upi/history",
                    "/api/v1/payments/upi/qr/generate"
                ]
            },
            {
                "name": "neft_outward_window",
                "description": "Enable NEFT outward window",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/payments/neft/transfer"
                ]
            },
            {
                "name": "rtgs_high_value_validation",
                "description": "Enable validation for high-value RTGS transfers",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/payments/rtgs/transfer"
                ]
            }
        ]
    
    def get_configurations(self) -> List[Dict[str, Any]]:
        """
        Get all configurations for the Payments module.
        
        Returns:
            List of configuration dictionaries
        """
        return [
            {
                "key": "neft_min_amount",
                "value": 1.0,
                "type": "module",
                "description": "Minimum amount for NEFT transfers",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "neft_max_amount",
                "value": 1000000.0,
                "type": "module",
                "description": "Maximum amount for NEFT transfers",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "rtgs_min_amount",
                "value": 200000.0,
                "type": "module",
                "description": "Minimum amount for RTGS transfers",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "rtgs_max_amount",
                "value": 50000000.0,
                "type": "module",
                "description": "Maximum amount for RTGS transfers",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "imps_min_amount",
                "value": 1.0,
                "type": "module",
                "description": "Minimum amount for IMPS transfers",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "imps_max_amount",
                "value": 500000.0,
                "type": "module",
                "description": "Maximum amount for IMPS transfers",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "upi_min_amount",
                "value": 1.0,
                "type": "module",
                "description": "Minimum amount for UPI transfers",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "upi_max_amount",
                "value": 100000.0,
                "type": "module",
                "description": "Maximum amount for UPI transfers",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "neft_processing_hours",
                "value": {
                    "start": "08:00",
                    "end": "19:00"
                },
                "type": "module",
                "description": "NEFT processing hours",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "rtgs_processing_hours",
                "value": {
                    "start": "09:00",
                    "end": "16:30"
                },
                "type": "module",
                "description": "RTGS processing hours",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "gateway_timeout",
                "value": 30,
                "type": "performance",
                "description": "Payment gateway timeout in seconds",
                "is_sensitive": False,
                "allowed_values": [15, 30, 45, 60]
            },
            {
                "key": "retry_attempts",
                "value": 3,
                "type": "performance",
                "description": "Number of retry attempts for failed payments",
                "is_sensitive": False,
                "allowed_values": [1, 2, 3, 4, 5]
            }
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check for the Payments module.
        
        Returns:
            Dictionary with health check results
        """
        # In a real implementation, this would check database connections,
        # payment gateway connections, and other dependencies
        
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
        
        # Mock payment gateway status
        gateways = {
            "neft_gateway": "connected",
            "rtgs_gateway": "connected",
            "imps_gateway": "connected",
            "upi_gateway": "connected"
        }
        
        # If this was a real implementation, we'd check actual gateway connections
        # and update the status accordingly
        
        return {
            "status": status,
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_bytes": memory_info.rss,
                "memory_percent": memory_percent,
                "active_transactions": 0  # Mock value
            },
            "details": {
                "gateways": gateways,
                "uptime": "12:30:45"  # Mock value
            },
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }


def register_with_admin():
    """Register the Payments module with the Admin module."""
    try:
        # Create the module registry
        registry = PaymentsModuleRegistry()
        
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
        print("Successfully registered Payments module with Admin module")
    else:
        print("Failed to register Payments module with Admin module")
        sys.exit(1)
