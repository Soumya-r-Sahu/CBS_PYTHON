from typing import Dict, List, Optional

from dashboard.application.interfaces.repositories import SystemHealthRepository, ModuleRepository
from dashboard.application.interfaces.services import MonitoringService, AuditService
from dashboard.domain.entities.system_health import SystemHealth, HealthStatus


class MonitoringServiceImpl(MonitoringService):
    """Implementation of the Monitoring Service"""
    
    def __init__(
        self, 
        health_repository: SystemHealthRepository,
        module_repository: ModuleRepository,
        audit_service: AuditService
    ):
        self.health_repository = health_repository
        self.module_repository = module_repository
        self.audit_service = audit_service
    
    def get_system_health(self) -> SystemHealth:
        """Get overall system health"""
        return self.health_repository.get_latest_health_status()
    
    def get_module_health(self, module_id: str) -> Optional[Dict]:
        """Get health information for a specific module"""
        health = self.health_repository.get_latest_health_status()
        
        if not health or not health.module_status:
            return None
        
        # Find the module in the health data
        for module_status in health.module_status:
            if module_status.get('module_id') == module_id:
                return module_status
        
        return None
    
    def update_system_health(self, health: SystemHealth, user_id: str) -> SystemHealth:
        """Update system health information"""
        saved_health = self.health_repository.save_health_status(health)
        
        # Log this health update
        health_summary = f"System health updated: Status={health.status}, CPU={health.cpu_usage}%, Memory={health.memory_usage}%"
        self.audit_service.log_action(
            user_id=user_id,
            action="UPDATE_HEALTH",
            resource_type="SYSTEM_HEALTH",
            resource_id=str(saved_health.id),
            details=health_summary
        )
        
        return saved_health
    
    def check_all_modules_health(self) -> List[Dict]:
        """Check health for all modules"""
        modules = self.module_repository.get_all_modules()
        results = []
        
        for module in modules:
            # This would typically involve making actual health checks to the modules
            # For now, we'll create placeholder data
            module_health = {
                'module_id': module.id,
                'name': module.name,
                'status': HealthStatus.HEALTHY,  # Default to healthy
                'last_check': None,
                'details': {
                    'response_time': 0,  # ms
                    'error_rate': 0,     # percentage
                    'uptime': 0,         # seconds
                    'last_error': None
                }
            }
            
            # In a real implementation, you would check each module's health endpoint
            # and update the status accordingly
            
            results.append(module_health)
        
        return results
    
    def get_health_history(self, days: int = 7) -> List[SystemHealth]:
        """Get system health history for the specified number of days"""
        return self.health_repository.get_health_history(days)
    
    def generate_performance_report(self) -> Dict:
        """Generate a comprehensive performance report"""
        history = self.health_repository.get_health_history(30)  # Last 30 days
        
        if not history:
            return {
                'status': 'No health data available',
                'data': {}
            }
        
        # Calculate averages and trends
        avg_cpu = sum(h.cpu_usage for h in history) / len(history) if history else 0
        avg_memory = sum(h.memory_usage for h in history) / len(history) if history else 0
        avg_response_time = sum(h.average_response_time for h in history) / len(history) if history else 0
        
        # Count health statuses
        status_counts = {
            'HEALTHY': sum(1 for h in history if h.status == HealthStatus.HEALTHY),
            'DEGRADED': sum(1 for h in history if h.status == HealthStatus.DEGRADED),
            'UNHEALTHY': sum(1 for h in history if h.status == HealthStatus.UNHEALTHY),
        }
        
        # Prepare the report
        report = {
            'status': 'generated',
            'period': f'Last {len(history)} health checks',
            'summary': {
                'average_cpu': round(avg_cpu, 2),
                'average_memory': round(avg_memory, 2),
                'average_response_time': round(avg_response_time, 2),
                'health_status_distribution': status_counts
            },
            'trends': {
                'cpu_usage': [h.cpu_usage for h in history],
                'memory_usage': [h.memory_usage for h in history],
                'response_times': [h.average_response_time for h in history],
            },
            'modules': self.check_all_modules_health()
        }
        
        return report
