"""
Risk Compliance Service Registry

This module manages the service registry for the Risk Compliance module.
It provides service discovery and registration for Risk Compliance components.

Tags: risk_compliance, service_registry, service_discovery, regulatory
AI-Metadata:
    component_type: service_registry
    criticality: high
    purpose: service_discovery
    impact_on_failure: regulatory_non_compliance
    versioning: component_level
"""

import logging
import time
from typing import Dict, List, Any, Callable, Optional, Tuple, Union
from datetime import datetime

# Import the service registry
from utils.lib.service_registry import ServiceRegistry

# Import error handling if available
try:
    from risk_compliance.utils.error_handling import log_error, handle_exception
except ImportError:
    # Fallback implementations
    def log_error(message, **kwargs):
        logger.error(message)
        
    def handle_exception(exception, **kwargs):
        return {"error": str(exception)}

# Configure logger
logger = logging.getLogger(__name__)

class RiskComplianceRegistry:
    """
    Service registry manager for Risk Compliance module
    
    This class manages service registration and discovery for
    the Risk Compliance module, interfacing with the centralized
    service registry.
    
    Features:
    - Risk assessment service registration
    - Compliance check service discovery
    - AML screening service management
    - Regulatory reporting service organization
    
    Usage:
        # Initialize registry
        registry = RiskComplianceRegistry()
        
        # Register a service
        registry.register_service("risk.transaction.assess", assess_transaction_risk)
        
        # Get a service
        risk_service = registry.get_service("risk.transaction.assess")
    
    AI-Metadata:
        purpose: Manage service discovery and registration for risk and compliance
        criticality: high
        regulatory_relevance: high
        failover_strategy: strict_enforcement
        last_reviewed: 2025-05-20
    """
    
    def __init__(self):
        """
        Initialize the Risk Compliance service registry
        
        Sets up the registry with default fallbacks and connects to
        the central service registry.
        
        AI-Metadata:
            lifecycle_stage: initialization
            error_handling: log_and_continue
        """
        self._services = {}
        self._fallbacks = {}
        self._metrics = {}
        
        # Get reference to central registry
        self._central_registry = ServiceRegistry()
        
        logger.info("Risk Compliance service registry initialized")
    
    def register_service(self, service_name: str, handler: Callable, 
                       version: str = "1.0.0", fallback: Optional[Callable] = None) -> bool:
        """
        Register a service with the registry
        
        Args:
            service_name: Unique name of the service
            handler: Function that implements the service
            version: Service version
            fallback: Optional fallback handler for degraded operation
        
        Returns:
            bool: True if registration was successful
        
        AI-Metadata:
            criticality: high
            error_handling: log_and_return_false
            regulatory_impact: service_availability
        """
        try:
            if service_name in self._services:
                logger.warning(f"Service {service_name} already registered, updating")
            
            self._services[service_name] = {
                "handler": handler,
                "version": version,
                "registered_at": datetime.now().isoformat(),
                "call_count": 0,
                "last_called": None,
                "errors": 0
            }
            
            # Register with central registry
            self._central_registry.register(
                service_name,
                handler,
                version=version,
                module_name="risk_compliance"
            )
            
            # Register fallback if provided
            if fallback:
                self.register_fallback(service_name, fallback)
            
            logger.info(f"Registered service {service_name} (v{version})")
            return True
        except Exception as e:
            log_error(f"Failed to register service {service_name}", exception=e)
            return False
    
    def register_fallback(self, service_name: str, fallback: Callable) -> bool:
        """
        Register a fallback handler for a service
        
        Args:
            service_name: Name of the service to register fallback for
            fallback: Fallback handler function
        
        Returns:
            bool: True if fallback registration was successful
        
        AI-Metadata:
            purpose: Provide degraded functionality when service is unavailable
            criticality: medium
        """
        try:
            self._fallbacks[service_name] = fallback
            
            # Register with central registry
            self._central_registry.register_fallback(service_name, fallback)
            
            logger.info(f"Registered fallback for {service_name}")
            return True
        except Exception as e:
            log_error(f"Failed to register fallback for {service_name}", exception=e)
            return False
    
    def get_service(self, service_name: str) -> Optional[Callable]:
        """
        Get a service handler by name
        
        Args:
            service_name: Name of the service to retrieve
        
        Returns:
            Callable or None: Service handler function or None if not found
        
        AI-Metadata:
            purpose: Access registered services
            usage_frequency: high
        """
        if service_name in self._services:
            service = self._services[service_name]
            
            # Update metrics
            service["call_count"] += 1
            service["last_called"] = datetime.now().isoformat()
            
            return service["handler"]
        
        logger.warning(f"Service {service_name} not found in Risk Compliance registry")
        return None
    
    def get_fallback(self, service_name: str) -> Optional[Callable]:
        """
        Get a fallback handler for a service
        
        Args:
            service_name: Name of the service to retrieve fallback for
        
        Returns:
            Callable or None: Fallback handler function or None if not found
        """
        return self._fallbacks.get(service_name)
    
    def list_services(self) -> List[Dict[str, Any]]:
        """
        List all registered services
        
        Returns:
            List of dictionaries containing service information
        """
        return [
            {
                "name": name,
                "version": info["version"],
                "registered_at": info["registered_at"],
                "call_count": info["call_count"],
                "last_called": info["last_called"]
            }
            for name, info in self._services.items()
        ]
    
    def deregister_service(self, service_name: str) -> bool:
        """
        Deregister a service from the registry
        
        Args:
            service_name: Name of the service to deregister
        
        Returns:
            bool: True if deregistration was successful
        """
        try:
            if service_name in self._services:
                del self._services[service_name]
                
                # Deregister from central registry
                self._central_registry.deregister(service_name)
                
                logger.info(f"Deregistered service {service_name}")
                return True
            
            logger.warning(f"Service {service_name} not found, cannot deregister")
            return False
        except Exception as e:
            log_error(f"Failed to deregister service {service_name}", exception=e)
            return False

# Create a singleton instance
_instance = None

def get_instance() -> RiskComplianceRegistry:
    """
    Get the singleton instance of the Risk Compliance registry
    
    Returns:
        RiskComplianceRegistry: The singleton instance
    """
    global _instance
    if _instance is None:
        _instance = RiskComplianceRegistry()
    return _instance

def register_risk_compliance_services():
    """
    Register all Risk Compliance services with the registry
    
    This function registers all risk assessment, compliance,
    and regulatory services with the central registry.
    
    Returns:
        bool: True if all services were registered successfully
    """
    registry = get_instance()
    central_registry = ServiceRegistry()
    
    try:
        # Import risk assessment services
        from risk_compliance.risk_scoring.risk_assessor import assess_customer_risk, assess_transaction_risk
        from risk_compliance.regulatory_reporting.report_generator import generate_regulatory_report
        from risk_compliance.fraud_detection.fraud_detector import detect_fraud
        
        # Define fallbacks
        def risk_assessment_fallback(entity_id, **kwargs):
            """Fallback for risk assessment when service is unavailable"""
            logger.warning(f"Using risk assessment fallback for {entity_id}")
            return {
                "success": False,
                "message": "Risk assessment service temporarily unavailable",
                "risk_score": None,
                "entity_id": entity_id,
                "fallback": True,
                "timestamp": datetime.now().isoformat()
            }
        
        def compliance_check_fallback(data, **kwargs):
            """Fallback for compliance checks when service is unavailable"""
            logger.warning("Using compliance check fallback")
            # In compliance context, we must fail safely by assuming non-compliance
            return {
                "success": False,
                "message": "Compliance check service temporarily unavailable",
                "compliant": False,  # Fail safe - assume non-compliant
                "fallback": True,
                "timestamp": datetime.now().isoformat()
            }
        
        # Register services with fallbacks
        registry.register_service("risk.customer.assess", assess_customer_risk, "1.0.0", risk_assessment_fallback)
        registry.register_service("risk.transaction.assess", assess_transaction_risk, "1.0.0", risk_assessment_fallback)
        registry.register_service("regulatory.report.generate", generate_regulatory_report, "1.0.0")
        registry.register_service("fraud.detect", detect_fraud, "1.0.0")
        
        # Register central services for other modules to find
        central_registry.register("risk.customer.assess", assess_customer_risk, "1.0.0", "risk_compliance")
        central_registry.register("risk.transaction.assess", assess_transaction_risk, "1.0.0", "risk_compliance")
        central_registry.register("regulatory.report.generate", generate_regulatory_report, "1.0.0", "risk_compliance")
        central_registry.register("fraud.detect", detect_fraud, "1.0.0", "risk_compliance")
        
        # Register fallbacks centrally
        central_registry.register_fallback("risk.customer.assess", risk_assessment_fallback)
        central_registry.register_fallback("risk.transaction.assess", risk_assessment_fallback)
        central_registry.register_fallback("regulatory.report.generate", lambda *args, **kwargs: {"success": False, "message": "Regulatory reporting unavailable"})
        central_registry.register_fallback("fraud.detect", lambda *args, **kwargs: {"success": False, "message": "Fraud detection unavailable", "safe_to_proceed": False})
        
        logger.info("Risk Compliance services registered successfully")
        return True
    except ImportError as e:
        logger.warning(f"Some Risk Compliance services could not be imported: {str(e)}")
        return False
    except Exception as e:
        log_error("Failed to register Risk Compliance services", exception=e)
        return False

# Register services when this module is imported
try:
    register_risk_compliance_services()
except Exception as e:
    logger.error(f"Error during Risk Compliance service registration: {str(e)}")
