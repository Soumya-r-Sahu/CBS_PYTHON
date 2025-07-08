"""
Advanced Service Routing and Discovery
Load balancing, health checking, and service discovery for the API Gateway
"""

import asyncio
import time
import logging
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import random
from urllib.parse import urljoin

from ..config import GatewayConfig, ServiceConfig, ROUTE_MAPPINGS

logger = logging.getLogger(__name__)


class ServiceState(Enum):
    """Service health states"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceInstance:
    """Represents a service instance"""
    name: str
    host: str
    port: int
    protocol: str = "http"
    state: ServiceState = ServiceState.UNKNOWN
    last_health_check: Optional[float] = None
    consecutive_failures: int = 0
    response_time: float = 0.0
    load_score: float = 0.0
    
    @property
    def base_url(self) -> str:
        """Get the base URL for this service instance"""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def is_healthy(self) -> bool:
        """Check if service instance is healthy"""
        return self.state == ServiceState.HEALTHY


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"


class ServiceRouter:
    """
    Advanced service router with load balancing and health checking
    """
    
    def __init__(self, services_config: Dict[str, ServiceConfig]):
        self.services_config = services_config
        self.service_instances: Dict[str, List[ServiceInstance]] = {}
        self.round_robin_counters: Dict[str, int] = {}
        self.connection_counts: Dict[str, int] = {}
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        self.load_balancing_strategy = LoadBalancingStrategy.ROUND_ROBIN
        
        # Initialize service instances
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize service instances from configuration"""
        for service_name, config in self.services_config.items():
            instance = ServiceInstance(
                name=service_name,
                host=config.host,
                port=config.port,
                protocol=config.protocol
            )
            
            self.service_instances[service_name] = [instance]
            self.round_robin_counters[service_name] = 0
            self.connection_counts[service_name] = 0
    
    async def get_service_url(self, service_name: str) -> Optional[str]:
        """Get URL for a service using load balancing"""
        if service_name not in self.service_instances:
            logger.error(f"Service {service_name} not found")
            return None
        
        instances = self.service_instances[service_name]
        healthy_instances = [inst for inst in instances if inst.is_healthy]
        
        if not healthy_instances:
            logger.warning(f"No healthy instances for service {service_name}")
            # Return any instance as fallback
            if instances:
                return instances[0].base_url
            return None
        
        # Select instance based on load balancing strategy
        selected_instance = self._select_instance(service_name, healthy_instances)
        
        if selected_instance:
            # Increment connection count
            self.connection_counts[service_name] += 1
            return selected_instance.base_url
        
        return None
    
    def _select_instance(self, service_name: str, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select service instance based on load balancing strategy"""
        if not instances:
            return None
        
        if self.load_balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(service_name, instances)
        elif self.load_balancing_strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection(instances)
        elif self.load_balancing_strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_selection(instances)
        elif self.load_balancing_strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(instances)
        else:
            # Default to round robin
            return self._round_robin_selection(service_name, instances)
    
    def _round_robin_selection(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round robin instance selection"""
        counter = self.round_robin_counters[service_name]
        selected = instances[counter % len(instances)]
        self.round_robin_counters[service_name] = (counter + 1) % len(instances)
        return selected
    
    def _least_connections_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with least connections"""
        return min(instances, key=lambda x: x.load_score)
    
    def _least_response_time_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with least response time"""
        return min(instances, key=lambda x: x.response_time)
    
    async def add_service_instance(self, service_name: str, host: str, port: int, protocol: str = "http"):
        """Add a new service instance"""
        if service_name not in self.service_instances:
            self.service_instances[service_name] = []
        
        instance = ServiceInstance(
            name=service_name,
            host=host,
            port=port,
            protocol=protocol
        )
        
        self.service_instances[service_name].append(instance)
        logger.info(f"Added service instance: {service_name} at {instance.base_url}")
    
    async def remove_service_instance(self, service_name: str, host: str, port: int):
        """Remove a service instance"""
        if service_name not in self.service_instances:
            return
        
        instances = self.service_instances[service_name]
        self.service_instances[service_name] = [
            inst for inst in instances 
            if not (inst.host == host and inst.port == port)
        ]
        
        logger.info(f"Removed service instance: {service_name} at {host}:{port}")
    
    def record_request_completion(self, service_name: str, response_time: float, success: bool):
        """Record completion of a request to update load balancing metrics"""
        if service_name in self.connection_counts:
            self.connection_counts[service_name] = max(0, self.connection_counts[service_name] - 1)
        
        # Update response time for all instances of the service
        if service_name in self.service_instances:
            for instance in self.service_instances[service_name]:
                # Simple exponential moving average
                instance.response_time = (instance.response_time * 0.8) + (response_time * 0.2)
                
                # Update load score (combination of connections and response time)
                connection_load = self.connection_counts.get(service_name, 0)
                instance.load_score = connection_load + (instance.response_time * 100)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {}
        for service_name, instances in self.service_instances.items():
            status[service_name] = {
                "instances": [
                    {
                        "url": inst.base_url,
                        "state": inst.state.value,
                        "last_health_check": inst.last_health_check,
                        "consecutive_failures": inst.consecutive_failures,
                        "response_time": inst.response_time,
                        "load_score": inst.load_score
                    }
                    for inst in instances
                ],
                "healthy_instances": len([inst for inst in instances if inst.is_healthy]),
                "total_instances": len(instances),
                "connection_count": self.connection_counts.get(service_name, 0)
            }
        return status


class HealthChecker:
    """
    Health checking system for service instances
    """
    
    def __init__(self, services_config: Dict[str, ServiceConfig], check_interval: int = 30):
        self.services_config = services_config
        self.check_interval = check_interval
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
    
    async def start_health_checks(self):
        """Start health checking for all services"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting health checks for all services")
        
        for service_name in self.services_config.keys():
            task = asyncio.create_task(self._health_check_loop(service_name))
            self.health_check_tasks[service_name] = task
    
    async def stop_health_checks(self):
        """Stop all health checking tasks"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping health checks")
        
        # Cancel all health check tasks
        for task in self.health_check_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.health_check_tasks:
            await asyncio.gather(*self.health_check_tasks.values(), return_exceptions=True)
        
        self.health_check_tasks.clear()
    
    async def _health_check_loop(self, service_name: str):
        """Continuous health checking loop for a service"""
        while self.is_running:
            try:
                await self._check_service_health(service_name)
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop for {service_name}: {e}")
                await asyncio.sleep(5)  # Short delay on error
    
    async def _check_service_health(self, service_name: str):
        """Check health of a specific service"""
        config = self.services_config.get(service_name)
        if not config:
            return
        
        health_url = f"{config.base_url}{config.health_check_path}"
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(health_url)
                
            response_time = time.time() - start_time
            
            # Update service health status
            await self._update_service_health(
                service_name,
                response.status_code == 200,
                response_time,
                response.json() if response.headers.get("content-type", "").startswith("application/json") else None
            )
            
        except Exception as e:
            logger.warning(f"Health check failed for {service_name}: {e}")
            await self._update_service_health(service_name, False, 0.0, {"error": str(e)})
    
    async def _update_service_health(self, service_name: str, is_healthy: bool, response_time: float, health_data: Optional[Dict] = None):
        """Update health status for a service"""
        # This would update the ServiceRouter's instance health
        # For now, just log the health status
        status = "healthy" if is_healthy else "unhealthy"
        logger.info(f"Service {service_name} health check: {status} (response_time: {response_time:.3f}s)")
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services immediately"""
        results = {}
        
        for service_name in self.services_config.keys():
            try:
                config = self.services_config[service_name]
                health_url = f"{config.base_url}{config.health_check_path}"
                
                start_time = time.time()
                
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(health_url)
                
                response_time = time.time() - start_time
                
                results[service_name] = {
                    "healthy": response.status_code == 200,
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "url": health_url,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
                }
                
            except Exception as e:
                results[service_name] = {
                    "healthy": False,
                    "error": str(e),
                    "url": health_url
                }
        
        return results


class ServiceDiscovery:
    """
    Service discovery system for dynamic service registration
    """
    
    def __init__(self, router: ServiceRouter):
        self.router = router
        self.registered_services: Dict[str, List[Dict[str, Any]]] = {}
    
    async def register_service(self, service_name: str, host: str, port: int, metadata: Optional[Dict] = None):
        """Register a new service instance"""
        if service_name not in self.registered_services:
            self.registered_services[service_name] = []
        
        service_info = {
            "host": host,
            "port": port,
            "metadata": metadata or {},
            "registered_at": time.time()
        }
        
        self.registered_services[service_name].append(service_info)
        
        # Add to router
        await self.router.add_service_instance(service_name, host, port)
        
        logger.info(f"Registered service: {service_name} at {host}:{port}")
    
    async def deregister_service(self, service_name: str, host: str, port: int):
        """Deregister a service instance"""
        if service_name in self.registered_services:
            self.registered_services[service_name] = [
                svc for svc in self.registered_services[service_name]
                if not (svc["host"] == host and svc["port"] == port)
            ]
        
        # Remove from router
        await self.router.remove_service_instance(service_name, host, port)
        
        logger.info(f"Deregistered service: {service_name} at {host}:{port}")
    
    async def discover_services(self, service_name: str) -> List[Dict[str, Any]]:
        """Discover all instances of a service"""
        return self.registered_services.get(service_name, [])
    
    def get_service_registry(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get the complete service registry"""
        return self.registered_services.copy()


def create_route_matcher():
    """Create a route matcher for mapping requests to services"""
    
    def match_route_to_service(path: str) -> Optional[str]:
        """Match a request path to a service"""
        # Exact matches first
        if path in ROUTE_MAPPINGS:
            return ROUTE_MAPPINGS[path]
        
        # Pattern matches
        for route_pattern, service_name in ROUTE_MAPPINGS.items():
            if "{path:path}" in route_pattern:
                # Extract the base path
                base_path = route_pattern.split("{path:path}")[0]
                if path.startswith(base_path):
                    return service_name
            elif path.startswith(route_pattern):
                return service_name
        
        return None
    
    return match_route_to_service


__all__ = [
    "ServiceRouter",
    "HealthChecker", 
    "ServiceDiscovery",
    "ServiceInstance",
    "ServiceState",
    "LoadBalancingStrategy",
    "create_route_matcher"
]
