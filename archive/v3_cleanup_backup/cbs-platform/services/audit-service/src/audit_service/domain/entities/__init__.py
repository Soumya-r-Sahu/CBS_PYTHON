"""
Audit Domain Entities
Business entities representing audit trail and compliance management
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
import json


class AuditEventType(str, Enum):
    """Audit event type enumeration"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_UPDATED = "account_updated"
    ACCOUNT_CLOSED = "account_closed"
    TRANSACTION_INITIATED = "transaction_initiated"
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_FAILED = "transaction_failed"
    PAYMENT_PROCESSED = "payment_processed"
    LOAN_APPLICATION = "loan_application"
    LOAN_APPROVED = "loan_approved"
    LOAN_DISBURSED = "loan_disbursed"
    DATA_EXPORT = "data_export"
    CONFIGURATION_CHANGED = "configuration_changed"
    SECURITY_VIOLATION = "security_violation"
    COMPLIANCE_CHECK = "compliance_check"
    REGULATORY_REPORT = "regulatory_report"


class AuditLevel(str, Enum):
    """Audit level enumeration"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ComplianceStatus(str, Enum):
    """Compliance status enumeration"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"
    REQUIRES_ACTION = "requires_action"
    EXEMPTED = "exempted"


class AuditSource(str, Enum):
    """Audit source enumeration"""
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    API = "api"
    BATCH_JOB = "batch_job"
    SYSTEM = "system"
    ADMIN_PANEL = "admin_panel"
    THIRD_PARTY = "third_party"


@dataclass
class UserContext:
    """User context information for audit"""
    user_id: str
    username: str
    role: str
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[str] = None
    
    def __post_init__(self):
        if not self.user_id:
            raise ValueError("User ID is required")
        if not self.username:
            raise ValueError("Username is required")


@dataclass
class SystemContext:
    """System context information for audit"""
    service_name: str
    version: str
    environment: str  # dev, test, prod
    hostname: str
    process_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.service_name:
            raise ValueError("Service name is required")


@dataclass
class BusinessContext:
    """Business context information for audit"""
    entity_type: str  # account, customer, transaction, loan
    entity_id: str
    entity_name: Optional[str] = None
    business_unit: Optional[str] = None
    product_type: Optional[str] = None
    channel: Optional[str] = None
    
    def __post_init__(self):
        if not self.entity_type:
            raise ValueError("Entity type is required")
        if not self.entity_id:
            raise ValueError("Entity ID is required")


@dataclass
class AuditEvent:
    """Audit event aggregate root"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.USER_LOGIN
    level: AuditLevel = AuditLevel.INFO
    source: AuditSource = AuditSource.SYSTEM
    
    # Context information
    user_context: Optional[UserContext] = None
    system_context: Optional[SystemContext] = None
    business_context: Optional[BusinessContext] = None
    
    # Event details
    description: str = ""
    action_performed: str = ""
    resource_accessed: Optional[str] = None
    operation_type: str = ""  # CREATE, READ, UPDATE, DELETE
    
    # Data changes
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    changed_fields: List[str] = field(default_factory=list)
    
    # Request/Response
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    response_code: Optional[str] = None
    
    # Outcome
    success: bool = True
    error_message: Optional[str] = None
    risk_score: Optional[int] = None
    
    # Timestamps
    event_timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[int] = None
    
    # Compliance and regulatory
    compliance_rules_applied: List[str] = field(default_factory=list)
    regulatory_flags: List[str] = field(default_factory=list)
    retention_period_days: int = 2555  # 7 years default
    
    # System fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    indexed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    
    def __post_init__(self):
        if not self.description:
            raise ValueError("Event description is required")
        if not self.action_performed:
            raise ValueError("Action performed is required")
    
    def add_compliance_rule(self, rule_name: str):
        """Add compliance rule that was applied"""
        if rule_name not in self.compliance_rules_applied:
            self.compliance_rules_applied.append(rule_name)
    
    def add_regulatory_flag(self, flag: str):
        """Add regulatory flag"""
        if flag not in self.regulatory_flags:
            self.regulatory_flags.append(flag)
    
    def calculate_data_changes(self, before: Dict[str, Any], after: Dict[str, Any]):
        """Calculate what fields changed between before and after states"""
        self.before_state = before.copy() if before else {}
        self.after_state = after.copy() if after else {}
        self.changed_fields = []
        
        # Find changed fields
        all_fields = set(before.keys()) | set(after.keys()) if before and after else set()
        
        for field in all_fields:
            before_value = before.get(field) if before else None
            after_value = after.get(field) if after else None
            
            if before_value != after_value:
                self.changed_fields.append(field)
    
    def mask_sensitive_data(self, sensitive_fields: List[str]):
        """Mask sensitive data in audit event"""
        for field in sensitive_fields:
            if self.before_state and field in self.before_state:
                self.before_state[field] = "***MASKED***"
            if self.after_state and field in self.after_state:
                self.after_state[field] = "***MASKED***"
            if self.request_data and field in self.request_data:
                self.request_data[field] = "***MASKED***"
            if self.response_data and field in self.response_data:
                self.response_data[field] = "***MASKED***"
    
    def is_high_risk(self) -> bool:
        """Check if event is high risk"""
        return (
            self.risk_score and self.risk_score >= 80 or
            self.level in [AuditLevel.ERROR, AuditLevel.CRITICAL] or
            len(self.regulatory_flags) > 0 or
            self.event_type in [
                AuditEventType.SECURITY_VIOLATION,
                AuditEventType.DATA_EXPORT,
                AuditEventType.CONFIGURATION_CHANGED
            ]
        )
    
    def should_alert(self) -> bool:
        """Check if event should trigger alerts"""
        return (
            self.is_high_risk() or
            not self.success or
            self.level == AuditLevel.CRITICAL
        )
    
    def get_retention_expiry_date(self) -> datetime:
        """Get when this audit record should be archived/deleted"""
        return datetime(
            self.event_timestamp.year + (self.retention_period_days // 365),
            self.event_timestamp.month,
            self.event_timestamp.day
        )
    
    def to_json(self) -> str:
        """Convert audit event to JSON for storage"""
        return json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "level": self.level.value,
            "source": self.source.value,
            "user_context": self.user_context.__dict__ if self.user_context else None,
            "system_context": self.system_context.__dict__ if self.system_context else None,
            "business_context": self.business_context.__dict__ if self.business_context else None,
            "description": self.description,
            "action_performed": self.action_performed,
            "resource_accessed": self.resource_accessed,
            "operation_type": self.operation_type,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "changed_fields": self.changed_fields,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "response_code": self.response_code,
            "success": self.success,
            "error_message": self.error_message,
            "risk_score": self.risk_score,
            "event_timestamp": self.event_timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "compliance_rules_applied": self.compliance_rules_applied,
            "regulatory_flags": self.regulatory_flags,
            "retention_period_days": self.retention_period_days,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "version": self.version
        }, default=str)


@dataclass
class ComplianceRule:
    """Compliance rule definition"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: str = ""  # AML, KYC, PCI_DSS, SOX, GDPR, etc.
    severity: AuditLevel = AuditLevel.WARNING
    
    # Rule conditions
    event_types: List[AuditEventType] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Actions
    auto_alert: bool = False
    auto_block: bool = False
    requires_approval: bool = False
    escalation_level: Optional[str] = None
    
    # Configuration
    is_active: bool = True
    effective_from: datetime = field(default_factory=datetime.utcnow)
    effective_to: Optional[datetime] = None
    
    # System fields
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Rule name is required")
        if not self.description:
            raise ValueError("Rule description is required")
    
    def is_applicable(self, event: AuditEvent) -> bool:
        """Check if rule is applicable to the audit event"""
        if not self.is_active:
            return False
        
        if datetime.utcnow() < self.effective_from:
            return False
        
        if self.effective_to and datetime.utcnow() > self.effective_to:
            return False
        
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        return True
    
    def evaluate(self, event: AuditEvent) -> bool:
        """Evaluate if the event violates this compliance rule"""
        if not self.is_applicable(event):
            return False
        
        # Simple condition evaluation (in production, use rule engine)
        for condition_field, expected_value in self.conditions.items():
            event_value = getattr(event, condition_field, None)
            if event_value != expected_value:
                return False
        
        return True


@dataclass
class ComplianceViolation:
    """Compliance violation record"""
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    rule_name: str = ""
    event_id: str = ""
    
    # Violation details
    violation_type: str = ""
    severity: AuditLevel = AuditLevel.WARNING
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    # Status and resolution
    status: ComplianceStatus = ComplianceStatus.UNDER_REVIEW
    assigned_to: Optional[str] = None
    resolution_notes: str = ""
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    # Impact assessment
    risk_level: str = "medium"  # low, medium, high, critical
    business_impact: str = ""
    regulatory_impact: str = ""
    
    # Timestamps
    detected_at: datetime = field(default_factory=datetime.utcnow)
    escalated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # System fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    
    def __post_init__(self):
        if not self.rule_id:
            raise ValueError("Rule ID is required")
        if not self.event_id:
            raise ValueError("Event ID is required")
    
    def assign_to(self, assignee: str):
        """Assign violation to user for resolution"""
        self.assigned_to = assignee
        self.status = ComplianceStatus.UNDER_REVIEW
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def resolve(self, resolved_by: str, resolution_notes: str):
        """Resolve the compliance violation"""
        self.status = ComplianceStatus.COMPLIANT
        self.resolved_by = resolved_by
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = resolution_notes
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def escalate(self, escalation_reason: str):
        """Escalate the violation"""
        self.escalated_at = datetime.utcnow()
        self.metadata["escalation_reason"] = escalation_reason
        self.metadata["escalated_at"] = self.escalated_at.isoformat()
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def is_overdue(self) -> bool:
        """Check if violation resolution is overdue"""
        return self.due_date and datetime.utcnow() > self.due_date


@dataclass
class AuditTrail:
    """Audit trail for tracking changes to entities"""
    trail_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str = ""
    entity_id: str = ""
    entity_name: Optional[str] = None
    
    # Trail configuration
    is_active: bool = True
    track_reads: bool = False
    track_creates: bool = True
    track_updates: bool = True
    track_deletes: bool = True
    
    # Audit events in this trail
    events: List[str] = field(default_factory=list)  # Event IDs
    
    # Summary statistics
    total_events: int = 0
    last_activity: Optional[datetime] = None
    created_by_users: List[str] = field(default_factory=list)
    
    # System fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.entity_type:
            raise ValueError("Entity type is required")
        if not self.entity_id:
            raise ValueError("Entity ID is required")
    
    def add_event(self, event_id: str, user_id: str):
        """Add event to audit trail"""
        if event_id not in self.events:
            self.events.append(event_id)
            self.total_events += 1
            self.last_activity = datetime.utcnow()
            
            if user_id not in self.created_by_users:
                self.created_by_users.append(user_id)
            
            self.updated_at = datetime.utcnow()
    
    def get_activity_summary(self) -> Dict[str, Any]:
        """Get activity summary for this entity"""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "total_events": self.total_events,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "unique_users": len(self.created_by_users),
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }


@dataclass
class RegulatoryReport:
    """Regulatory reporting entity"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str = ""  # AML_SAR, KYC_REPORT, TRANSACTION_REPORT, etc.
    report_name: str = ""
    period_from: datetime = field(default_factory=datetime.utcnow)
    period_to: datetime = field(default_factory=datetime.utcnow)
    
    # Report content
    data_criteria: Dict[str, Any] = field(default_factory=dict)
    report_data: Dict[str, Any] = field(default_factory=dict)
    summary_statistics: Dict[str, Any] = field(default_factory=dict)
    
    # Status and approval
    status: str = "draft"  # draft, pending_review, approved, submitted, rejected
    generated_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    submitted_by: Optional[str] = None
    
    # Regulatory details
    regulatory_body: str = ""
    submission_deadline: Optional[datetime] = None
    submission_reference: Optional[str] = None
    
    # Timestamps
    generated_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    
    # System fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    
    def __post_init__(self):
        if not self.report_type:
            raise ValueError("Report type is required")
        if not self.report_name:
            raise ValueError("Report name is required")
    
    def submit_for_review(self, reviewer: str):
        """Submit report for review"""
        if self.status != "draft":
            raise ValueError("Can only submit draft reports for review")
        
        self.status = "pending_review"
        self.reviewed_by = reviewer
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def approve(self, approver: str):
        """Approve the report"""
        if self.status != "pending_review":
            raise ValueError("Can only approve reports under review")
        
        self.status = "approved"
        self.approved_by = approver
        self.approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def submit_to_regulator(self, submitter: str, reference: str):
        """Submit report to regulatory body"""
        if self.status != "approved":
            raise ValueError("Can only submit approved reports")
        
        self.status = "submitted"
        self.submitted_by = submitter
        self.submitted_at = datetime.utcnow()
        self.submission_reference = reference
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def is_overdue(self) -> bool:
        """Check if report submission is overdue"""
        return (
            self.submission_deadline and 
            datetime.utcnow() > self.submission_deadline and 
            self.status != "submitted"
        )
