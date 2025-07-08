"""
Health Monitoring and Status Management
Comprehensive health checking and monitoring for the API Gateway
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import httpx

from ..config import GatewayConfig, ServiceConfig

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthMetrics:
    """Health metrics for a service"""
    response_time: float = 0.0
    success_rate: float = 100.0
    error_count: int = 0
    last_error: Optional[str] = None
    uptime: float = 0.0
    last_check: Optional[datetime] = None


class HealthChecker:
    """
    Advanced health checking system with metrics and alerting
    """
    
    def __init__(self, services_config: Dict[str, ServiceConfig], config: GatewayConfig):
        self.services_config = services_config
        self.config = config
        self.health_status: Dict[str, HealthStatus] = {}
        self.health_metrics: Dict[str, HealthMetrics] = {}
        self.health_history: Dict[str, List[Dict[str, Any]]] = {}
        self.check_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        
        # Initialize health status
        for service_name in services_config.keys():
            self.health_status[service_name] = HealthStatus.UNKNOWN
            self.health_metrics[service_name] = HealthMetrics()
            self.health_history[service_name] = []
    
    async def start_health_checks(self):
        """Start continuous health monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting health monitoring system")
        
        # Start health check tasks for each service
        for service_name in self.services_config.keys():
            task = asyncio.create_task(self._health_check_loop(service_name))
            self.check_tasks[service_name] = task
    
    async def stop_health_checks(self):
        """Stop health monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping health monitoring system")
        
        # Cancel all tasks
        for task in self.check_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.check_tasks:
            await asyncio.gather(*self.check_tasks.values(), return_exceptions=True)
        
        self.check_tasks.clear()
    
    async def _health_check_loop(self, service_name: str):
        """Continuous health check loop for a service"""
        interval = self.config.monitoring.health_check_interval
        
        while self.is_running:
            try:
                await self._perform_health_check(service_name)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop for {service_name}: {e}")
                await asyncio.sleep(5)  # Brief delay on error
    
    async def _perform_health_check(self, service_name: str):
        """Perform health check for a specific service"""
        config = self.services_config.get(service_name)
        if not config:
            return
        
        health_url = f"{config.base_url}{config.health_check_path}"
        timeout = self.config.monitoring.health_check_timeout
        
        start_time = time.time()
        success = False
        error_message = None
        response_data = None
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(health_url)
                
            response_time = time.time() - start_time
            success = response.status_code == 200
            
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    response_data = response.json()
                except:
                    pass
            
            # Update metrics
            await self._update_health_metrics(
                service_name, success, response_time, error_message, response_data
            )
            
        except httpx.TimeoutException:
            error_message = f"Health check timeout after {timeout}s"
            response_time = timeout
            await self._update_health_metrics(
                service_name, False, response_time, error_message
            )
            
        except Exception as e:
            error_message = str(e)
            response_time = time.time() - start_time
            await self._update_health_metrics(
                service_name, False, response_time, error_message
            )
    
    async def _update_health_metrics(
        self, 
        service_name: str, 
        success: bool, 
        response_time: float, 
        error_message: Optional[str] = None,
        response_data: Optional[Dict] = None
    ):
        """Update health metrics for a service"""
        metrics = self.health_metrics[service_name]
        current_time = datetime.utcnow()
        
        # Update metrics
        metrics.response_time = (metrics.response_time * 0.8) + (response_time * 0.2)  # EMA
        metrics.last_check = current_time
        
        if not success:
            metrics.error_count += 1
            metrics.last_error = error_message
        
        # Calculate success rate over last 10 checks
        history = self.health_history[service_name]
        history.append({
            "timestamp": current_time.isoformat(),
            "success": success,
            "response_time": response_time,
            "error": error_message,
            "data": response_data
        })
        
        # Keep only last 100 checks
        if len(history) > 100:
            history[:] = history[-100:]
        
        # Calculate success rate over last 10 checks
        recent_checks = history[-10:]
        if recent_checks:
            successful_checks = sum(1 for check in recent_checks if check["success"])
            metrics.success_rate = (successful_checks / len(recent_checks)) * 100
        
        # Determine health status
        old_status = self.health_status[service_name]
        new_status = self._determine_health_status(metrics, recent_checks)
        self.health_status[service_name] = new_status
        
        # Log status changes
        if old_status != new_status:
            logger.warning(f"Service {service_name} status changed: {old_status.value} -> {new_status.value}")
        
        # Log current status
        logger.debug(f"Health check {service_name}: {new_status.value} "
                    f"(response_time: {response_time:.3f}s, success_rate: {metrics.success_rate:.1f}%)")
    
    def _determine_health_status(self, metrics: HealthMetrics, recent_checks: List[Dict]) -> HealthStatus:
        """Determine health status based on metrics"""
        if not recent_checks:
            return HealthStatus.UNKNOWN
        
        # Check if service is completely down
        if metrics.success_rate == 0:
            return HealthStatus.UNHEALTHY
        
        # Check if service is degraded
        if metrics.success_rate < 80 or metrics.response_time > 5.0:
            return HealthStatus.DEGRADED
        
        # Service is healthy
        return HealthStatus.HEALTHY
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Perform immediate health check on all services"""
        results = {}
        
        tasks = []
        service_names = []
        
        for service_name in self.services_config.keys():
            task = asyncio.create_task(self._perform_immediate_health_check(service_name))
            tasks.append(task)
            service_names.append(service_name)
        
        # Wait for all checks to complete
        check_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile results
        for service_name, result in zip(service_names, check_results):
            if isinstance(result, Exception):
                results[service_name] = {
                    "healthy": False,
                    "error": str(result),
                    "status": self.health_status[service_name].value
                }
            else:
                results[service_name] = result
        
        return results
    
    async def _perform_immediate_health_check(self, service_name: str) -> Dict[str, Any]:
        """Perform immediate health check for a service"""
        config = self.services_config.get(service_name)
        if not config:
            return {"healthy": False, "error": "Service configuration not found"}
        
        health_url = f"{config.base_url}{config.health_check_path}"
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(health_url)
            
            response_time = time.time() - start_time
            is_healthy = response.status_code == 200
            
            result = {
                "healthy": is_healthy,
                "status": self.health_status[service_name].value,
                "response_time": response_time,
                "status_code": response.status_code,
                "url": health_url,
                "metrics": {
                    "success_rate": self.health_metrics[service_name].success_rate,
                    "avg_response_time": self.health_metrics[service_name].response_time,
                    "error_count": self.health_metrics[service_name].error_count,
                    "last_error": self.health_metrics[service_name].last_error
                }
            }
            
            # Include response data if JSON
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    result["data"] = response.json()
                except:
                    pass
            
            return result
            
        except Exception as e:
            return {
                "healthy": False,
                "status": self.health_status[service_name].value,
                "error": str(e),
                "url": health_url,
                "metrics": {
                    "success_rate": self.health_metrics[service_name].success_rate,
                    "avg_response_time": self.health_metrics[service_name].response_time,
                    "error_count": self.health_metrics[service_name].error_count,
                    "last_error": self.health_metrics[service_name].last_error
                }
            }
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health information for a specific service"""
        if service_name not in self.health_status:
            return {"error": "Service not found"}
        
        status = self.health_status[service_name]
        metrics = self.health_metrics[service_name]
        history = self.health_history.get(service_name, [])
        
        return {
            "service": service_name,
            "status": status.value,
            "healthy": status == HealthStatus.HEALTHY,
            "metrics": {
                "response_time": metrics.response_time,
                "success_rate": metrics.success_rate,
                "error_count": metrics.error_count,
                "last_error": metrics.last_error,
                "last_check": metrics.last_check.isoformat() if metrics.last_check else None
            },
            "recent_checks": history[-10:],  # Last 10 checks
            "total_checks": len(history)
        }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        total_services = len(self.health_status)
        healthy_services = sum(1 for status in self.health_status.values() if status == HealthStatus.HEALTHY)
        degraded_services = sum(1 for status in self.health_status.values() if status == HealthStatus.DEGRADED)
        unhealthy_services = sum(1 for status in self.health_status.values() if status == HealthStatus.UNHEALTHY)
        
        # Determine overall status
        if unhealthy_services > 0:
            overall_status = "unhealthy"
        elif degraded_services > 0:
            overall_status = "degraded" 
        elif healthy_services == total_services:
            overall_status = "healthy"
        else:
            overall_status = "unknown"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "total": total_services,
                "healthy": healthy_services,
                "degraded": degraded_services,
                "unhealthy": unhealthy_services,
                "unknown": total_services - healthy_services - degraded_services - unhealthy_services
            },
            "service_status": {
                service: status.value 
                for service, status in self.health_status.items()
            }
        }
    
    def get_health_history(self, service_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get health check history for a service"""
        if service_name not in self.health_history:
            return []
        
        return self.health_history[service_name][-limit:]
    
    def get_all_health_metrics(self) -> Dict[str, Any]:
        """Get comprehensive health metrics for all services"""
        return {
            "overall": self.get_overall_health(),
            "services": {
                service_name: self.get_service_health(service_name)
                for service_name in self.health_status.keys()
            }
        }


__all__ = [
    "HealthChecker",
    "HealthStatus", 
    "HealthMetrics"
]
