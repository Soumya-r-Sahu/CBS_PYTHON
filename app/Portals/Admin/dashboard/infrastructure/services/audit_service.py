from datetime import datetime
from typing import Dict, List, Optional

from dashboard.application.interfaces.repositories import AuditLogRepository
from dashboard.application.interfaces.services import AuditService
from dashboard.domain.entities.audit_log import AuditLog


class AuditServiceImpl(AuditService):
    """Implementation of the Audit Service"""
    
    def __init__(self, audit_log_repository: AuditLogRepository):
        self.audit_log_repository = audit_log_repository
    
    def log_action(
        self, 
        user_id: str, 
        action: str, 
        resource_type: str, 
        resource_id: str, 
        details: str, 
        metadata: Optional[Dict] = None
    ) -> AuditLog:
        """Log an administrative action"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            timestamp=datetime.now(),
            details=details,
            metadata=metadata or {}
        )
        
        return self.audit_log_repository.save_audit_log(audit_log)
    
    def get_logs(
        self, 
        user_id: Optional[str] = None, 
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs with optional filtering"""
        return self.audit_log_repository.get_logs(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    def get_recent_activity(self, limit: int = 10) -> List[AuditLog]:
        """Get recent activity logs"""
        return self.audit_log_repository.get_logs(limit=limit)
    
    def get_user_activity(self, user_id: str, limit: int = 100) -> List[AuditLog]:
        """Get activity logs for a specific user"""
        return self.audit_log_repository.get_logs(user_id=user_id, limit=limit)
    
    def delete_old_logs(self, days: int = 90) -> int:
        """Delete logs older than the specified number of days"""
        return self.audit_log_repository.delete_old_logs(days)
    
    def generate_audit_report(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict:
        """Generate an audit report for a specified period"""
        logs = self.audit_log_repository.get_logs(
            start_date=start_date,
            end_date=end_date
        )
        
        # Group logs by user
        user_actions = {}
        for log in logs:
            if log.user_id not in user_actions:
                user_actions[log.user_id] = []
            user_actions[log.user_id].append(log)
        
        # Group logs by action type
        action_counts = {}
        for log in logs:
            if log.action not in action_counts:
                action_counts[log.action] = 0
            action_counts[log.action] += 1
        
        # Group logs by resource type
        resource_counts = {}
        for log in logs:
            if log.resource_type not in resource_counts:
                resource_counts[log.resource_type] = 0
            resource_counts[log.resource_type] += 1
        
        # Create report
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'total_actions': len(logs),
            'users': {
                'count': len(user_actions),
                'details': {
                    user_id: len(actions) for user_id, actions in user_actions.items()
                }
            },
            'actions': action_counts,
            'resources': resource_counts,
        }
        
        return report
