"""
Audit Service Database Models

This module contains all database models for the audit service,
implementing comprehensive audit logging and compliance functionality.
"""

import enum
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, 
    JSON, Index, ForeignKey, Enum as SQLEnum, 
    Numeric, create_engine, event, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID

# Base class for all models
Base = declarative_base()


class AuditEventType(enum.Enum):
    """Audit event type enumeration"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    TRANSACTION = "transaction"
    PAYMENT = "payment"
    TRANSFER = "transfer"
    ACCOUNT_CHANGE = "account_change"
    CUSTOMER_CHANGE = "customer_change"
    SECURITY_EVENT = "security_event"
    SYSTEM_EVENT = "system_event"
    CONFIGURATION = "configuration"
    ADMIN_ACTION = "admin_action"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    BACKUP = "backup"
    RESTORE = "restore"


class AuditSeverity(enum.Enum):
    """Audit severity enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(enum.Enum):
    """Audit status enumeration"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"
    CANCELLED = "cancelled"


class UserType(enum.Enum):
    """User type enumeration"""
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    ADMIN = "admin"
    SYSTEM = "system"
    API = "api"
    SERVICE = "service"


class EntityType(enum.Enum):
    """Entity type enumeration"""
    CUSTOMER = "customer"
    ACCOUNT = "account"
    TRANSACTION = "transaction"
    PAYMENT = "payment"
    LOAN = "loan"
    CARD = "card"
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
    CONFIG = "config"
    NOTIFICATION = "notification"
    REPORT = "report"


class AuditLogModel(Base):
    """Main audit log database model"""
    __tablename__ = 'audit_logs'

    # Primary key
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event identification
    event_id = Column(String(100), unique=True, nullable=False, index=True)
    correlation_id = Column(String(100), index=True)  # For linking related events
    parent_event_id = Column(String(100), index=True)  # For event hierarchies
    
    # Event details
    event_type = Column(SQLEnum(AuditEventType), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    description = Column(Text)
    
    # User information
    user_id = Column(String(50), index=True)
    user_type = Column(SQLEnum(UserType), default=UserType.CUSTOMER)
    user_name = Column(String(100))
    
    # Entity information
    entity_type = Column(SQLEnum(EntityType), index=True)
    entity_id = Column(String(100), index=True)
    entity_name = Column(String(200))
    
    # Status and severity
    status = Column(SQLEnum(AuditStatus), default=AuditStatus.SUCCESS, index=True)
    severity = Column(SQLEnum(AuditSeverity), default=AuditSeverity.MEDIUM, index=True)
    
    # Data changes
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state
    changed_fields = Column(JSON)  # List of changed field names
    
    # Context information
    session_id = Column(String(100), index=True)
    request_id = Column(String(100), index=True)
    transaction_id = Column(String(100), index=True)
    
    # Network and client details
    ip_address = Column(String(45))  # Supports IPv6
    user_agent = Column(Text)
    device_fingerprint = Column(String(255))
    
    # Location information
    location_data = Column(JSON)  # Country, city, coordinates, etc.
    
    # Service information
    service_name = Column(String(50), index=True)
    service_version = Column(String(20))
    endpoint = Column(String(255))
    method = Column(String(10))  # HTTP method
    
    # Error information
    error_code = Column(String(50))
    error_message = Column(Text)
    error_details = Column(JSON)
    stack_trace = Column(Text)
    
    # Compliance and risk
    risk_score = Column(Numeric(5, 2))  # 0.00 to 100.00
    compliance_flags = Column(JSON)
    regulatory_tags = Column(JSON)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    duration_ms = Column(Integer)  # Event duration in milliseconds
    
    # Additional metadata
    metadata = Column(JSON)
    tags = Column(JSON)  # Array of tags for categorization
    
    # Data retention
    retention_category = Column(String(50), default='standard')
    expires_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_entity_timestamp', 'entity_type', 'entity_id', 'timestamp'),
        Index('idx_audit_event_timestamp', 'event_type', 'timestamp'),
        Index('idx_audit_service_timestamp', 'service_name', 'timestamp'),
        Index('idx_audit_status_severity', 'status', 'severity'),
        Index('idx_audit_correlation', 'correlation_id', 'timestamp'),
        Index('idx_audit_session', 'session_id', 'timestamp'),
        Index('idx_audit_ip_timestamp', 'ip_address', 'timestamp'),
        Index('idx_audit_retention', 'retention_category', 'expires_at'),
    )


class SecurityEventModel(Base):
    """Security-specific audit events"""
    __tablename__ = 'security_events'

    # Primary key
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to main audit log
    audit_log_id = Column(UUID(as_uuid=True), ForeignKey('audit_logs.log_id'), nullable=False)
    
    # Security event details
    threat_type = Column(String(50))  # brute_force, injection, etc.
    threat_level = Column(String(20))  # low, medium, high, critical
    attack_vector = Column(String(100))
    
    # Detection information
    detection_method = Column(String(50))  # rule_based, ml_model, signature, etc.
    detection_confidence = Column(Numeric(5, 2))  # 0.00 to 100.00
    false_positive_probability = Column(Numeric(5, 2))
    
    # Response actions
    response_actions = Column(JSON)  # List of automated responses
    blocked = Column(Boolean, default=False)
    quarantined = Column(Boolean, default=False)
    
    # Impact assessment
    impact_score = Column(Numeric(5, 2))
    affected_systems = Column(JSON)
    data_classification = Column(String(50))
    
    # Investigation details
    investigation_status = Column(String(50), default='open')
    assigned_to = Column(String(100))
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)
    
    # Additional security context
    security_context = Column(JSON)
    ioc_indicators = Column(JSON)  # Indicators of Compromise
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    audit_log = relationship("AuditLogModel", backref="security_events")

    # Indexes
    __table_args__ = (
        Index('idx_security_threat_level', 'threat_level', 'created_at'),
        Index('idx_security_investigation', 'investigation_status', 'assigned_to'),
        Index('idx_security_impact', 'impact_score', 'created_at'),
    )


class ComplianceEventModel(Base):
    """Compliance-specific audit events"""
    __tablename__ = 'compliance_events'

    # Primary key
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to main audit log
    audit_log_id = Column(UUID(as_uuid=True), ForeignKey('audit_logs.log_id'), nullable=False)
    
    # Compliance framework
    framework = Column(String(50))  # PCI_DSS, SOX, GDPR, etc.
    control_id = Column(String(100))
    control_description = Column(Text)
    
    # Compliance status
    compliance_status = Column(String(50))  # compliant, non_compliant, warning
    violation_type = Column(String(100))
    violation_severity = Column(String(20))
    
    # Regulatory information
    regulation = Column(String(100))
    jurisdiction = Column(String(50))
    reporting_required = Column(Boolean, default=False)
    
    # Risk assessment
    risk_rating = Column(String(20))
    business_impact = Column(Text)
    mitigation_required = Column(Boolean, default=False)
    
    # Remediation
    remediation_plan = Column(Text)
    remediation_deadline = Column(DateTime)
    remediation_status = Column(String(50))
    remediation_notes = Column(Text)
    
    # Additional compliance data
    evidence_data = Column(JSON)
    attestation_required = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    audit_log = relationship("AuditLogModel", backref="compliance_events")

    # Indexes
    __table_args__ = (
        Index('idx_compliance_framework', 'framework', 'compliance_status'),
        Index('idx_compliance_violation', 'violation_type', 'violation_severity'),
        Index('idx_compliance_reporting', 'reporting_required', 'created_at'),
    )


class AuditTrailModel(Base):
    """Audit trail for linking related events"""
    __tablename__ = 'audit_trails'

    # Primary key
    trail_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Trail identification
    trail_name = Column(String(100), nullable=False)
    trail_type = Column(String(50))  # business_process, user_session, etc.
    
    # Related events
    primary_event_id = Column(UUID(as_uuid=True), ForeignKey('audit_logs.log_id'))
    related_events = Column(JSON)  # Array of related event IDs
    
    # Trail metadata
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_ms = Column(Integer)
    
    # Status and completion
    status = Column(String(50), default='active')
    completion_percentage = Column(Numeric(5, 2))
    
    # Context
    business_process = Column(String(100))
    workflow_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    primary_event = relationship("AuditLogModel", backref="audit_trails")

    # Indexes
    __table_args__ = (
        Index('idx_trail_type_status', 'trail_type', 'status'),
        Index('idx_trail_process', 'business_process', 'start_time'),
    )


class AuditConfigurationModel(Base):
    """Audit configuration and rules"""
    __tablename__ = 'audit_configurations'

    # Primary key
    config_id = Column(String(50), primary_key=True)
    
    # Configuration details
    config_name = Column(String(100), nullable=False)
    config_type = Column(String(50), nullable=False)  # event_rule, retention, alert, etc.
    description = Column(Text)
    
    # Rule configuration
    rule_conditions = Column(JSON)
    rule_actions = Column(JSON)
    
    # Scope
    applies_to_services = Column(JSON)  # List of service names
    applies_to_event_types = Column(JSON)  # List of event types
    applies_to_user_types = Column(JSON)  # List of user types
    
    # Settings
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    
    # Retention settings
    retention_days = Column(Integer)
    archive_after_days = Column(Integer)
    delete_after_days = Column(Integer)
    
    # Alert settings
    alert_thresholds = Column(JSON)
    notification_channels = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

    # Indexes
    __table_args__ = (
        Index('idx_config_type_active', 'config_type', 'is_active'),
        Index('idx_config_priority', 'priority'),
    )


class AuditMetricsModel(Base):
    """Aggregated audit metrics"""
    __tablename__ = 'audit_metrics'

    # Primary key
    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)  # hour, day, week, month
    
    # Grouping dimensions
    service_name = Column(String(50))
    event_type = Column(SQLEnum(AuditEventType))
    user_type = Column(SQLEnum(UserType))
    entity_type = Column(SQLEnum(EntityType))
    
    # Metrics
    total_events = Column(Integer, default=0)
    success_events = Column(Integer, default=0)
    failure_events = Column(Integer, default=0)
    security_events = Column(Integer, default=0)
    compliance_events = Column(Integer, default=0)
    
    # Performance metrics
    avg_duration_ms = Column(Numeric(10, 2))
    min_duration_ms = Column(Integer)
    max_duration_ms = Column(Integer)
    
    # Risk metrics
    avg_risk_score = Column(Numeric(5, 2))
    high_risk_events = Column(Integer, default=0)
    critical_events = Column(Integer, default=0)
    
    # User activity
    unique_users = Column(Integer, default=0)
    unique_sessions = Column(Integer, default=0)
    unique_ips = Column(Integer, default=0)
    
    # Error analysis
    top_errors = Column(JSON)
    error_rate_percentage = Column(Numeric(5, 2))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_metrics_period', 'period_start', 'period_end', 'period_type'),
        Index('idx_metrics_service', 'service_name', 'period_start'),
        Index('idx_metrics_event_type', 'event_type', 'period_start'),
        UniqueConstraint('period_start', 'period_end', 'period_type', 'service_name', 'event_type', 'user_type', 'entity_type'),
    )


class DataRetentionLogModel(Base):
    """Data retention and archival tracking"""
    __tablename__ = 'data_retention_logs'

    # Primary key
    retention_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Retention operation
    operation_type = Column(String(50), nullable=False)  # archive, delete, purge
    table_name = Column(String(100), nullable=False)
    
    # Criteria
    retention_criteria = Column(JSON)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    
    # Results
    records_processed = Column(Integer, default=0)
    records_archived = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    
    # Status
    status = Column(String(50), default='pending')
    error_message = Column(Text)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_minutes = Column(Integer)
    
    # Metadata
    initiated_by = Column(String(100))
    policy_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_retention_table_date', 'table_name', 'started_at'),
        Index('idx_retention_status', 'status', 'started_at'),
    )


# Database utilities
class DatabaseManager:
    """Database session and connection management"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()


# Export all models and utilities
__all__ = [
    'Base',
    'AuditLogModel',
    'SecurityEventModel',
    'ComplianceEventModel',
    'AuditTrailModel',
    'AuditConfigurationModel',
    'AuditMetricsModel',
    'DataRetentionLogModel',
    'AuditEventType',
    'AuditSeverity',
    'AuditStatus',
    'UserType',
    'EntityType',
    'DatabaseManager'
]
