"""
System health repository implementation.
"""
from typing import Dict, List, Optional, Any
from django.utils import timezone
from datetime import datetime
from dashboard.domain.entities.system_health import SystemHealth as SystemHealthEntity, HealthStatus as HealthStatusEntity
from dashboard.application.interfaces.repositories import SystemHealthRepository
from dashboard.models import SystemHealth as SystemHealthModel, HealthStatus


class DjangoSystemHealthRepository(SystemHealthRepository):
    """Django implementation of the SystemHealthRepository interface."""

    def get_all_health_metrics(self) -> List[SystemHealthEntity]:
        """Get all system health metrics."""
        # Get the latest health metric for each component
        latest_health_metrics = {}
        for health in SystemHealthModel.objects.all().order_by('-timestamp'):
            if health.component not in latest_health_metrics:
                latest_health_metrics[health.component] = health
        
        return [self._to_entity(health) for health in latest_health_metrics.values()]
    
    def get_health_by_component(self, component: str) -> Optional[SystemHealthEntity]:
        """Get health metrics for a specific component."""
        try:
            # Get the latest health metric for the component
            health = SystemHealthModel.objects.filter(
                component=component
            ).order_by('-timestamp').first()
            
            if health:
                return self._to_entity(health)
            return None
        except SystemHealthModel.DoesNotExist:
            return None
    
    def create_health_metric(self, health: SystemHealthEntity) -> SystemHealthEntity:
        """Create a new health metric record."""
        model = SystemHealthModel(
            component=health.component,
            status=health.status.value,
            metrics=health.metrics,
            details=health.details,
            alerts=health.alerts
        )
        model.save()
        return self._to_entity(model)
    
    def update_health_metric(self, health: SystemHealthEntity) -> SystemHealthEntity:
        """Update an existing health metric record."""
        try:
            model = SystemHealthModel.objects.get(id=health.id)
            model.component = health.component
            model.status = health.status.value
            model.metrics = health.metrics
            model.details = health.details
            model.alerts = health.alerts
            model.save()
            return self._to_entity(model)
        except SystemHealthModel.DoesNotExist:
            return None
    
    def get_historical_health(self, component: str, start_time: str, end_time: str) -> List[SystemHealthEntity]:
        """Get historical health metrics for a component."""
        try:
            start_datetime = datetime.fromisoformat(start_time)
            end_datetime = datetime.fromisoformat(end_time)
            
            health_metrics = SystemHealthModel.objects.filter(
                component=component,
                timestamp__range=[start_datetime, end_datetime]
            ).order_by('-timestamp')
            
            return [self._to_entity(health) for health in health_metrics]
        except ValueError:
            # Invalid datetime format
            return []
    
    def _to_entity(self, model: SystemHealthModel) -> SystemHealthEntity:
        """Convert a Django model to a domain entity."""
        return SystemHealthEntity(
            id=str(model.id),
            component=model.component,
            status=HealthStatusEntity(model.status),
            timestamp=model.timestamp.isoformat(),
            metrics=model.metrics,
            details=model.details,
            alerts=model.alerts
        )
