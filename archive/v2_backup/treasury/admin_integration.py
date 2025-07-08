"""
Treasury Module Registry

This module implements the Module Registry Interface for the Treasury module.
It registers the Treasury module, its API endpoints, feature flags, and configurations
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

class TreasuryModuleRegistry(BaseModuleRegistry):
    """Treasury module registry implementation."""
    
    def __init__(self):
        """Initialize the Treasury module registry."""
        super().__init__(
            module_id="treasury",
            module_name="Treasury Module",
            version="1.0.0",
            description="Treasury management services including liquidity management, investments, and forex operations."
        )
        self.set_dependencies(["core_banking", "payments"])
    
    def get_api_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get all API endpoints for the Treasury module.
        
        Returns:
            List of API endpoint dictionaries
        """
        return [
            # Liquidity Management Endpoints
            {
                "path": "/api/v1/treasury/liquidity/position",
                "method": "GET",
                "description": "Get current liquidity position",
                "auth_required": True,
                "rate_limit": 100
            },
            {
                "path": "/api/v1/treasury/liquidity/forecast",
                "method": "GET",
                "description": "Get liquidity forecast",
                "auth_required": True,
                "rate_limit": 50
            },
            {
                "path": "/api/v1/treasury/liquidity/transfer",
                "method": "POST",
                "description": "Transfer funds between liquidity pools",
                "auth_required": True,
                "rate_limit": 100
            },
            
            # Investment Management Endpoints
            {
                "path": "/api/v1/treasury/investments/portfolio",
                "method": "GET",
                "description": "Get investment portfolio details",
                "auth_required": True,
                "rate_limit": 100
            },
            {
                "path": "/api/v1/treasury/investments/execute",
                "method": "POST",
                "description": "Execute investment transaction",
                "auth_required": True,
                "rate_limit": 50
            },
            {
                "path": "/api/v1/treasury/investments/history",
                "method": "GET",
                "description": "Get investment transaction history",
                "auth_required": True,
                "rate_limit": 100
            },
            
            # Forex Operations Endpoints
            {
                "path": "/api/v1/treasury/forex/rates",
                "method": "GET",
                "description": "Get current forex rates",
                "auth_required": True,
                "rate_limit": 500
            },
            {
                "path": "/api/v1/treasury/forex/trade",
                "method": "POST",
                "description": "Execute forex trade",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/treasury/forex/exposure",
                "method": "GET",
                "description": "Get current forex exposure",
                "auth_required": True,
                "rate_limit": 100
            },
            
            # Risk Management Endpoints
            {
                "path": "/api/v1/treasury/risk/var",
                "method": "GET",
                "description": "Get Value at Risk (VaR) metrics",
                "auth_required": True,
                "rate_limit": 50
            },
            {
                "path": "/api/v1/treasury/risk/limits/check",
                "method": "POST",
                "description": "Check treasury risk limits",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/treasury/risk/reports",
                "method": "GET",
                "description": "Get treasury risk reports",
                "auth_required": True,
                "rate_limit": 50
            }
        ]
    
    def get_feature_flags(self) -> List[Dict[str, Any]]:
        """
        Get all feature flags for the Treasury module.
        
        Returns:
            List of feature flag dictionaries
        """
        return [
            {
                "name": "enable_automated_liquidity_management",
                "description": "Enable automated liquidity management",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/treasury/liquidity/transfer"
                ]
            },
            {
                "name": "enable_investment_auto_rebalancing",
                "description": "Enable automated portfolio rebalancing",
                "enabled": False,
                "affects_endpoints": [
                    "/api/v1/treasury/investments/execute"
                ]
            },
            {
                "name": "enable_forex_auto_hedging",
                "description": "Enable automated forex hedging",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/treasury/forex/trade"
                ]
            },
            {
                "name": "enable_real_time_var",
                "description": "Enable real-time Value at Risk calculation",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/treasury/risk/var"
                ]
            },
            {
                "name": "enable_market_data_integration",
                "description": "Enable external market data integration",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/treasury/forex/rates",
                    "/api/v1/treasury/investments/portfolio"
                ]
            }
        ]
    
    def get_configurations(self) -> List[Dict[str, Any]]:
        """
        Get all configurations for the Treasury module.
        
        Returns:
            List of configuration dictionaries
        """
        return [
            {
                "key": "liquidity_min_threshold",
                "value": 10000000.0,
                "type": "module",
                "description": "Minimum liquidity threshold in base currency",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "investment_risk_tolerance",
                "value": "moderate",
                "type": "module",
                "description": "Investment risk tolerance level",
                "is_sensitive": False,
                "allowed_values": ["conservative", "moderate", "aggressive"]
            },
            {
                "key": "forex_position_limit",
                "value": 5000000.0,
                "type": "module",
                "description": "Maximum forex position limit in base currency",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "var_confidence_level",
                "value": 0.95,
                "type": "module",
                "description": "Value at Risk (VaR) confidence level",
                "is_sensitive": False,
                "allowed_values": [0.90, 0.95, 0.99]
            },
            {
                "key": "market_data_refresh_interval",
                "value": 300,
                "type": "performance",
                "description": "Market data refresh interval in seconds",
                "is_sensitive": False,
                "allowed_values": [60, 300, 600, 900, 1800]
            },
            {
                "key": "market_data_api_key",
                "value": "dummy-market-data-api-key",
                "type": "security",
                "description": "API key for external market data service",
                "is_sensitive": True,
                "allowed_values": None
            },
            {
                "key": "allowed_investment_instruments",
                "value": ["bonds", "treasury_bills", "money_market", "mutual_funds"],
                "type": "module",
                "description": "List of allowed investment instruments",
                "is_sensitive": False,
                "allowed_values": None
            }
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check for the Treasury module.
        
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
            "market_data_service": "connected",
            "trade_execution_service": "connected",
            "risk_calculation_engine": "connected",
            "liquidity_management_service": "connected"
        }
        
        # If this was a real implementation, we'd check actual service connections
        # and update the status accordingly
        
        return {
            "status": status,
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_bytes": memory_info.rss,
                "memory_percent": memory_percent,
                "active_trades": 0  # Mock value
            },
            "details": {
                "external_services": external_services,
                "uptime": "10:15:45"  # Mock value
            },
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }


def register_with_admin():
    """Register the Treasury module with the Admin module."""
    try:
        # Create the module registry
        registry = TreasuryModuleRegistry()
        
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
        print("Successfully registered Treasury module with Admin module")
    else:
        print("Failed to register Treasury module with Admin module")
        sys.exit(1)
