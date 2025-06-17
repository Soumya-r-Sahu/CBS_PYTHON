"""
Audit Service API Controllers

This module contains comprehensive FastAPI controllers for the audit service,
implementing enterprise-grade audit logging, compliance reporting, and security monitoring APIs.
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from ...application.services.audit_services import (
    AuditService, CreateAuditLogUseCase, AuditQueryUseCase, 
    AuditAnalyticsUseCase, AuditLogRequest, SecurityEventRequest,
    ComplianceEventRequest, AuditQueryRequest, AuditAnalyticsRequest
)
from ...infrastructure.database import (
    AuditEventType, AuditSeverity, AuditStatus, UserType, EntityType
)


# Pydantic Models for API Request/Response
class AuditLogCreateRequest(BaseModel):
    """Request model for creating audit logs"""
    event_type: str = Field(..., description="Type of audit event")
    action: str = Field(..., description="Action performed")
    user_id: Optional[str] = Field(None, description="User ID who performed the action")
    user_type: str = Field("customer", description="Type of user")
    user_name: Optional[str] = Field(None, description="Name of the user")
    entity_type: Optional[str] = Field(None, description="Type of entity affected")
    entity_id: Optional[str] = Field(None, description="ID of entity affected")
    entity_name: Optional[str] = Field(None, description="Name of entity affected")
    description: Optional[str] = Field(None, description="Description of the action")
    status: str = Field("success", description="Status of the action")
    severity: str = Field("medium", description="Severity level")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Previous values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    changed_fields: Optional[List[str]] = Field(None, description="Fields that changed")
    session_id: Optional[str] = Field(None, description="Session ID")
    request_id: Optional[str] = Field(None, description="Request ID")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    parent_event_id: Optional[str] = Field(None, description="Parent event ID")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint")
    location_data: Optional[Dict[str, Any]] = Field(None, description="Location information")
    service_name: Optional[str] = Field(None, description="Service name")
    service_version: Optional[str] = Field(None, description="Service version")

    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = [e.value for e in AuditEventType]
        if v not in valid_types:
            raise ValueError(f'Invalid event type. Must be one of: {valid_types}')
        return v

    @validator('severity')
    def validate_severity(cls, v):
        valid_severities = [s.value for s in AuditSeverity]
        if v not in valid_severities:
            raise ValueError(f'Invalid severity. Must be one of: {valid_severities}')
        return v

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = [s.value for s in AuditStatus]
        if v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v


class SecurityEventCreateRequest(BaseModel):
    """Request model for creating security events"""
    event_category: str = Field(..., description="Security event category")
    threat_level: str = Field("medium", description="Threat level")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    target_ip: Optional[str] = Field(None, description="Target IP address")
    attack_type: Optional[str] = Field(None, description="Type of attack")
    attack_vector: Optional[str] = Field(None, description="Attack vector")
    detection_method: Optional[str] = Field(None, description="Detection method")
    mitigation_status: str = Field("pending", description="Mitigation status")
    false_positive: bool = Field(False, description="False positive flag")
    risk_score: float = Field(0.0, description="Risk score", ge=0.0, le=100.0)
    event_data: Optional[Dict[str, Any]] = Field(None, description="Additional event data")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")


class ComplianceEventCreateRequest(BaseModel):
    """Request model for creating compliance events"""
    compliance_framework: str = Field(..., description="Compliance framework (PCI-DSS, SOX, etc.)")
    requirement_id: str = Field(..., description="Specific requirement ID")
    compliance_status: str = Field("compliant", description="Compliance status")
    control_id: Optional[str] = Field(None, description="Control ID")
    assessment_date: Optional[datetime] = Field(None, description="Assessment date")
    next_review_date: Optional[datetime] = Field(None, description="Next review date")
    responsible_party: Optional[str] = Field(None, description="Responsible party")
    evidence_links: Optional[List[str]] = Field(None, description="Evidence links")
    exceptions: Optional[List[str]] = Field(None, description="Exceptions")
    remediation_plan: Optional[str] = Field(None, description="Remediation plan")
    business_impact: Optional[str] = Field(None, description="Business impact")
    risk_rating: str = Field("medium", description="Risk rating")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AuditLogQueryRequest(BaseModel):
    """Request model for querying audit logs"""
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    actions: Optional[List[str]] = Field(None, description="Filter by actions")
    user_ids: Optional[List[str]] = Field(None, description="Filter by user IDs")
    user_types: Optional[List[str]] = Field(None, description="Filter by user types")
    entity_types: Optional[List[str]] = Field(None, description="Filter by entity types")
    entity_ids: Optional[List[str]] = Field(None, description="Filter by entity IDs")
    severities: Optional[List[str]] = Field(None, description="Filter by severities")
    statuses: Optional[List[str]] = Field(None, description="Filter by statuses")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    ip_addresses: Optional[List[str]] = Field(None, description="Filter by IP addresses")
    session_ids: Optional[List[str]] = Field(None, description="Filter by session IDs")
    correlation_ids: Optional[List[str]] = Field(None, description="Filter by correlation IDs")
    search_text: Optional[str] = Field(None, description="Full-text search")
    page: int = Field(1, description="Page number", ge=1)
    page_size: int = Field(50, description="Page size", ge=1, le=1000)
    sort_by: str = Field("timestamp", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v


class AuditLogResponse(BaseModel):
    """Response model for audit logs"""
    log_id: str
    event_type: str
    action: str
    timestamp: datetime
    user_id: Optional[str]
    user_type: str
    user_name: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    entity_name: Optional[str]
    description: Optional[str]
    status: str
    severity: str
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    changed_fields: Optional[List[str]]
    session_id: Optional[str]
    request_id: Optional[str]
    transaction_id: Optional[str]
    correlation_id: Optional[str]
    parent_event_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_fingerprint: Optional[str]
    location_data: Optional[Dict[str, Any]]
    service_name: Optional[str]
    service_version: Optional[str]
    risk_score: Optional[float]
    compliance_flags: Optional[List[str]]
    retention_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]


class SecurityEventResponse(BaseModel):
    """Response model for security events"""
    event_id: str
    event_category: str
    threat_level: str
    timestamp: datetime
    source_ip: Optional[str]
    target_ip: Optional[str]
    attack_type: Optional[str]
    attack_vector: Optional[str]
    detection_method: Optional[str]
    mitigation_status: str
    false_positive: bool
    risk_score: float
    event_data: Optional[Dict[str, Any]]
    user_id: Optional[str]
    session_id: Optional[str]
    correlation_id: Optional[str]
    investigation_notes: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]


class ComplianceEventResponse(BaseModel):
    """Response model for compliance events"""
    event_id: str
    compliance_framework: str
    requirement_id: str
    compliance_status: str
    control_id: Optional[str]
    assessment_date: Optional[datetime]
    next_review_date: Optional[datetime]
    responsible_party: Optional[str]
    evidence_links: Optional[List[str]]
    exceptions: Optional[List[str]]
    remediation_plan: Optional[str]
    business_impact: Optional[str]
    risk_rating: str
    metadata: Optional[Dict[str, Any]]
    audit_log_id: str
    created_at: datetime
    updated_at: Optional[datetime]


class PaginatedResponse(BaseModel):
    """Generic paginated response model"""
    items: List[Dict[str, Any]]
    total_items: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class AnalyticsResponse(BaseModel):
    """Response model for analytics data"""
    metric_name: str
    metric_value: Union[int, float, str]
    metric_type: str
    timestamp: datetime
    dimensions: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    uptime: float
    database_status: str
    service_dependencies: Dict[str, str]


# Security dependency
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract current user from JWT token"""
    # In a real implementation, this would validate the JWT token
    # and extract user information
    return {
        "user_id": "system",
        "user_type": "service",
        "permissions": ["audit:read", "audit:write", "audit:admin"]
    }


def get_database_session():
    """Get database session dependency"""
    # This would be implemented with proper database session management
    pass


class AuditLogController:
    """Main audit log management controller"""

    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service

    async def create_audit_log(
        self,
        request: AuditLogCreateRequest,
        current_user: dict = Depends(get_current_user)
    ) -> AuditLogResponse:
        """Create a new audit log entry"""
        try:
            # Convert request to service format
            audit_request = AuditLogRequest(
                event_type=request.event_type,
                action=request.action,
                user_id=request.user_id,
                user_type=request.user_type,
                user_name=request.user_name,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                entity_name=request.entity_name,
                description=request.description,
                status=request.status,
                severity=request.severity,
                old_values=request.old_values,
                new_values=request.new_values,
                changed_fields=request.changed_fields,
                session_id=request.session_id,
                request_id=request.request_id,
                transaction_id=request.transaction_id,
                correlation_id=request.correlation_id,
                parent_event_id=request.parent_event_id,
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                device_fingerprint=request.device_fingerprint,
                location_data=request.location_data,
                service_name=request.service_name,
                service_version=request.service_version
            )

            # Create audit log
            result = await self.audit_service.create_audit_log(audit_request)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message
                )

            # Convert to response format
            audit_log = result.data
            return AuditLogResponse(
                log_id=str(audit_log.log_id),
                event_type=audit_log.event_type.value,
                action=audit_log.action,
                timestamp=audit_log.timestamp,
                user_id=audit_log.user_id,
                user_type=audit_log.user_type.value,
                user_name=audit_log.user_name,
                entity_type=audit_log.entity_type.value if audit_log.entity_type else None,
                entity_id=audit_log.entity_id,
                entity_name=audit_log.entity_name,
                description=audit_log.description,
                status=audit_log.status.value,
                severity=audit_log.severity.value,
                old_values=audit_log.old_values,
                new_values=audit_log.new_values,
                changed_fields=audit_log.changed_fields,
                session_id=audit_log.session_id,
                request_id=audit_log.request_id,
                transaction_id=audit_log.transaction_id,
                correlation_id=audit_log.correlation_id,
                parent_event_id=audit_log.parent_event_id,
                ip_address=audit_log.ip_address,
                user_agent=audit_log.user_agent,
                device_fingerprint=audit_log.device_fingerprint,
                location_data=audit_log.location_data,
                service_name=audit_log.service_name,
                service_version=audit_log.service_version,
                risk_score=audit_log.risk_score,
                compliance_flags=audit_log.compliance_flags,
                retention_date=audit_log.retention_date,
                created_at=audit_log.created_at,
                updated_at=audit_log.updated_at
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create audit log: {str(e)}"
            )

    async def get_audit_log(
        self,
        log_id: str = Path(..., description="Audit log ID"),
        current_user: dict = Depends(get_current_user)
    ) -> AuditLogResponse:
        """Get audit log by ID"""
        try:
            result = await self.audit_service.get_audit_log_by_id(log_id)
            
            if not result.success:
                if "not found" in result.error_message.lower():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=result.error_message
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message
                )

            audit_log = result.data
            return AuditLogResponse(
                log_id=str(audit_log.log_id),
                event_type=audit_log.event_type.value,
                action=audit_log.action,
                timestamp=audit_log.timestamp,
                user_id=audit_log.user_id,
                user_type=audit_log.user_type.value,
                user_name=audit_log.user_name,
                entity_type=audit_log.entity_type.value if audit_log.entity_type else None,
                entity_id=audit_log.entity_id,
                entity_name=audit_log.entity_name,
                description=audit_log.description,
                status=audit_log.status.value,
                severity=audit_log.severity.value,
                old_values=audit_log.old_values,
                new_values=audit_log.new_values,
                changed_fields=audit_log.changed_fields,
                session_id=audit_log.session_id,
                request_id=audit_log.request_id,
                transaction_id=audit_log.transaction_id,
                correlation_id=audit_log.correlation_id,
                parent_event_id=audit_log.parent_event_id,
                ip_address=audit_log.ip_address,
                user_agent=audit_log.user_agent,
                device_fingerprint=audit_log.device_fingerprint,
                location_data=audit_log.location_data,
                service_name=audit_log.service_name,
                service_version=audit_log.service_version,
                risk_score=audit_log.risk_score,
                compliance_flags=audit_log.compliance_flags,
                retention_date=audit_log.retention_date,
                created_at=audit_log.created_at,
                updated_at=audit_log.updated_at
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get audit log: {str(e)}"
            )

    async def query_audit_logs(
        self,
        query_request: AuditLogQueryRequest,
        current_user: dict = Depends(get_current_user)
    ) -> PaginatedResponse:
        """Query audit logs with filters and pagination"""
        try:
            # Convert request to service format
            audit_query = AuditQueryRequest(
                event_types=query_request.event_types,
                actions=query_request.actions,
                user_ids=query_request.user_ids,
                user_types=query_request.user_types,
                entity_types=query_request.entity_types,
                entity_ids=query_request.entity_ids,
                severities=query_request.severities,
                statuses=query_request.statuses,
                start_date=query_request.start_date,
                end_date=query_request.end_date,
                ip_addresses=query_request.ip_addresses,
                session_ids=query_request.session_ids,
                correlation_ids=query_request.correlation_ids,
                search_text=query_request.search_text,
                page=query_request.page,
                page_size=query_request.page_size,
                sort_by=query_request.sort_by,
                sort_order=query_request.sort_order
            )

            # Execute query
            result = await self.audit_service.query_audit_logs(audit_query)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message
                )

            # Convert results to response format
            audit_logs = []
            for log in result.data['items']:
                audit_logs.append({
                    'log_id': str(log.log_id),
                    'event_type': log.event_type.value,
                    'action': log.action,
                    'timestamp': log.timestamp.isoformat(),
                    'user_id': log.user_id,
                    'user_type': log.user_type.value,
                    'user_name': log.user_name,
                    'entity_type': log.entity_type.value if log.entity_type else None,
                    'entity_id': log.entity_id,
                    'entity_name': log.entity_name,
                    'description': log.description,
                    'status': log.status.value,
                    'severity': log.severity.value,
                    'old_values': log.old_values,
                    'new_values': log.new_values,
                    'changed_fields': log.changed_fields,
                    'session_id': log.session_id,
                    'request_id': log.request_id,
                    'transaction_id': log.transaction_id,
                    'correlation_id': log.correlation_id,
                    'parent_event_id': log.parent_event_id,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'device_fingerprint': log.device_fingerprint,
                    'location_data': log.location_data,
                    'service_name': log.service_name,
                    'service_version': log.service_version,
                    'risk_score': log.risk_score,
                    'compliance_flags': log.compliance_flags,
                    'retention_date': log.retention_date.isoformat() if log.retention_date else None,
                    'created_at': log.created_at.isoformat(),
                    'updated_at': log.updated_at.isoformat() if log.updated_at else None
                })

            return PaginatedResponse(
                items=audit_logs,
                total_items=result.data['total_items'],
                page=result.data['page'],
                page_size=result.data['page_size'],
                total_pages=result.data['total_pages'],
                has_next=result.data['has_next'],
                has_previous=result.data['has_previous']
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to query audit logs: {str(e)}"
            )


class SecurityEventController:
    """Security event management controller"""

    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service

    async def create_security_event(
        self,
        request: SecurityEventCreateRequest,
        current_user: dict = Depends(get_current_user)
    ) -> SecurityEventResponse:
        """Create a new security event"""
        try:
            # Convert request to service format
            security_request = SecurityEventRequest(
                event_category=request.event_category,
                threat_level=request.threat_level,
                source_ip=request.source_ip,
                target_ip=request.target_ip,
                attack_type=request.attack_type,
                attack_vector=request.attack_vector,
                detection_method=request.detection_method,
                mitigation_status=request.mitigation_status,
                false_positive=request.false_positive,
                risk_score=request.risk_score,
                event_data=request.event_data,
                user_id=request.user_id,
                session_id=request.session_id,
                correlation_id=request.correlation_id
            )

            # Create security event
            result = await self.audit_service.create_security_event(security_request)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message
                )

            # Convert to response format
            event = result.data
            return SecurityEventResponse(
                event_id=str(event.event_id),
                event_category=event.event_category,
                threat_level=event.threat_level,
                timestamp=event.timestamp,
                source_ip=event.source_ip,
                target_ip=event.target_ip,
                attack_type=event.attack_type,
                attack_vector=event.attack_vector,
                detection_method=event.detection_method,
                mitigation_status=event.mitigation_status,
                false_positive=event.false_positive,
                risk_score=event.risk_score,
                event_data=event.event_data,
                user_id=event.user_id,
                session_id=event.session_id,
                correlation_id=event.correlation_id,
                investigation_notes=event.investigation_notes,
                resolved_at=event.resolved_at,
                created_at=event.created_at,
                updated_at=event.updated_at
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create security event: {str(e)}"
            )

    async def get_security_events(
        self,
        threat_level: Optional[str] = Query(None, description="Filter by threat level"),
        event_category: Optional[str] = Query(None, description="Filter by event category"),
        start_date: Optional[datetime] = Query(None, description="Start date filter"),
        end_date: Optional[datetime] = Query(None, description="End date filter"),
        resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
        page: int = Query(1, description="Page number", ge=1),
        page_size: int = Query(50, description="Page size", ge=1, le=1000),
        current_user: dict = Depends(get_current_user)
    ) -> PaginatedResponse:
        """Get security events with filtering"""
        try:
            result = await self.audit_service.get_security_events(
                threat_level=threat_level,
                event_category=event_category,
                start_date=start_date,
                end_date=end_date,
                resolved=resolved,
                page=page,
                page_size=page_size
            )
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message
                )

            # Convert results to response format
            events = []
            for event in result.data['items']:
                events.append({
                    'event_id': str(event.event_id),
                    'event_category': event.event_category,
                    'threat_level': event.threat_level,
                    'timestamp': event.timestamp.isoformat(),
                    'source_ip': event.source_ip,
                    'target_ip': event.target_ip,
                    'attack_type': event.attack_type,
                    'attack_vector': event.attack_vector,
                    'detection_method': event.detection_method,
                    'mitigation_status': event.mitigation_status,
                    'false_positive': event.false_positive,
                    'risk_score': event.risk_score,
                    'event_data': event.event_data,
                    'user_id': event.user_id,
                    'session_id': event.session_id,
                    'correlation_id': event.correlation_id,
                    'investigation_notes': event.investigation_notes,
                    'resolved_at': event.resolved_at.isoformat() if event.resolved_at else None,
                    'created_at': event.created_at.isoformat(),
                    'updated_at': event.updated_at.isoformat() if event.updated_at else None
                })

            return PaginatedResponse(
                items=events,
                total_items=result.data['total_items'],
                page=result.data['page'],
                page_size=result.data['page_size'],
                total_pages=result.data['total_pages'],
                has_next=result.data['has_next'],
                has_previous=result.data['has_previous']
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get security events: {str(e)}"
            )


class ComplianceController:
    """Compliance event management controller"""

    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service

    async def create_compliance_event(
        self,
        request: ComplianceEventCreateRequest,
        current_user: dict = Depends(get_current_user)
    ) -> ComplianceEventResponse:
        """Create a new compliance event"""
        try:
            # Convert request to service format
            compliance_request = ComplianceEventRequest(
                compliance_framework=request.compliance_framework,
                requirement_id=request.requirement_id,
                compliance_status=request.compliance_status,
                control_id=request.control_id,
                assessment_date=request.assessment_date,
                next_review_date=request.next_review_date,
                responsible_party=request.responsible_party,
                evidence_links=request.evidence_links,
                exceptions=request.exceptions,
                remediation_plan=request.remediation_plan,
                business_impact=request.business_impact,
                risk_rating=request.risk_rating,
                metadata=request.metadata
            )

            # Create compliance event
            result = await self.audit_service.create_compliance_event(compliance_request)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message
                )

            # Convert to response format
            event = result.data
            return ComplianceEventResponse(
                event_id=str(event.event_id),
                compliance_framework=event.compliance_framework,
                requirement_id=event.requirement_id,
                compliance_status=event.compliance_status,
                control_id=event.control_id,
                assessment_date=event.assessment_date,
                next_review_date=event.next_review_date,
                responsible_party=event.responsible_party,
                evidence_links=event.evidence_links,
                exceptions=event.exceptions,
                remediation_plan=event.remediation_plan,
                business_impact=event.business_impact,
                risk_rating=event.risk_rating,
                metadata=event.metadata,
                audit_log_id=str(event.audit_log_id),
                created_at=event.created_at,
                updated_at=event.updated_at
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create compliance event: {str(e)}"
            )

    async def get_compliance_report(
        self,
        framework: str = Query(..., description="Compliance framework"),
        start_date: Optional[datetime] = Query(None, description="Start date filter"),
        end_date: Optional[datetime] = Query(None, description="End date filter"),
        status: Optional[str] = Query(None, description="Compliance status filter"),
        current_user: dict = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        try:
            result = await self.audit_service.generate_compliance_report(
                framework=framework,
                start_date=start_date,
                end_date=end_date,
                status=status
            )
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message
                )

            return result.data

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate compliance report: {str(e)}"
            )


class AnalyticsController:
    """Audit analytics controller"""

    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service

    async def get_audit_analytics(
        self,
        metric_type: str = Query(..., description="Type of analytics metric"),
        start_date: Optional[datetime] = Query(None, description="Start date filter"),
        end_date: Optional[datetime] = Query(None, description="End date filter"),
        granularity: str = Query("day", description="Time granularity (hour/day/week/month)"),
        filters: Optional[str] = Query(None, description="Additional filters as JSON"),
        current_user: dict = Depends(get_current_user)
    ) -> List[AnalyticsResponse]:
        """Get audit analytics data"""
        try:
            # Parse filters if provided
            filter_dict = {}
            if filters:
                try:
                    filter_dict = json.loads(filters)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid filters JSON format"
                    )

            # Create analytics request
            analytics_request = AuditAnalyticsRequest(
                metric_type=metric_type,
                start_date=start_date,
                end_date=end_date,
                granularity=granularity,
                filters=filter_dict
            )

            result = await self.audit_service.get_audit_analytics(analytics_request)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message
                )

            # Convert to response format
            analytics = []
            for metric in result.data:
                analytics.append(AnalyticsResponse(
                    metric_name=metric['metric_name'],
                    metric_value=metric['metric_value'],
                    metric_type=metric['metric_type'],
                    timestamp=metric['timestamp'],
                    dimensions=metric.get('dimensions'),
                    metadata=metric.get('metadata')
                ))

            return analytics

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get audit analytics: {str(e)}"
            )

    async def get_risk_dashboard(
        self,
        current_user: dict = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get risk assessment dashboard data"""
        try:
            result = await self.audit_service.get_risk_dashboard()
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message
                )

            return result.data

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get risk dashboard: {str(e)}"
            )


class HealthController:
    """Health check controller"""

    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service

    async def health_check(self) -> HealthCheckResponse:
        """Perform health check"""
        try:
            result = await self.audit_service.health_check()
            
            return HealthCheckResponse(
                status=result.get('status', 'unknown'),
                timestamp=datetime.utcnow(),
                version=result.get('version', '2.0.0'),
                uptime=result.get('uptime', 0.0),
                database_status=result.get('database_status', 'unknown'),
                service_dependencies=result.get('service_dependencies', {})
            )

        except Exception as e:
            return HealthCheckResponse(
                status='unhealthy',
                timestamp=datetime.utcnow(),
                version='2.0.0',
                uptime=0.0,
                database_status='error',
                service_dependencies={'error': str(e)}
            )


# FastAPI application factory
def create_audit_api(audit_service: AuditService) -> FastAPI:
    """Create FastAPI application for audit service"""
    
    app = FastAPI(
        title="CBS Platform - Audit Service API",
        description="Comprehensive audit logging, compliance tracking, and security monitoring API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Initialize controllers
    audit_controller = AuditLogController(audit_service)
    security_controller = SecurityEventController(audit_service)
    compliance_controller = ComplianceController(audit_service)
    analytics_controller = AnalyticsController(audit_service)
    health_controller = HealthController(audit_service)

    # Audit Log Routes
    @app.post("/audit-logs", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
    async def create_audit_log(
        request: AuditLogCreateRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new audit log entry"""
        return await audit_controller.create_audit_log(request, current_user)

    @app.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
    async def get_audit_log(
        log_id: str = Path(..., description="Audit log ID"),
        current_user: dict = Depends(get_current_user)
    ):
        """Get audit log by ID"""
        return await audit_controller.get_audit_log(log_id, current_user)

    @app.post("/audit-logs/query", response_model=PaginatedResponse)
    async def query_audit_logs(
        query_request: AuditLogQueryRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Query audit logs with filters and pagination"""
        return await audit_controller.query_audit_logs(query_request, current_user)

    # Security Event Routes
    @app.post("/security-events", response_model=SecurityEventResponse, status_code=status.HTTP_201_CREATED)
    async def create_security_event(
        request: SecurityEventCreateRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new security event"""
        return await security_controller.create_security_event(request, current_user)

    @app.get("/security-events", response_model=PaginatedResponse)
    async def get_security_events(
        threat_level: Optional[str] = Query(None),
        event_category: Optional[str] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        resolved: Optional[bool] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=1000),
        current_user: dict = Depends(get_current_user)
    ):
        """Get security events with filtering"""
        return await security_controller.get_security_events(
            threat_level, event_category, start_date, end_date, resolved, page, page_size, current_user
        )

    # Compliance Routes
    @app.post("/compliance-events", response_model=ComplianceEventResponse, status_code=status.HTTP_201_CREATED)
    async def create_compliance_event(
        request: ComplianceEventCreateRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new compliance event"""
        return await compliance_controller.create_compliance_event(request, current_user)

    @app.get("/compliance/reports/{framework}")
    async def get_compliance_report(
        framework: str = Path(..., description="Compliance framework"),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        status: Optional[str] = Query(None),
        current_user: dict = Depends(get_current_user)
    ):
        """Generate compliance report"""
        return await compliance_controller.get_compliance_report(
            framework, start_date, end_date, status, current_user
        )

    # Analytics Routes
    @app.get("/analytics/{metric_type}", response_model=List[AnalyticsResponse])
    async def get_audit_analytics(
        metric_type: str = Path(..., description="Type of analytics metric"),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        granularity: str = Query("day"),
        filters: Optional[str] = Query(None),
        current_user: dict = Depends(get_current_user)
    ):
        """Get audit analytics data"""
        return await analytics_controller.get_audit_analytics(
            metric_type, start_date, end_date, granularity, filters, current_user
        )

    @app.get("/analytics/dashboard/risk")
    async def get_risk_dashboard(
        current_user: dict = Depends(get_current_user)
    ):
        """Get risk assessment dashboard data"""
        return await analytics_controller.get_risk_dashboard(current_user)

    # Health Check Routes
    @app.get("/health", response_model=HealthCheckResponse)
    async def health_check():
        """Perform health check"""
        return await health_controller.health_check()

    return app


# Export main components
__all__ = [
    'AuditLogController',
    'SecurityEventController', 
    'ComplianceController',
    'AnalyticsController',
    'HealthController',
    'create_audit_api',
    'AuditLogCreateRequest',
    'SecurityEventCreateRequest',
    'ComplianceEventCreateRequest',
    'AuditLogQueryRequest',
    'AuditLogResponse',
    'SecurityEventResponse',
    'ComplianceEventResponse',
    'PaginatedResponse',
    'AnalyticsResponse',
    'HealthCheckResponse'
]
