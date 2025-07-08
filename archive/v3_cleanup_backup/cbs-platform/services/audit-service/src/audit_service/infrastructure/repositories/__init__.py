"""
Audit Service Repository Implementations

This module provides repository implementations for audit data access
using SQLAlchemy ORM with comprehensive querying and analytics capabilities.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text, between
from sqlalchemy.exc import SQLAlchemyError

from ..database import (
    AuditLogModel, SecurityEventModel, ComplianceEventModel, AuditTrailModel,
    AuditConfigurationModel, AuditMetricsModel, DataRetentionLogModel,
    AuditEventType, AuditSeverity, AuditStatus, UserType, EntityType
)


class SQLAuditLogRepository:
    """SQL implementation of audit log repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_audit_log(self, log_data: Dict[str, Any]) -> AuditLogModel:
        """Create a new audit log entry"""
        try:
            audit_log = AuditLogModel(
                event_id=log_data.get('event_id') or f"EVT_{uuid.uuid4().hex[:8]}",
                correlation_id=log_data.get('correlation_id'),
                parent_event_id=log_data.get('parent_event_id'),
                event_type=AuditEventType(log_data['event_type']),
                action=log_data['action'],
                description=log_data.get('description'),
                user_id=log_data.get('user_id'),
                user_type=UserType(log_data.get('user_type', 'customer')),
                user_name=log_data.get('user_name'),
                entity_type=EntityType(log_data.get('entity_type')) if log_data.get('entity_type') else None,
                entity_id=log_data.get('entity_id'),
                entity_name=log_data.get('entity_name'),
                status=AuditStatus(log_data.get('status', 'success')),
                severity=AuditSeverity(log_data.get('severity', 'medium')),
                old_values=log_data.get('old_values'),
                new_values=log_data.get('new_values'),
                changed_fields=log_data.get('changed_fields'),
                session_id=log_data.get('session_id'),
                request_id=log_data.get('request_id'),
                transaction_id=log_data.get('transaction_id'),
                ip_address=log_data.get('ip_address'),
                user_agent=log_data.get('user_agent'),
                device_fingerprint=log_data.get('device_fingerprint'),
                location_data=log_data.get('location_data'),
                service_name=log_data.get('service_name'),
                service_version=log_data.get('service_version'),
                endpoint=log_data.get('endpoint'),
                method=log_data.get('method'),
                error_code=log_data.get('error_code'),
                error_message=log_data.get('error_message'),
                error_details=log_data.get('error_details'),
                stack_trace=log_data.get('stack_trace'),
                risk_score=log_data.get('risk_score'),
                compliance_flags=log_data.get('compliance_flags'),
                regulatory_tags=log_data.get('regulatory_tags'),
                timestamp=log_data.get('timestamp', datetime.utcnow()),
                duration_ms=log_data.get('duration_ms'),
                metadata=log_data.get('metadata'),
                tags=log_data.get('tags'),
                retention_category=log_data.get('retention_category', 'standard'),
                expires_at=log_data.get('expires_at')
            )
            
            self.session.add(audit_log)
            self.session.commit()
            self.session.refresh(audit_log)
            return audit_log
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error creating audit log: {str(e)}")
    
    def get_audit_log_by_id(self, log_id: uuid.UUID) -> Optional[AuditLogModel]:
        """Get audit log by ID"""
        return self.session.query(AuditLogModel).filter(
            AuditLogModel.log_id == log_id
        ).first()
    
    def get_audit_log_by_event_id(self, event_id: str) -> Optional[AuditLogModel]:
        """Get audit log by event ID"""
        return self.session.query(AuditLogModel).filter(
            AuditLogModel.event_id == event_id
        ).first()
    
    def search_audit_logs(self, filters: Dict[str, Any], 
                         limit: int = 100, offset: int = 0) -> Tuple[List[AuditLogModel], int]:
        """Search audit logs with comprehensive filters"""
        query = self.session.query(AuditLogModel)
        
        # Apply filters
        if filters.get('user_id'):
            query = query.filter(AuditLogModel.user_id == filters['user_id'])
        
        if filters.get('user_type'):
            query = query.filter(AuditLogModel.user_type == UserType(filters['user_type']))
        
        if filters.get('event_type'):
            if isinstance(filters['event_type'], list):
                query = query.filter(AuditLogModel.event_type.in_([AuditEventType(t) for t in filters['event_type']]))
            else:
                query = query.filter(AuditLogModel.event_type == AuditEventType(filters['event_type']))
        
        if filters.get('entity_type'):
            query = query.filter(AuditLogModel.entity_type == EntityType(filters['entity_type']))
        
        if filters.get('entity_id'):
            query = query.filter(AuditLogModel.entity_id == filters['entity_id'])
        
        if filters.get('service_name'):
            query = query.filter(AuditLogModel.service_name == filters['service_name'])
        
        if filters.get('status'):
            if isinstance(filters['status'], list):
                query = query.filter(AuditLogModel.status.in_([AuditStatus(s) for s in filters['status']]))
            else:
                query = query.filter(AuditLogModel.status == AuditStatus(filters['status']))
        
        if filters.get('severity'):
            if isinstance(filters['severity'], list):
                query = query.filter(AuditLogModel.severity.in_([AuditSeverity(s) for s in filters['severity']]))
            else:
                query = query.filter(AuditLogModel.severity == AuditSeverity(filters['severity']))
        
        if filters.get('ip_address'):
            query = query.filter(AuditLogModel.ip_address == filters['ip_address'])
        
        if filters.get('session_id'):
            query = query.filter(AuditLogModel.session_id == filters['session_id'])
        
        if filters.get('correlation_id'):
            query = query.filter(AuditLogModel.correlation_id == filters['correlation_id'])
        
        if filters.get('date_from'):
            query = query.filter(AuditLogModel.timestamp >= filters['date_from'])
        
        if filters.get('date_to'):
            query = query.filter(AuditLogModel.timestamp <= filters['date_to'])
        
        if filters.get('tags'):
            # JSON contains filter for tags
            for tag in filters['tags']:
                query = query.filter(AuditLogModel.tags.contains([tag]))
        
        if filters.get('search_text'):
            # Full-text search across multiple fields
            search_term = f"%{filters['search_text']}%"
            query = query.filter(or_(
                AuditLogModel.description.ilike(search_term),
                AuditLogModel.action.ilike(search_term),
                AuditLogModel.error_message.ilike(search_term),
                AuditLogModel.entity_name.ilike(search_term)
            ))
        
        # Get total count
        total_count = query.count()
        
        # Apply ordering and pagination
        audit_logs = query.order_by(desc(AuditLogModel.timestamp)).offset(offset).limit(limit).all()
        
        return audit_logs, total_count
    
    def get_related_events(self, correlation_id: str) -> List[AuditLogModel]:
        """Get all events with the same correlation ID"""
        return self.session.query(AuditLogModel).filter(
            AuditLogModel.correlation_id == correlation_id
        ).order_by(asc(AuditLogModel.timestamp)).all()
    
    def get_user_activity(self, user_id: str, date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None, limit: int = 100) -> List[AuditLogModel]:
        """Get user activity logs"""
        query = self.session.query(AuditLogModel).filter(
            AuditLogModel.user_id == user_id
        )
        
        if date_from:
            query = query.filter(AuditLogModel.timestamp >= date_from)
        
        if date_to:
            query = query.filter(AuditLogModel.timestamp <= date_to)
        
        return query.order_by(desc(AuditLogModel.timestamp)).limit(limit).all()
    
    def get_entity_history(self, entity_type: EntityType, entity_id: str,
                          limit: int = 100) -> List[AuditLogModel]:
        """Get complete history for an entity"""
        return self.session.query(AuditLogModel).filter(
            AuditLogModel.entity_type == entity_type,
            AuditLogModel.entity_id == entity_id
        ).order_by(desc(AuditLogModel.timestamp)).limit(limit).all()
    
    def get_security_events(self, date_from: Optional[datetime] = None,
                           date_to: Optional[datetime] = None, 
                           severity: Optional[List[AuditSeverity]] = None,
                           limit: int = 100) -> List[AuditLogModel]:
        """Get security-related events"""
        query = self.session.query(AuditLogModel).filter(
            AuditLogModel.event_type == AuditEventType.SECURITY_EVENT
        )
        
        if date_from:
            query = query.filter(AuditLogModel.timestamp >= date_from)
        
        if date_to:
            query = query.filter(AuditLogModel.timestamp <= date_to)
        
        if severity:
            query = query.filter(AuditLogModel.severity.in_(severity))
        
        return query.order_by(desc(AuditLogModel.timestamp)).limit(limit).all()
    
    def get_compliance_violations(self, date_from: Optional[datetime] = None,
                                 date_to: Optional[datetime] = None) -> List[AuditLogModel]:
        """Get events that may indicate compliance violations"""
        query = self.session.query(AuditLogModel).filter(
            AuditLogModel.compliance_flags.isnot(None),
            AuditLogModel.status == AuditStatus.FAILURE
        )
        
        if date_from:
            query = query.filter(AuditLogModel.timestamp >= date_from)
        
        if date_to:
            query = query.filter(AuditLogModel.timestamp <= date_to)
        
        return query.order_by(desc(AuditLogModel.timestamp)).all()
    
    def get_audit_statistics(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """Get audit statistics for a date range"""
        query = self.session.query(AuditLogModel).filter(
            between(AuditLogModel.timestamp, date_from, date_to)
        )
        
        total_events = query.count()
        success_events = query.filter(AuditLogModel.status == AuditStatus.SUCCESS).count()
        failure_events = query.filter(AuditLogModel.status == AuditStatus.FAILURE).count()
        security_events = query.filter(AuditLogModel.event_type == AuditEventType.SECURITY_EVENT).count()
        
        # Event type distribution
        event_type_stats = self.session.query(
            AuditLogModel.event_type,
            func.count(AuditLogModel.log_id)
        ).filter(
            between(AuditLogModel.timestamp, date_from, date_to)
        ).group_by(AuditLogModel.event_type).all()
        
        # Service distribution
        service_stats = self.session.query(
            AuditLogModel.service_name,
            func.count(AuditLogModel.log_id)
        ).filter(
            between(AuditLogModel.timestamp, date_from, date_to),
            AuditLogModel.service_name.isnot(None)
        ).group_by(AuditLogModel.service_name).all()
        
        # Top errors
        error_stats = self.session.query(
            AuditLogModel.error_code,
            func.count(AuditLogModel.log_id)
        ).filter(
            between(AuditLogModel.timestamp, date_from, date_to),
            AuditLogModel.error_code.isnot(None)
        ).group_by(AuditLogModel.error_code).order_by(
            desc(func.count(AuditLogModel.log_id))
        ).limit(10).all()
        
        return {
            'total_events': total_events,
            'success_events': success_events,
            'failure_events': failure_events,
            'security_events': security_events,
            'success_rate': (success_events / total_events * 100) if total_events > 0 else 0,
            'event_type_distribution': {str(event_type): count for event_type, count in event_type_stats},
            'service_distribution': {service: count for service, count in service_stats},
            'top_errors': {error_code: count for error_code, count in error_stats}
        }
    
    def delete_old_audit_logs(self, retention_days: int) -> int:
        """Delete audit logs older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        deleted_count = self.session.query(AuditLogModel).filter(
            AuditLogModel.timestamp < cutoff_date,
            or_(
                AuditLogModel.expires_at.is_(None),
                AuditLogModel.expires_at < datetime.utcnow()
            )
        ).delete()
        
        self.session.commit()
        return deleted_count


class SQLSecurityEventRepository:
    """SQL implementation of security event repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_security_event(self, event_data: Dict[str, Any]) -> SecurityEventModel:
        """Create a new security event"""
        try:
            security_event = SecurityEventModel(
                audit_log_id=event_data['audit_log_id'],
                threat_type=event_data.get('threat_type'),
                threat_level=event_data.get('threat_level', 'medium'),
                attack_vector=event_data.get('attack_vector'),
                detection_method=event_data.get('detection_method'),
                detection_confidence=event_data.get('detection_confidence'),
                false_positive_probability=event_data.get('false_positive_probability'),
                response_actions=event_data.get('response_actions'),
                blocked=event_data.get('blocked', False),
                quarantined=event_data.get('quarantined', False),
                impact_score=event_data.get('impact_score'),
                affected_systems=event_data.get('affected_systems'),
                data_classification=event_data.get('data_classification'),
                investigation_status=event_data.get('investigation_status', 'open'),
                assigned_to=event_data.get('assigned_to'),
                security_context=event_data.get('security_context'),
                ioc_indicators=event_data.get('ioc_indicators')
            )
            
            self.session.add(security_event)
            self.session.commit()
            self.session.refresh(security_event)
            return security_event
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error creating security event: {str(e)}")
    
    def update_investigation_status(self, event_id: uuid.UUID, status: str,
                                   assigned_to: Optional[str] = None,
                                   resolution_notes: Optional[str] = None) -> bool:
        """Update security event investigation status"""
        try:
            security_event = self.session.query(SecurityEventModel).filter(
                SecurityEventModel.event_id == event_id
            ).first()
            
            if security_event:
                security_event.investigation_status = status
                if assigned_to:
                    security_event.assigned_to = assigned_to
                if resolution_notes:
                    security_event.resolution_notes = resolution_notes
                if status == 'resolved':
                    security_event.resolved_at = datetime.utcnow()
                security_event.updated_at = datetime.utcnow()
                
                self.session.commit()
                return True
            
            return False
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error updating security event: {str(e)}")
    
    def get_open_security_events(self, threat_level: Optional[str] = None) -> List[SecurityEventModel]:
        """Get open security events"""
        query = self.session.query(SecurityEventModel).filter(
            SecurityEventModel.investigation_status == 'open'
        )
        
        if threat_level:
            query = query.filter(SecurityEventModel.threat_level == threat_level)
        
        return query.order_by(desc(SecurityEventModel.created_at)).all()
    
    def get_threat_intelligence(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """Get threat intelligence analytics"""
        query = self.session.query(SecurityEventModel).filter(
            between(SecurityEventModel.created_at, date_from, date_to)
        )
        
        total_threats = query.count()
        
        # Threat type distribution
        threat_types = self.session.query(
            SecurityEventModel.threat_type,
            func.count(SecurityEventModel.event_id)
        ).filter(
            between(SecurityEventModel.created_at, date_from, date_to)
        ).group_by(SecurityEventModel.threat_type).all()
        
        # Threat level distribution
        threat_levels = self.session.query(
            SecurityEventModel.threat_level,
            func.count(SecurityEventModel.event_id)
        ).filter(
            between(SecurityEventModel.created_at, date_from, date_to)
        ).group_by(SecurityEventModel.threat_level).all()
        
        return {
            'total_threats': total_threats,
            'threat_types': {threat_type: count for threat_type, count in threat_types},
            'threat_levels': {threat_level: count for threat_level, count in threat_levels}
        }


class SQLComplianceEventRepository:
    """SQL implementation of compliance event repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_compliance_event(self, event_data: Dict[str, Any]) -> ComplianceEventModel:
        """Create a new compliance event"""
        try:
            compliance_event = ComplianceEventModel(
                audit_log_id=event_data['audit_log_id'],
                framework=event_data.get('framework'),
                control_id=event_data.get('control_id'),
                control_description=event_data.get('control_description'),
                compliance_status=event_data.get('compliance_status', 'compliant'),
                violation_type=event_data.get('violation_type'),
                violation_severity=event_data.get('violation_severity'),
                regulation=event_data.get('regulation'),
                jurisdiction=event_data.get('jurisdiction'),
                reporting_required=event_data.get('reporting_required', False),
                risk_rating=event_data.get('risk_rating'),
                business_impact=event_data.get('business_impact'),
                mitigation_required=event_data.get('mitigation_required', False),
                remediation_plan=event_data.get('remediation_plan'),
                remediation_deadline=event_data.get('remediation_deadline'),
                remediation_status=event_data.get('remediation_status'),
                evidence_data=event_data.get('evidence_data'),
                attestation_required=event_data.get('attestation_required', False)
            )
            
            self.session.add(compliance_event)
            self.session.commit()
            self.session.refresh(compliance_event)
            return compliance_event
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error creating compliance event: {str(e)}")
    
    def get_compliance_violations(self, framework: Optional[str] = None,
                                 date_from: Optional[datetime] = None,
                                 date_to: Optional[datetime] = None) -> List[ComplianceEventModel]:
        """Get compliance violations"""
        query = self.session.query(ComplianceEventModel).filter(
            ComplianceEventModel.compliance_status.in_(['non_compliant', 'warning'])
        )
        
        if framework:
            query = query.filter(ComplianceEventModel.framework == framework)
        
        if date_from:
            query = query.filter(ComplianceEventModel.created_at >= date_from)
        
        if date_to:
            query = query.filter(ComplianceEventModel.created_at <= date_to)
        
        return query.order_by(desc(ComplianceEventModel.created_at)).all()
    
    def get_compliance_report(self, framework: str, date_from: datetime, 
                            date_to: datetime) -> Dict[str, Any]:
        """Generate compliance report for a framework"""
        query = self.session.query(ComplianceEventModel).filter(
            ComplianceEventModel.framework == framework,
            between(ComplianceEventModel.created_at, date_from, date_to)
        )
        
        total_events = query.count()
        compliant_events = query.filter(ComplianceEventModel.compliance_status == 'compliant').count()
        violations = query.filter(ComplianceEventModel.compliance_status == 'non_compliant').count()
        warnings = query.filter(ComplianceEventModel.compliance_status == 'warning').count()
        
        return {
            'framework': framework,
            'period': {
                'from': date_from.isoformat(),
                'to': date_to.isoformat()
            },
            'total_events': total_events,
            'compliant_events': compliant_events,
            'violations': violations,
            'warnings': warnings,
            'compliance_rate': (compliant_events / total_events * 100) if total_events > 0 else 0
        }


class SQLAuditConfigurationRepository:
    """SQL implementation of audit configuration repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_configuration(self, config_data: Dict[str, Any]) -> AuditConfigurationModel:
        """Create audit configuration"""
        try:
            config = AuditConfigurationModel(
                config_id=config_data['config_id'],
                config_name=config_data['config_name'],
                config_type=config_data['config_type'],
                description=config_data.get('description'),
                rule_conditions=config_data.get('rule_conditions'),
                rule_actions=config_data.get('rule_actions'),
                applies_to_services=config_data.get('applies_to_services'),
                applies_to_event_types=config_data.get('applies_to_event_types'),
                applies_to_user_types=config_data.get('applies_to_user_types'),
                is_active=config_data.get('is_active', True),
                priority=config_data.get('priority', 1),
                retention_days=config_data.get('retention_days'),
                archive_after_days=config_data.get('archive_after_days'),
                delete_after_days=config_data.get('delete_after_days'),
                alert_thresholds=config_data.get('alert_thresholds'),
                notification_channels=config_data.get('notification_channels'),
                created_by=config_data.get('created_by')
            )
            
            self.session.add(config)
            self.session.commit()
            self.session.refresh(config)
            return config
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error creating audit configuration: {str(e)}")
    
    def get_active_configurations(self, config_type: Optional[str] = None) -> List[AuditConfigurationModel]:
        """Get active audit configurations"""
        query = self.session.query(AuditConfigurationModel).filter(
            AuditConfigurationModel.is_active == True
        )
        
        if config_type:
            query = query.filter(AuditConfigurationModel.config_type == config_type)
        
        return query.order_by(asc(AuditConfigurationModel.priority)).all()


# Export all repositories
__all__ = [
    'SQLAuditLogRepository',
    'SQLSecurityEventRepository',
    'SQLComplianceEventRepository',
    'SQLAuditConfigurationRepository'
]
