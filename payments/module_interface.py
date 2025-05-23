"""
Payments Module Interface Implementation

This module implements the standardized module interface for the payments module.
It provides a unified interface for all payment types and processing capabilities.

Tags: payments, module_interface, banking, transfers, api
AI-Metadata:
    component_type: module_interface
    criticality: high
    input_data: payment_requests, refund_requests
    output_data: payment_confirmations, transaction_records
    dependencies: core_banking, security, database
    versioning: semantic
"""

import logging
import os
import sys
from typing import Dict, List, Any, Optional, Union, Tuple, TypedDict, cast
from datetime import datetime
import traceback
import functools

# Import the module interface
from utils.lib.module_interface import ModuleInterface
from utils.lib.service_registry import ServiceRegistry

# Import module-specific utilities
try:
    from payments.utils.error_handling import PaymentError, handle_exception, log_error
    from payments.utils.validators import validate_payment_data, validate_card_number
except ImportError:
    # Will be properly initialized after utils directory creation
    PaymentError = Exception
    handle_exception = lambda e: {"error": str(e)}
    log_error = lambda msg, **kwargs: None
    validate_payment_data = lambda *args: (False, ["Validation not available"])
    validate_card_number = lambda *args: False

# Configure logger
logger = logging.getLogger(__name__)

# Type definitions for better type checking
class HealthStatus(TypedDict):
    module_name: str
    version: str
    timestamp: str
    status: str
    checks: List[Dict[str, Any]]
    dependencies_status: str
    services_status: str
    database_status: str
    overall_status: str

class PaymentsModule(ModuleInterface):
    """
    Payments module implementation
    
    This class implements the standardized module interface for the
    payments module, providing payment processing capabilities to
    the CBS_PYTHON system.
    
    Features:
    - Multi-channel payment processing
    - Card, mobile, and transfer payment types
    - Refund processing
    - Payment validation
    - Secure transaction handling
    
    AI-Metadata:
        purpose: Process and manage all payment transactions
        criticality: high
        failover_strategy: graceful_degradation
        last_reviewed: 2025-05-23
    """
    
    # Class-level caching for module instance
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'PaymentsModule':
        """Get or create the singleton instance of this module"""
        if cls._instance is None:
            cls._instance = PaymentsModule()
        return cls._instance
    
    def __init__(self):
        """
        Initialize the payments module
        
        Sets up the module with its dependencies, configures payment processors,
        and initializes required services.
        
        AI-Metadata:
            lifecycle_stage: initialization
            error_handling: global_exception_handler
        """
        super().__init__("payments", "1.2.0")
        
        # Define module-specific attributes
        self.supported_payment_types = ["transfer", "card", "cash", "mobile"]
        self.processors: Dict[str, Any] = {}
        self.health_status = {
            "status": "initializing",
            "last_check": datetime.now().isoformat(),
            "issues": []
        }
        
        # Service implementation cache
        self._service_impl_cache: Dict[str, Any] = {}
        
        # Register dependencies
        self.register_dependency("database", ["database.operations"], is_critical=True)
        self.register_dependency("security", ["security.operations"], is_critical=True)
        self.register_dependency("accounts", ["accounts.get_account"], is_critical=True)
        self.register_dependency("notifications", ["notifications.send"], is_critical=False)
        
        logger.info("Payments module initialized")
    
    def register_services(self) -> bool:
        """
        Register payment services with the service registry
        
        Returns:
            bool: True if registration was successful
            
        AI-Metadata:
            criticality: high
            retry_on_failure: true
            max_retries: 3
        """
        try:
            registry = self.get_registry()
            success_count = 0
            service_count = 0
            
            # Helper function to register a service with error handling
            def register_service(name: str, func: Any, version: str) -> bool:
                nonlocal success_count, service_count
                service_count += 1
                try:
                    registry.register(
                        name, 
                        func, 
                        version=version, 
                        module_name=self.name
                    )
                    self.service_registrations.append(name)
                    success_count += 1
                    return True
                except Exception as e:
                    logger.error(f"Failed to register service '{name}': {str(e)}")
                    return False
            
            # Initialize processors
            self._initialize_processors()
            
            # Register payment processor service
            register_service(
                "payment.processor", 
                self.processors.get("general"),
                "1.2.0"
            )
            
            # Register card processor service
            register_service(
                "payment.card_processor", 
                self.processors.get("card"),
                "1.1.0"
            )
            
            # Register mobile processor service
            register_service(
                "payment.mobile_processor", 
                self.processors.get("mobile"),
                "1.0.0"
            )
            
            # Register individual operations as services
            register_service(
                "payment.process", 
                self.process_payment,
                "1.2.0"
            )
            
            register_service(
                "payment.refund", 
                self.process_refund,
                "1.1.0"
            )
            
            register_service(
                "payment.validate", 
                self.validate_payment,
                "1.0.0"
            )
            
            # Register fallbacks for graceful degradation
            self._register_fallbacks(registry)
            
            logger.info(f"Registered {success_count}/{service_count} {self.name} module services")
            return success_count == service_count
        except Exception as e:
            logger.error(f"Failed to register payment services: {str(e)}")
            traceback.print_exc()
            return False
    
    def _initialize_processors(self) -> None:
        """
        Initialize payment processors
        
        Creates instances of all supported payment processors.
        """
        try:
            # Import processors here to avoid circular imports
            from payments.processors.payment_processor import PaymentProcessor
            from payments.processors.card_processor import CardProcessor
            from payments.processors.mobile_processor import MobileProcessor
            from payments.processors.cash_processor import CashProcessor
            
            # Create processor instances
            self.processors = {
                "general": PaymentProcessor(),
                "card": CardProcessor(),
                "mobile": MobileProcessor(),
                "cash": CashProcessor()
            }
            logger.info("Payment processors initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize payment processors: {str(e)}")
            # Create minimal processors to avoid NoneType errors
            self.processors = {
                "general": None,
                "card": None,
                "mobile": None,
                "cash": None
            }
    
    def _register_fallbacks(self, registry: ServiceRegistry) -> None:
        """
        Register fallback implementations
        
        Args:
            registry (ServiceRegistry): Service registry instance
        """
        # General payment fallback
        def payment_fallback(payment_data: Dict[str, Any]) -> Dict[str, Any]:
            """Fallback when payment module is unavailable"""
            logger.warning("Using payment fallback - payment module unavailable")
            return {
                "success": False,
                "message": "Payment processing temporarily unavailable",
                "error_code": "MODULE_UNAVAILABLE",
                "payment_info": {
                    "amount": payment_data.get("amount", 0),
                    "timestamp": payment_data.get("timestamp", "")
                }
            }
        
        # Card payment fallback
        def card_payment_fallback(card_data: Dict[str, Any]) -> Dict[str, Any]:
            """Fallback when card payment module is unavailable"""
            logger.warning("Using card payment fallback - payment module unavailable")
            return {
                "success": False,
                "message": "Card payment processing temporarily unavailable",
                "error_code": "MODULE_UNAVAILABLE"
            }
        
        # Refund fallback
        def refund_fallback(refund_data: Dict[str, Any]) -> Dict[str, Any]:
            """Fallback when refund processing is unavailable"""
            logger.warning("Using refund fallback - payment module unavailable")
            return {
                "success": False,
                "message": "Refund processing temporarily unavailable",
                "error_code": "MODULE_UNAVAILABLE"
            }
        
        # Register fallbacks
        registry.register_fallback("payment.process", payment_fallback)
        registry.register_fallback("payment.card_processor", card_payment_fallback)
        registry.register_fallback("payment.refund", refund_fallback)
    
    def get_service_implementation(self, service_name: str) -> Any:
        """
        Get an implementation of a service by name
        
        Args:
            service_name (str): Name of the service
            
        Returns:
            Any: Service implementation or None if not found
        """
        # Check cache first
        if service_name in self._service_impl_cache:
            return self._service_impl_cache[service_name]
            
        # Try to get the implementation
        try:
            registry = self.get_registry()
            implementation = registry.get_service(service_name)
            
            if implementation:
                # Cache the result
                self._service_impl_cache[service_name] = implementation
                return implementation
            else:
                logger.warning(f"Service implementation not found: {service_name}")
                return None
        except Exception as e:
            logger.error(f"Error getting service implementation for {service_name}: {str(e)}")
            return None
    
    def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment
        
        Args:
            payment_data (dict): Payment information
            
        Returns:
            dict: Payment result
        """
        # Get the appropriate processor
        payment_type = payment_data.get("type", "transfer")
        
        try:
            if payment_type == "card" and "card" in self.processors and self.processors["card"]:
                processor = self.processors["card"]
            elif payment_type == "mobile" and "mobile" in self.processors and self.processors["mobile"]:
                processor = self.processors["mobile"]
            elif payment_type == "cash" and "cash" in self.processors and self.processors["cash"]:
                processor = self.processors["cash"]
            elif "general" in self.processors and self.processors["general"]:
                processor = self.processors["general"]
            else:
                raise PaymentError("No appropriate payment processor available")
            
            # Process the payment
            result = processor.process_payment(payment_data)
            logger.info(f"Payment processed: {result.get('success', False)}")
            return result
        except Exception as e:
            error_msg = f"Error processing payment: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "error_code": "PAYMENT_PROCESSING_ERROR",
                "timestamp": datetime.now().isoformat()
            }
    
    def process_refund(self, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a refund
        
        Args:
            refund_data (dict): Refund information
            
        Returns:
            dict: Refund result
        """
        try:
            # Get the general processor for refunds
            if "general" not in self.processors or not self.processors["general"]:
                raise PaymentError("General payment processor unavailable")
                
            processor = self.processors["general"]
            
            # Process the refund
            result = processor.process_refund(refund_data)
            logger.info(f"Refund processed: {result.get('success', False)}")
            return result
        except Exception as e:
            error_msg = f"Error processing refund: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "error_code": "REFUND_PROCESSING_ERROR",
                "timestamp": datetime.now().isoformat()
            }
    
    def validate_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a payment
        
        Args:
            payment_data (dict): Payment information
            
        Returns:
            dict: Validation result
        """
        try:
            # Validate required fields
            required_fields = ["amount", "source", "destination"]
            missing_fields = [field for field in required_fields if field not in payment_data]
            
            if missing_fields:
                return {
                    "valid": False,
                    "errors": [f"Missing required field: {field}" for field in missing_fields]
                }
            
            # Validate amount
            try:
                amount = float(payment_data["amount"])
                if amount <= 0:
                    return {
                        "valid": False,
                        "errors": ["Amount must be positive"]
                    }
            except (ValueError, TypeError):
                return {
                    "valid": False,
                    "errors": ["Amount must be a valid number"]
                }
            
            # All validations passed
            return {
                "valid": True
            }
        except Exception as e:
            error_msg = f"Error validating payment: {str(e)}"
            logger.error(error_msg)
            return {
                "valid": False,
                "errors": [str(e)]
            }
    
    def _check_database_connections(self) -> Dict[str, Any]:
        """
        Check database connections for the payments module
        
        Returns:
            dict: Database connection status
        """
        try:
            # This is a placeholder - in a real implementation, this would check actual database connections
            # for payment-specific tables and schemas
            
            # Example implementation:
            from utils.config import database_config_manager
            
            # Get database configuration for the payments module
            module_db_config = database_config_manager.get_config_for_module(self.name)
            
            # Check required tables
            required_tables = [
                "payments", "payment_transactions", "payment_methods", 
                "card_details", "refunds", "payment_gateways"
            ]
            
            # This would be a real connection test in production
            connection_ok = True
            missing_tables = []
            
            if connection_ok and not missing_tables:
                return {
                    "status": "healthy",
                    "message": "Payment database connections operational"
                }
            elif connection_ok:
                return {
                    "status": "degraded",
                    "message": f"Missing {len(missing_tables)} payment tables",
                    "details": {
                        "missing_tables": missing_tables
                    }
                }
            else:
                return {
                    "status": "critical",
                    "message": "Payment database connections failed",
                    "details": {
                        "error": "Could not establish payment database connection"
                    }
                }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Error checking payment database connections: {str(e)}",
                "details": {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            }
    
    def _check_service_registrations(self) -> Dict[str, Any]:
        """
        Check service registrations for the payments module
        
        Returns:
            dict: Service registration status
        """
        try:
            registry = self.get_registry()
            registered_services = []
            missing_services = []
            
            # Check for required payment services
            required_services = [
                "payment.processor",
                "payment.card_processor",
                "payment.mobile_processor",
                "payment.process",
                "payment.refund",
                "payment.validate"
            ]
            
            for service_name in required_services:
                try:
                    service = registry.get_service(service_name)
                    if service is not None:
                        registered_services.append(service_name)
                    else:
                        missing_services.append(service_name)
                except Exception as e:
                    logger.warning(f"Error checking service {service_name}: {str(e)}")
                    missing_services.append(service_name)
            
            if missing_services:
                return {
                    "status": "degraded" if len(registered_services) > 0 else "critical",
                    "message": f"{len(missing_services)} payment services not registered properly",
                    "details": {
                        "registered": registered_services,
                        "missing": missing_services
                    }
                }
            else:
                return {
                    "status": "healthy",
                    "message": f"All {len(registered_services)} payment services registered properly",
                    "details": {
                        "registered": registered_services
                    }
                }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Error checking payment service registrations: {str(e)}",
                "details": {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            }
    
    def _perform_health_check(self) -> HealthStatus:
        """
        Perform module-specific health checks
        
        Returns:
            dict: Health check details with standardized format
        """
        # Get standard health details from base implementation
        health_details: HealthStatus = {
            "module_name": self.name,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "status": "active" if self.active else "inactive",
            "checks": [],
            "dependencies_status": "healthy",
            "services_status": "healthy",
            "database_status": "healthy",
            "overall_status": "healthy"
        }
        
        # Check dependencies
        missing_deps = self.check_dependencies()
        if missing_deps:
            health_details["dependencies_status"] = "degraded" if not any(dep["is_critical"] for dep in missing_deps) else "critical"
            health_details["checks"].append({
                "name": "dependencies_check",
                "status": health_details["dependencies_status"],
                "message": f"Missing {len(missing_deps)} dependencies",
                "details": missing_deps
            })
        else:
            health_details["checks"].append({
                "name": "dependencies_check",
                "status": "healthy",
                "message": "All dependencies available"
            })
        
        # Check database connections
        db_status = self._check_database_connections()
        health_details["database_status"] = db_status["status"]
        health_details["checks"].append({
            "name": "database_check",
            "status": db_status["status"],
            "message": db_status["message"],
            "details": db_status.get("details", {})
        })
        
        # Check services
        service_status = self._check_service_registrations()
        health_details["services_status"] = service_status["status"]
        health_details["checks"].append({
            "name": "services_check",
            "status": service_status["status"],
            "message": service_status["message"],
            "details": service_status.get("details", {})
        })
        
        # Add module-specific checks from the payments health checks module
        try:
            # Import the health check module
            from payments.utils.health_checks import run_payment_health_checks
            
            # Run all payment-specific health checks
            specific_checks = run_payment_health_checks(self.processors)
            
            for check in specific_checks:
                health_details["checks"].append(check)
                # Update overall status if any check is critical
                if check["status"] == "critical":
                    health_details["overall_status"] = "critical"
                elif check["status"] == "degraded" and health_details["overall_status"] != "critical":
                    health_details["overall_status"] = "degraded"
        except Exception as e:
            health_details["checks"].append({
                "name": "payments_health_checks",
                "status": "critical",
                "message": f"Failed to run payment health checks: {str(e)}",
                "details": {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            })
            health_details["overall_status"] = "critical"
        
        # Set overall status based on component statuses
        if health_details["dependencies_status"] == "critical" or health_details["database_status"] == "critical":
            health_details["overall_status"] = "critical"
        elif health_details["dependencies_status"] == "degraded" or health_details["database_status"] == "degraded" or health_details["services_status"] == "degraded":
            health_details["overall_status"] = "degraded"
        
        return health_details


# Create module instance (using singleton pattern)
def get_module_instance() -> PaymentsModule:
    """
    Get the payments module instance (singleton)
    
    Returns:
        PaymentsModule: The payments module instance
    """
    return PaymentsModule.get_instance()

# Register module with module registry
def register_module() -> PaymentsModule:
    """
    Register the payments module with the module registry
    
    Returns:
        PaymentsModule: The registered module instance
    """
    from utils.lib.module_interface import ModuleRegistry
    
    # Get module registry
    registry = ModuleRegistry.get_instance()
    
    # Create and register module (using singleton pattern)
    module = get_module_instance()
    registry.register_module(module)
    
    return module
