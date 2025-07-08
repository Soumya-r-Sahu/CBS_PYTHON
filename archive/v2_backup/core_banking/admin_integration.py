"""
Core Banking Module Registry

This module implements the Module Registry Interface for the Core Banking module.
It registers the Core Banking module, its API endpoints, feature flags, and configurations
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

class CoreBankingModuleRegistry(BaseModuleRegistry):
    """Core Banking module registry implementation."""
    
    def __init__(self):
        """Initialize the Core Banking module registry."""
        super().__init__(
            module_id="core_banking",
            module_name="Core Banking Module",
            version="1.0.0",
            description="Core banking services including accounts, transactions, and customer management."
        )
        # Core Banking is a foundational module with no dependencies
        self.set_dependencies([])
    
    def get_api_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get all API endpoints for the Core Banking module.
        
        Returns:
            List of API endpoint dictionaries
        """
        return [
            # Accounts Endpoints
            {
                "path": "/api/v1/accounts",
                "method": "GET",
                "description": "List all accounts",
                "auth_required": True,
                "rate_limit": 100
            },
            {
                "path": "/api/v1/accounts",
                "method": "POST",
                "description": "Create a new account",
                "auth_required": True,
                "rate_limit": 50
            },
            {
                "path": "/api/v1/accounts/{id}",
                "method": "GET",
                "description": "Get account details",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/accounts/{id}",
                "method": "PUT",
                "description": "Update account",
                "auth_required": True,
                "rate_limit": 50
            },
            {
                "path": "/api/v1/accounts/{id}",
                "method": "DELETE",
                "description": "Close account",
                "auth_required": True,
                "rate_limit": 20
            },
            {
                "path": "/api/v1/accounts/{id}/deposit",
                "method": "POST",
                "description": "Deposit funds to account",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/accounts/{id}/withdraw",
                "method": "POST",
                "description": "Withdraw funds from account",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/accounts/{id}/transfer",
                "method": "POST",
                "description": "Transfer funds between accounts",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/accounts/{id}/statement",
                "method": "GET",
                "description": "Get account statement",
                "auth_required": True,
                "rate_limit": 100
            },
            
            # Customer Management Endpoints
            {
                "path": "/api/v1/customers",
                "method": "GET",
                "description": "List all customers",
                "auth_required": True,
                "rate_limit": 100
            },
            {
                "path": "/api/v1/customers",
                "method": "POST",
                "description": "Create a new customer",
                "auth_required": True,
                "rate_limit": 50
            },
            {
                "path": "/api/v1/customers/{id}",
                "method": "GET",
                "description": "Get customer details",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/customers/{id}",
                "method": "PUT",
                "description": "Update customer",
                "auth_required": True,
                "rate_limit": 50
            },
            {
                "path": "/api/v1/customers/{id}",
                "method": "DELETE",
                "description": "Delete customer",
                "auth_required": True,
                "rate_limit": 20
            },
            {
                "path": "/api/v1/customers/{id}/accounts",
                "method": "GET",
                "description": "Get customer's accounts",
                "auth_required": True,
                "rate_limit": 100
            },
            {
                "path": "/api/v1/customers/{id}/kyc",
                "method": "GET",
                "description": "Get customer KYC details",
                "auth_required": True,
                "rate_limit": 100
            },
            {
                "path": "/api/v1/customers/{id}/kyc",
                "method": "POST",
                "description": "Submit customer KYC documents",
                "auth_required": True,
                "rate_limit": 50
            },
            
            # Transactions Endpoints
            {
                "path": "/api/v1/transactions",
                "method": "GET",
                "description": "List all transactions",
                "auth_required": True,
                "rate_limit": 100
            },
            {
                "path": "/api/v1/transactions/{id}",
                "method": "GET",
                "description": "Get transaction details",
                "auth_required": True,
                "rate_limit": 200
            },
            {
                "path": "/api/v1/transactions/account/{account_id}",
                "method": "GET",
                "description": "Get transactions for an account",
                "auth_required": True,
                "rate_limit": 100
            }
        ]
    
    def get_feature_flags(self) -> List[Dict[str, Any]]:
        """
        Get all feature flags for the Core Banking module.
        
        Returns:
            List of feature flag dictionaries
        """
        return [
            {
                "name": "enable_accounts",
                "description": "Enable account management",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/accounts",
                    "/api/v1/accounts/{id}",
                    "/api/v1/accounts/{id}/deposit",
                    "/api/v1/accounts/{id}/withdraw",
                    "/api/v1/accounts/{id}/transfer",
                    "/api/v1/accounts/{id}/statement"
                ]
            },
            {
                "name": "enable_customer_management",
                "description": "Enable customer management",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/customers",
                    "/api/v1/customers/{id}",
                    "/api/v1/customers/{id}/accounts",
                    "/api/v1/customers/{id}/kyc"
                ]
            },
            {
                "name": "enable_transactions",
                "description": "Enable transaction processing",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/transactions",
                    "/api/v1/transactions/{id}",
                    "/api/v1/transactions/account/{account_id}"
                ]
            },
            {
                "name": "advanced_account_validation",
                "description": "Enable advanced validation for accounts",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/accounts",
                    "/api/v1/accounts/{id}"
                ]
            },
            {
                "name": "kyc_verification",
                "description": "Enable KYC verification",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/customers/{id}/kyc"
                ]
            },
            {
                "name": "detailed_transaction_history",
                "description": "Enable detailed transaction history",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/transactions",
                    "/api/v1/transactions/{id}",
                    "/api/v1/transactions/account/{account_id}"
                ]
            }
        ]
    
    def get_configurations(self) -> List[Dict[str, Any]]:
        """
        Get all configurations for the Core Banking module.
        
        Returns:
            List of configuration dictionaries
        """
        return [
            {
                "key": "minimum_balance",
                "value": 1000.0,
                "type": "module",
                "description": "Minimum balance required for accounts",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "daily_withdrawal_limit",
                "value": 50000.0,
                "type": "module",
                "description": "Maximum daily withdrawal limit",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "transaction_fee_percentage",
                "value": 0.1,
                "type": "module",
                "description": "Transaction fee percentage",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "interest_rates",
                "value": {
                    "savings": 4.0,
                    "current": 0.0,
                    "fixed_deposit": 6.5
                },
                "type": "module",
                "description": "Interest rates for different account types",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "kyc_required_fields",
                "value": [
                    "name",
                    "address",
                    "date_of_birth",
                    "tax_id",
                    "phone_number",
                    "email"
                ],
                "type": "module",
                "description": "Required fields for KYC verification",
                "is_sensitive": False,
                "allowed_values": None
            },
            {
                "key": "transaction_history_days",
                "value": 90,
                "type": "performance",
                "description": "Number of days to keep in transaction history",
                "is_sensitive": False,
                "allowed_values": [30, 60, 90, 180, 365]
            },
            {
                "key": "db_connection_timeout",
                "value": 30,
                "type": "performance",
                "description": "Database connection timeout in seconds",
                "is_sensitive": False,
                "allowed_values": [15, 30, 45, 60]
            },
            {
                "key": "db_connection_pool_size",
                "value": 10,
                "type": "performance",
                "description": "Database connection pool size",
                "is_sensitive": False,
                "allowed_values": [5, 10, 20, 50, 100]
            }
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check for the Core Banking module.
        
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
        
        # Mock database status
        databases = {
            "accounts_db": "connected",
            "customers_db": "connected",
            "transactions_db": "connected"
        }
        
        # If this was a real implementation, we'd check actual database connections
        # and update the status accordingly
        
        return {
            "status": status,
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_bytes": memory_info.rss,
                "memory_percent": memory_percent,
                "active_connections": 0  # Mock value
            },
            "details": {
                "databases": databases,
                "uptime": "24:15:30"  # Mock value
            },
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }


def register_with_admin():
    """Register the Core Banking module with the Admin module."""
    try:
        # Create the module registry
        registry = CoreBankingModuleRegistry()
        
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
        print("Successfully registered Core Banking module with Admin module")
    else:
        print("Failed to register Core Banking module with Admin module")
        sys.exit(1)
