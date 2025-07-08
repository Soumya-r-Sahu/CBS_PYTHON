"""
Audit Service Application Services

This module contains the core business logic and use cases for the audit service,
implementing comprehensive audit logging, compliance tracking, and security monitoring.
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..infrastructure.database import (
    AuditEventType, AuditSeverity, AuditStatus, UserType, EntityType
)
from ..infrastructure.repositories import (
    SQLAuditLogRepository, SQLSecurityEventRepository,
    SQLComplianceEventRepository, SQLAuditConfigurationRepository
)


@dataclass
class AuditLogRequest:
    """Audit log request data structure"""
    event_type: str
    action: str
    user_id: Optional[str] = None
    user_type: str = "customer"
    user_name: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    description: Optional[str] = None
    status: str = "success"
    severity: str = "medium"
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    transaction_id: Optional[str] = None
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None
    service_name: Optional[str] = None
    service_version: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    risk_score: Optional[float] = None
    compliance_flags: Optional[Dict[str, Any]] = None
    regulatory_tags: Optional[List[str]] = None
    duration_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    retention_category: str = "standard"


@dataclass
class SecurityEventRequest:
    """Security event request data structure"""
    audit_log_id: str
    threat_type: Optional[str] = None
    threat_level: str = "medium"
    attack_vector: Optional[str] = None
    detection_method: Optional[str] = None
    detection_confidence: Optional[float] = None
    false_positive_probability: Optional[float] = None
    response_actions: Optional[List[str]] = None
    blocked: bool = False
    quarantined: bool = False
    impact_score: Optional[float] = None
    affected_systems: Optional[List[str]] = None
    data_classification: Optional[str] = None
    security_context: Optional[Dict[str, Any]] = None
    ioc_indicators: Optional[Dict[str, Any]] = None


@dataclass
class ComplianceEventRequest:
    """Compliance event request data structure"""
    audit_log_id: str
    framework: Optional[str] = None
    control_id: Optional[str] = None
    control_description: Optional[str] = None
    compliance_status: str = "compliant"
    violation_type: Optional[str] = None
    violation_severity: Optional[str] = None
    regulation: Optional[str] = None
    jurisdiction: Optional[str] = None
    reporting_required: bool = False
    risk_rating: Optional[str] = None
    business_impact: Optional[str] = None
    mitigation_required: bool = False
    remediation_plan: Optional[str] = None
    remediation_deadline: Optional[datetime] = None
    evidence_data: Optional[Dict[str, Any]] = None
    attestation_required: bool = False


@dataclass
class AuditResponse:
    """Audit service response data structure"""
    success: bool
    event_id: Optional[str] = None
    log_id: Optional[str] = None
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None


class CreateAuditLogUseCase:
    """Use case for creating audit logs"""
    
    def __init__(self, audit_repo: SQLAuditLogRepository,
                 security_repo: SQLSecurityEventRepository,
                 compliance_repo: SQLComplianceEventRepository,
                 config_repo: SQLAuditConfigurationRepository):
        self.audit_repo = audit_repo
        self.security_repo = security_repo
        self.compliance_repo = compliance_repo
        self.config_repo = config_repo
    
    def execute(self, request: AuditLogRequest) -> AuditResponse:
        """Execute audit log creation"""
        try:
            # Validate request
            if not self._validate_request(request):
                return AuditResponse(
                    success=False,
                    error_message="Invalid audit log request"
                )
            
            # Enrich audit data
            enriched_data = self._enrich_audit_data(request)
            
            # Create audit log
            audit_log = self.audit_repo.create_audit_log(enriched_data)
            
            warnings = []
            
            # Create security event if needed
            if self._is_security_event(request):
                try:
                    self._create_security_event(audit_log.log_id, request)
                except Exception as e:
                    warnings.append(f"Failed to create security event: {str(e)}")
            
            # Create compliance event if needed
            if self._is_compliance_event(request):
                try:
                    self._create_compliance_event(audit_log.log_id, request)
                except Exception as e:
                    warnings.append(f"Failed to create compliance event: {str(e)}")
            
            return AuditResponse(
                success=True,
                event_id=audit_log.event_id,
                log_id=str(audit_log.log_id),
                warnings=warnings if warnings else None
            )
            
        except Exception as e:
            return AuditResponse(
                success=False,
                error_message=f"Failed to create audit log: {str(e)}"
            )
    
    def _validate_request(self, request: AuditLogRequest) -> bool:
        """Validate audit log request"""
        if not request.event_type or not request.action:
            return False
        
        try:
            AuditEventType(request.event_type)
            AuditSeverity(request.severity)
            AuditStatus(request.status)
            UserType(request.user_type)
            if request.entity_type:
                EntityType(request.entity_type)
            return True
        except ValueError:
            return False
    
    def _enrich_audit_data(self, request: AuditLogRequest) -> Dict[str, Any]:
        """Enrich audit data with additional context"""
        data = request.__dict__.copy()
        
        # Set timestamp if not provided
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        
        # Generate event ID if not provided
        if not data.get('event_id'):
            data['event_id'] = f"EVT_{uuid.uuid4().hex[:8]}"
        
        # Calculate risk score if not provided
        if data.get('risk_score') is None:
            data['risk_score'] = self._calculate_risk_score(request)
        
        # Set expiry based on retention category
        if not data.get('expires_at'):
            data['expires_at'] = self._calculate_expiry(request.retention_category)
        
        # Add compliance flags based on event characteristics
        if not data.get('compliance_flags'):
            data['compliance_flags'] = self._generate_compliance_flags(request)
        
        return data
    
    def _calculate_risk_score(self, request: AuditLogRequest) -> float:
        """Calculate risk score based on event characteristics"""
        base_score = 0.0
        
        # Event type scoring
        event_risk_scores = {
            'login': 10.0,
            'authentication': 15.0,
            'authorization': 20.0,
            'transaction': 30.0,
            'payment': 35.0,
            'security_event': 80.0,
            'admin_action': 25.0,
            'data_export': 40.0,
            'configuration': 30.0
        }
        
        base_score += event_risk_scores.get(request.event_type, 5.0)
        
        # Status scoring
        if request.status == 'failure':
            base_score *= 2.0
        
        # Severity scoring
        severity_multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5,
            'critical': 2.0
        }
        
        base_score *= severity_multipliers.get(request.severity, 1.0)
        
        # Error conditions
        if request.error_code or request.error_message:
            base_score *= 1.3
        
        # Cap at 100.0
        return min(base_score, 100.0)
    
    def _calculate_expiry(self, retention_category: str) -> datetime:
        """Calculate expiry date based on retention category"""
        retention_periods = {
            'short': 30,    # 30 days
            'standard': 365,  # 1 year
            'long': 2555,   # 7 years
            'permanent': None
        }
        
        days = retention_periods.get(retention_category, 365)
        if days is None:
            return None
        
        return datetime.utcnow() + timedelta(days=days)
    
    def _generate_compliance_flags(self, request: AuditLogRequest) -> Optional[Dict[str, Any]]:
        """Generate compliance flags based on event characteristics"""
        flags = {}
        
        # Financial transaction compliance
        if request.event_type in ['transaction', 'payment', 'transfer']:
            flags['financial_transaction'] = True
            flags['aml_relevant'] = True
        
        # Authentication compliance
        if request.event_type in ['login', 'authentication']:
            flags['access_control'] = True
        
        # Data access compliance
        if request.event_type in ['read', 'data_export']:
            flags['data_access'] = True
            flags['privacy_relevant'] = True
        
        # Administrative actions
        if request.event_type == 'admin_action':
            flags['administrative'] = True
            flags['sox_relevant'] = True
        
        # Security events
        if request.event_type == 'security_event':
            flags['security_incident'] = True
            flags['immediate_review'] = True
        
        return flags if flags else None
    
    def _is_security_event(self, request: AuditLogRequest) -> bool:
        """Determine if this should create a security event"""
        return (
            request.event_type == 'security_event' or
            request.status == 'failure' and request.severity in ['high', 'critical'] or
            request.error_code in ['AUTH_FAILED', 'UNAUTHORIZED_ACCESS', 'SUSPICIOUS_ACTIVITY']
        )
    
    def _is_compliance_event(self, request: AuditLogRequest) -> bool:
        """Determine if this should create a compliance event"""
        return (
            request.compliance_flags is not None or
            request.regulatory_tags is not None or
            request.event_type in ['admin_action', 'configuration', 'data_export']
        )
    
    def _create_security_event(self, audit_log_id: uuid.UUID, request: AuditLogRequest):
        """Create associated security event"""
        security_request = SecurityEventRequest(
            audit_log_id=str(audit_log_id),
            threat_type=self._determine_threat_type(request),
            threat_level=self._map_severity_to_threat_level(request.severity),
            detection_method='audit_rule',
            blocked=request.status == 'failure',
            security_context=request.metadata
        )
        
        self.security_repo.create_security_event(security_request.__dict__)
    
    def _create_compliance_event(self, audit_log_id: uuid.UUID, request: AuditLogRequest):
        """Create associated compliance event"""
        compliance_request = ComplianceEventRequest(
            audit_log_id=str(audit_log_id),
            compliance_status='compliant' if request.status == 'success' else 'warning',
            evidence_data=request.metadata
        )
        
        self.compliance_repo.create_compliance_event(compliance_request.__dict__)
    
    def _determine_threat_type(self, request: AuditLogRequest) -> Optional[str]:
        """Determine threat type based on request characteristics"""
        if request.error_code == 'AUTH_FAILED':
            return 'authentication_failure'
        elif request.error_code == 'UNAUTHORIZED_ACCESS':
            return 'authorization_violation'
        elif request.event_type == 'security_event':
            return 'security_violation'
        return 'unknown'
    
    def _map_severity_to_threat_level(self, severity: str) -> str:
        """Map audit severity to threat level"""
        mapping = {
            'low': 'low',
            'medium': 'medium',
            'high': 'high',
            'critical': 'critical'
        }
        return mapping.get(severity, 'medium')


class AuditQueryUseCase:
    """Use case for querying audit logs"""
    
    def __init__(self, audit_repo: SQLAuditLogRepository,
                 security_repo: SQLSecurityEventRepository,
                 compliance_repo: SQLComplianceEventRepository):
        self.audit_repo = audit_repo
        self.security_repo = security_repo
        self.compliance_repo = compliance_repo
    
    def search_audit_logs(self, filters: Dict[str, Any], 
                         page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Search audit logs with filters"""
        offset = (page - 1) * page_size
        audit_logs, total_count = self.audit_repo.search_audit_logs(
            filters, page_size, offset
        )
        
        return {
            'audit_logs': [self._format_audit_log(log) for log in audit_logs],
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': (total_count + page_size - 1) // page_size
        }
    
    def get_user_activity(self, user_id: str, date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user activity logs"""
        audit_logs = self.audit_repo.get_user_activity(user_id, date_from, date_to, limit)
        return [self._format_audit_log(log) for log in audit_logs]
    
    def get_entity_history(self, entity_type: str, entity_id: str,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get entity change history"""
        try:
            entity_type_enum = EntityType(entity_type)
            audit_logs = self.audit_repo.get_entity_history(entity_type_enum, entity_id, limit)
            return [self._format_audit_log(log) for log in audit_logs]
        except ValueError:
            return []
    
    def get_related_events(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get all related events by correlation ID"""
        audit_logs = self.audit_repo.get_related_events(correlation_id)
        return [self._format_audit_log(log) for log in audit_logs]
    
    def get_security_events(self, date_from: Optional[datetime] = None,
                           date_to: Optional[datetime] = None,
                           threat_level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get security events"""
        security_events = self.security_repo.get_open_security_events(threat_level)
        return [self._format_security_event(event) for event in security_events]
    
    def get_compliance_violations(self, framework: Optional[str] = None,
                                 date_from: Optional[datetime] = None,
                                 date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get compliance violations"""
        violations = self.compliance_repo.get_compliance_violations(framework, date_from, date_to)
        return [self._format_compliance_event(event) for event in violations]
    
    def get_audit_statistics(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """Get audit statistics"""
        return self.audit_repo.get_audit_statistics(date_from, date_to)
    
    def _format_audit_log(self, log) -> Dict[str, Any]:
        """Format audit log for API response"""
        return {
            'log_id': str(log.log_id),
            'event_id': log.event_id,
            'correlation_id': log.correlation_id,
            'event_type': log.event_type.value,
            'action': log.action,
            'description': log.description,
            'user_id': log.user_id,
            'user_type': log.user_type.value if log.user_type else None,
            'user_name': log.user_name,
            'entity_type': log.entity_type.value if log.entity_type else None,
            'entity_id': log.entity_id,
            'entity_name': log.entity_name,
            'status': log.status.value,
            'severity': log.severity.value,
            'old_values': log.old_values,
            'new_values': log.new_values,
            'changed_fields': log.changed_fields,
            'session_id': log.session_id,
            'ip_address': log.ip_address,
            'service_name': log.service_name,
            'error_code': log.error_code,
            'error_message': log.error_message,
            'risk_score': float(log.risk_score) if log.risk_score else None,
            'compliance_flags': log.compliance_flags,
            'regulatory_tags': log.regulatory_tags,
            'timestamp': log.timestamp.isoformat(),
            'duration_ms': log.duration_ms,
            'metadata': log.metadata,
            'tags': log.tags
        }
    
    def _format_security_event(self, event) -> Dict[str, Any]:
        """Format security event for API response"""
        return {
            'event_id': str(event.event_id),
            'audit_log_id': str(event.audit_log_id),
            'threat_type': event.threat_type,
            'threat_level': event.threat_level,
            'attack_vector': event.attack_vector,
            'detection_method': event.detection_method,
            'detection_confidence': float(event.detection_confidence) if event.detection_confidence else None,
            'blocked': event.blocked,
            'quarantined': event.quarantined,
            'impact_score': float(event.impact_score) if event.impact_score else None,
            'investigation_status': event.investigation_status,
            'assigned_to': event.assigned_to,
            'created_at': event.created_at.isoformat(),
            'updated_at': event.updated_at.isoformat() if event.updated_at else None
        }
    
    def _format_compliance_event(self, event) -> Dict[str, Any]:
        """Format compliance event for API response"""
        return {
            'event_id': str(event.event_id),
            'audit_log_id': str(event.audit_log_id),
            'framework': event.framework,
            'control_id': event.control_id,
            'compliance_status': event.compliance_status,
            'violation_type': event.violation_type,
            'violation_severity': event.violation_severity,
            'regulation': event.regulation,
            'jurisdiction': event.jurisdiction,
            'reporting_required': event.reporting_required,
            'remediation_required': event.mitigation_required,
            'remediation_deadline': event.remediation_deadline.isoformat() if event.remediation_deadline else None,
            'created_at': event.created_at.isoformat(),
            'updated_at': event.updated_at.isoformat() if event.updated_at else None
        }


class AuditAnalyticsUseCase:
    """Use case for audit analytics and reporting"""
    
    def __init__(self, audit_repo: SQLAuditLogRepository,
                 security_repo: SQLSecurityEventRepository,
                 compliance_repo: SQLComplianceEventRepository):
        self.audit_repo = audit_repo
        self.security_repo = security_repo
        self.compliance_repo = compliance_repo
    
    def generate_security_report(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """Generate security analytics report"""
        security_events = self.audit_repo.get_security_events(date_from, date_to)
        threat_intelligence = self.security_repo.get_threat_intelligence(date_from, date_to)
        
        return {
            'period': {
                'from': date_from.isoformat(),
                'to': date_to.isoformat()
            },
            'security_events_count': len(security_events),
            'threat_intelligence': threat_intelligence,
            'top_threats': self._analyze_top_threats(security_events),
            'security_trends': self._analyze_security_trends(security_events)
        }
    
    def generate_compliance_report(self, framework: str, date_from: datetime, 
                                  date_to: datetime) -> Dict[str, Any]:
        """Generate compliance report"""
        return self.compliance_repo.get_compliance_report(framework, date_from, date_to)
    
    def _analyze_top_threats(self, security_events) -> List[Dict[str, Any]]:
        """Analyze top security threats"""
        # Simplified threat analysis - in production would be more sophisticated
        threat_counts = {}
        for event in security_events:
            # Extract threat info from metadata if available
            threat = "unknown"
            if hasattr(event, 'security_events') and event.security_events:
                threat = event.security_events[0].threat_type or "unknown"
            
            threat_counts[threat] = threat_counts.get(threat, 0) + 1
        
        return [
            {'threat_type': threat, 'count': count}
            for threat, count in sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)
        ][:10]
    
    def _analyze_security_trends(self, security_events) -> Dict[str, Any]:
        """Analyze security trends"""
        # Simplified trend analysis
        if not security_events:
            return {'trend': 'stable', 'change_percentage': 0}
        
        # Calculate basic trends
        total_events = len(security_events)
        recent_events = sum(1 for event in security_events 
                           if (datetime.utcnow() - event.timestamp).days <= 7)
        
        if total_events == 0:
            return {'trend': 'stable', 'change_percentage': 0}
        
        recent_percentage = (recent_events / total_events) * 100
        
        if recent_percentage > 70:
            trend = 'increasing'
        elif recent_percentage < 30:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'recent_percentage': recent_percentage,
            'total_events': total_events,
            'recent_events': recent_events
        }


class AuditService:
    """Main audit service orchestrating all use cases"""
    
    def __init__(self, audit_repo: SQLAuditLogRepository,
                 security_repo: SQLSecurityEventRepository,
                 compliance_repo: SQLComplianceEventRepository,
                 config_repo: SQLAuditConfigurationRepository):
        
        self.audit_repo = audit_repo
        self.security_repo = security_repo
        self.compliance_repo = compliance_repo
        self.config_repo = config_repo
        
        # Initialize use cases
        self.create_audit_log = CreateAuditLogUseCase(
            audit_repo, security_repo, compliance_repo, config_repo
        )
        self.query_audit = AuditQueryUseCase(
            audit_repo, security_repo, compliance_repo
        )
        self.analytics = AuditAnalyticsUseCase(
            audit_repo, security_repo, compliance_repo
        )
    
    def log_event(self, request: AuditLogRequest) -> AuditResponse:
        """Log an audit event"""
        return self.create_audit_log.execute(request)
    
    def log_transaction(self, transaction_data: Dict[str, Any]) -> AuditResponse:
        """Log a transaction event"""
        request = AuditLogRequest(
            event_type='transaction',
            action=transaction_data.get('action', 'unknown'),
            user_id=transaction_data.get('user_id'),
            entity_type='transaction',
            entity_id=transaction_data.get('transaction_id'),
            description=f"Transaction {transaction_data.get('action', 'processed')}",
            service_name='transaction-service',
            metadata=transaction_data
        )
        return self.create_audit_log.execute(request)
    
    def log_security_event(self, security_data: Dict[str, Any]) -> AuditResponse:
        """Log a security event"""
        request = AuditLogRequest(
            event_type='security_event',
            action=security_data.get('action', 'security_violation'),
            user_id=security_data.get('user_id'),
            description=security_data.get('description', 'Security event detected'),
            severity='high',
            service_name=security_data.get('service_name', 'security-service'),
            ip_address=security_data.get('ip_address'),
            error_code=security_data.get('error_code'),
            metadata=security_data
        )
        return self.create_audit_log.execute(request)
    
    def get_user_audit_trail(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get user audit trail"""
        date_from = datetime.utcnow() - timedelta(days=days)
        return self.query_audit.get_user_activity(user_id, date_from)
    
    def search_events(self, filters: Dict[str, Any], page: int = 1, 
                     page_size: int = 100) -> Dict[str, Any]:
        """Search audit events"""
        return self.query_audit.search_audit_logs(filters, page, page_size)
    
    def get_security_dashboard(self, days: int = 7) -> Dict[str, Any]:
        """Get security dashboard data"""
        date_from = datetime.utcnow() - timedelta(days=days)
        date_to = datetime.utcnow()
        
        return self.analytics.generate_security_report(date_from, date_to)
    
    def get_compliance_dashboard(self, framework: str = 'PCI_DSS', 
                               days: int = 30) -> Dict[str, Any]:
        """Get compliance dashboard data"""
        date_from = datetime.utcnow() - timedelta(days=days)
        date_to = datetime.utcnow()
        
        return self.analytics.generate_compliance_report(framework, date_from, date_to)
    
    def cleanup_old_logs(self, retention_days: int = 365) -> Dict[str, Any]:
        """Cleanup old audit logs"""
        deleted_count = self.audit_repo.delete_old_audit_logs(retention_days)
        
        return {
            'deleted_count': deleted_count,
            'retention_days': retention_days,
            'cleanup_date': datetime.utcnow().isoformat()
        }


# Export main service and data classes
__all__ = [
    'AuditService',
    'AuditLogRequest',
    'SecurityEventRequest', 
    'ComplianceEventRequest',
    'AuditResponse',
    'CreateAuditLogUseCase',
    'AuditQueryUseCase',
    'AuditAnalyticsUseCase'
]
