"""
Audit log repository implementation.
"""
from typing import Dict, List, Optional, Any
from django.db.models import Q
from dashboard.domain.entities.audit_log import AuditLog as AuditLogEntity, AuditLogAction as AuditLogActionEntity, AuditLogSeverity as AuditLogSeverityEntity
from dashboard.application.interfaces.repositories import AuditLogRepository
from dashboard.models import AuditLog as AuditLogModel, AuditLogAction, AuditLogSeverity


class DjangoAuditLogRepository(AuditLogRepository):
    """Django implementation of the AuditLogRepository interface."""

    def get_all_logs(self, limit: int = 100, offset: int = 0) -> List[AuditLogEntity]:
        """Get all audit logs with pagination."""
        logs = AuditLogModel.objects.all().order_by('-timestamp')[offset:offset + limit]
        return [self._to_entity(log) for log in logs]
    
    def get_log_by_id(self, log_id: str) -> Optional[AuditLogEntity]:
        """Get an audit log by its ID."""
        try:
            log = AuditLogModel.objects.get(id=log_id)
            return self._to_entity(log)
        except AuditLogModel.DoesNotExist:
            return None
    
    def get_logs_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> List[AuditLogEntity]:
        """Get all audit logs for a specific user."""
        logs = AuditLogModel.objects.filter(user_id=user_id).order_by('-timestamp')[offset:offset + limit]
        return [self._to_entity(log) for log in logs]
    
    def get_logs_by_resource(self, resource_type: str, resource_id: str, limit: int = 100, offset: int = 0) -> List[AuditLogEntity]:
        """Get all audit logs for a specific resource."""
        logs = AuditLogModel.objects.filter(
            resource_type=resource_type,
            resource_id=resource_id
        ).order_by('-timestamp')[offset:offset + limit]
        return [self._to_entity(log) for log in logs]
    
    def create_log(self, log: AuditLogEntity) -> AuditLogEntity:
        """Create a new audit log."""
        model = AuditLogModel(
            user_id=log.user_id,
            action=log.action.value,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            severity=log.severity.value,
            details=log.details,
            ip_address=log.ip_address,
            success=log.success,
            error_message=log.error_message
        )
        model.save()
        return self._to_entity(model)
    
    def search_logs(self, criteria: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[AuditLogEntity]:
        """Search audit logs based on criteria."""
        query = Q()
        
        # Build query from criteria
        if 'user_id' in criteria:
            query &= Q(user_id=criteria['user_id'])
        
        if 'action' in criteria:
            query &= Q(action=criteria['action'])
        
        if 'resource_type' in criteria:
            query &= Q(resource_type=criteria['resource_type'])
        
        if 'resource_id' in criteria:
            query &= Q(resource_id=criteria['resource_id'])
        
        if 'severity' in criteria:
            query &= Q(severity=criteria['severity'])
        
        if 'success' in criteria:
            query &= Q(success=criteria['success'])
        
        if 'start_date' in criteria and 'end_date' in criteria:
            query &= Q(timestamp__range=[criteria['start_date'], criteria['end_date']])
        
        logs = AuditLogModel.objects.filter(query).order_by('-timestamp')[offset:offset + limit]
        return [self._to_entity(log) for log in logs]
    
    def _to_entity(self, model: AuditLogModel) -> AuditLogEntity:
        """Convert a Django model to a domain entity."""
        return AuditLogEntity(
            id=str(model.id),
            timestamp=model.timestamp.isoformat(),
            user_id=str(model.user.id) if model.user else None,
            action=AuditLogActionEntity(model.action),
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            severity=AuditLogSeverityEntity(model.severity),
            details=model.details,
            ip_address=model.ip_address,
            success=model.success,
            error_message=model.error_message
        )
