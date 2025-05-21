"""
Digital Channels Service Registry

This module manages the service registry for the Digital Channels module.
It provides service discovery and registration for Digital Channels components.

Tags: digital_banking, channels, service_registry, service_discovery
AI-Metadata:
    component_type: service_registry
    criticality: high
    purpose: service_discovery
    impact_on_failure: service_unavailability
    versioning: component_level
"""

import logging
import time
from typing import Dict, List, Any, Callable, Optional, Tuple, Union

# Import the service registry
from utils.lib.service_registry import ServiceRegistry

# Configure logger
logger = logging.getLogger(__name__)

class DigitalChannelsRegistry:
    """
    Service registry manager for Digital Channels module
    
    This class manages service registration and discovery for
    the Digital Channels module, interfacing with the centralized
    service registry.
    
    Features:
    - Channel-specific service registration
    - Service versioning and lifecycle management
    - Fallback handlers for degraded operation
    - Health checking for registered services
    - Metrics collection for service usage
    
    Usage:
        # Initialize registry
        registry = DigitalChannelsRegistry()
        
        # Register a service
        registry.register_service("web.authenticate", authenticate_web_handler)
        
        # Get a service
        auth_service = registry.get_service("web.authenticate")
    
    AI-Metadata:
        purpose: Manage service discovery and registration
        criticality: high
        failover_strategy: use_fallback_handlers
        last_reviewed: 2025-05-19
    """
    
    def __init__(self):
        """
        Initialize the Digital Channels service registry
        
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
        
        logger.info("Digital Channels service registry initialized")
    
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
        """
        try:
            if service_name in self._services:
                logger.warning(f"Service {service_name} already registered, updating")
            
            self._services[service_name] = {
                "handler": handler,
                "version": version,
                "registered_at": time.time(),
                "health": "healthy"
            }
            
            if fallback:
                self._fallbacks[service_name] = fallback
                logger.debug(f"Registered fallback handler for {service_name}")
            
            self._metrics[service_name] = {
                "calls": 0,
                "errors": 0,
                "last_called": None,
                "avg_response_time": 0
            }
            
            logger.info(f"Registered service {service_name} v{version}")
            return True
        except Exception as e:
            logger.error(f"Failed to register service {service_name}: {str(e)}")
            return False
    
    def get_service(self, service_name: str) -> Optional[Callable]:
        """
        Get a service handler by name
        
        Args:
            service_name: Name of the service to retrieve
        
        Returns:
            Callable: Service handler function or None if not found
        
        AI-Metadata:
            criticality: high
            error_handling: return_none
            fallback: use_service_fallback
        """
        if service_name not in self._services:
            logger.warning(f"Service {service_name} not found in registry")
            return None
        
        service = self._services[service_name]
        
        # Check if service is marked as unhealthy
        if service["health"] != "healthy":
            logger.warning(f"Service {service_name} is unhealthy, using fallback if available")
            if service_name in self._fallbacks:
                return self._fallbacks[service_name]
            else:
                logger.error(f"No fallback available for unhealthy service {service_name}")
                return None
        
        return service["handler"]
