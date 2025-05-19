"""
Risk Compliance Module Registry

This module implements the Module Registry Interface for the Risk Compliance module.
It registers the Risk Compliance module, its API endpoints, feature flags, and configurations
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

class RiskComplianceModuleRegistry(BaseModuleRegistry):
    """Risk Compliance module registry implementation."""
    
    def __init__(self):
        """Initialize the Risk Compliance module registry."""
        super().__init__(
            module_id="risk_compliance",
            module_name="Risk & Compliance Module",
            version="1.0.0",
            description="Core risk management and regulatory compliance services."
        )
        self.set_dependencies(["core_banking", "payments"])
    
    def get_api_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get all API endpoints for the Risk Compliance module.
        
        Returns:
            List of API endpoint dictionaries
        """
        return [
            # AML Endpoints
            {
                "path": "/api/v1/risk/aml/screening",
                "method": "POST",
                "description": "Run AML screening on a customer or transaction",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/risk/aml/history/{customer_id}",
                "method": "GET",
                "description": "Get AML screening history for a customer",
                "auth_required": True,
                "rate_limit": 100
            },
            {
                "path": "/api/v1/risk/aml/alerts",
                "method": "GET",
                "description": "Get current AML alerts",
                "auth_required": True,
                "rate_limit": 50
            },
            
            # KYC Endpoints
            {
                "path": "/api/v1/risk/kyc/verify",
                "method": "POST",
                "description": "Verify KYC information",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/risk/kyc/status/{customer_id}",
                "method": "GET",
                "description": "Get KYC status for a customer",
                "auth_required": True,
                "rate_limit": 500
            },
            {
                "path": "/api/v1/risk/kyc/update",
                "method": "PUT",
                "description": "Update KYC information",
                "auth_required": True,
                "rate_limit": 100
            },
            
            # Fraud Detection Endpoints
            {
                "path": "/api/v1/risk/fraud/analyze",
                "method": "POST",
                "description": "Analyze transaction for fraud",
                "auth_required": True,
                "rate_limit": 1000
            },
            {
                "path": "/api/v1/risk/fraud/alerts",
                "method": "GET",
                "description": "Get current fraud alerts",
                "auth_required": True,
                "rate_limit": 50
            },
            {
                "path": "/api/v1/risk/fraud/rules",
                "method": "GET",
                "description": "Get fraud detection rules",
                "auth_required": True,
                "rate_limit": 20
            },
            
            # Regulatory Reporting Endpoints
            {
                "path": "/api/v1/compliance/reports/generate",
                "method": "POST",
                "description": "Generate regulatory report",
                "auth_required": True,
                "rate_limit": 10
            },
            {
                "path": "/api/v1/compliance/reports/list",
                "method": "GET",
                "description": "List available regulatory reports",
                "auth_required": True,
                "rate_limit": 50
            },
            {
                "path": "/api/v1/compliance/reports/{report_id}",
                "method": "GET",
                "description": "Get regulatory report by ID",
                "auth_required": True,
                "rate_limit": 50
            }
        ]
    
    def get_feature_flags(self) -> List[Dict[str, Any]]:
        """
        Get all feature flags for the Risk Compliance module.
        
        Returns:
            List of feature flag dictionaries
        """
        return [
            {
                "name": "enable_real_time_aml",
                "description": "Enable real-time AML screening for transactions",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/risk/aml/screening"
                ]
            },
            {
                "name": "enable_ai_fraud_detection",
                "description": "Enable AI-based fraud detection",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/risk/fraud/analyze"
                ]
            },
            {
                "name": "enhanced_kyc",
                "description": "Enable enhanced KYC verification",
                "enabled": False,
                "affects_endpoints": [
                    "/api/v1/risk/kyc/verify",
                    "/api/v1/risk/kyc/update"
                ]
            },
            {
                "name": "automated_regulatory_reporting",
                "description": "Enable automated regulatory report generation",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/compliance/reports/generate"
                ]
            },
            {
                "name": "sanction_list_screening",
                "description": "Enable sanction list screening",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/risk/aml/screening"
                ]
            }
        ]
    
    def get_configurations(self) -> List[Dict[str, Any]]:
        """
        Get all configurations for the Risk Compliance module.
        
        Returns:
            List of configuration dictionaries
        """
        return [
            {
                "key": "aml_screening_timeout",
                "value": 10,
                "type": "performance",
                "description": "AML screening timeout in seconds",
                "is_sensitive": False,
                "allowed_values": [5, 10, 15, 20, 30]
            },
            {
                "key": "aml_screening_threshold",
                "value": 0.7,
                "type": "module",
                "description": "AML match threshold (0.0 - 1.0)",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "fraud_detection_sensitivity",
                "value": "medium",
                "type": "module",
                "description": "Fraud detection sensitivity level",
                "is_sensitive": False,
                "allowed_values": ["low", "medium", "high"]
            },
            {
                "key": "kyc_verification_level",
                "value": "standard",
                "type": "module",
                "description": "KYC verification level",
                "is_sensitive": False,
                "allowed_values": ["basic", "standard", "enhanced"]
            },
            {
                "key": "regulatory_report_schedule",
                "value": {
                    "daily": ["CTR"],
                    "monthly": ["BSA", "SARS"],
                    "quarterly": ["FRTB"]
                },
                "type": "module",
                "description": "Regulatory report generation schedule",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "aml_api_key",
                "value": "dummy-aml-api-key",
                "type": "security",
                "description": "API key for external AML service",
                "is_sensitive": True,
                "allowed_values": None
            },
            {
                "key": "cache_expiry",
                "value": 3600,
                "type": "performance",
                "description": "Cache expiry time in seconds for verification results",
                "is_sensitive": False,
                "allowed_values": [600, 1800, 3600, 7200, 14400]
            }
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check for the Risk Compliance module.
        
        Returns:
            Dictionary with health check results
        """
        # In a real implementation, this would check database connections,
        # external API connections, and other dependencies
        
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
        
        # Mock external service status
        external_services = {
            "aml_service": "connected",
            "kyc_verification_service": "connected",
            "sanction_list_database": "connected",
            "regulatory_reporting_engine": "connected"
        }
        
        # If this was a real implementation, we'd check actual service connections
        # and update the status accordingly
        
        return {
            "status": status,
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_bytes": memory_info.rss,
                "memory_percent": memory_percent,
                "active_screenings": 0  # Mock value
            },
            "details": {
                "external_services": external_services,
                "uptime": "08:45:22"  # Mock value
            },
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }


def register_with_admin():
    """Register the Risk Compliance module with the Admin module."""
    try:
        # Create the module registry
        registry = RiskComplianceModuleRegistry()
        
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
        print("Successfully registered Risk Compliance module with Admin module")
    else:
        print("Failed to register Risk Compliance module with Admin module")
        sys.exit(1)
