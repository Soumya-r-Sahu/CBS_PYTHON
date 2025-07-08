"""
Notification Domain Entities

Core business entities for notification management in CBS platform.
Implements comprehensive notification system with multiple channels.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from platform.shared.events import DomainEvent


class NotificationType(Enum):
    """Types of notifications."""
    TRANSACTIONAL = "TRANSACTIONAL"
    PROMOTIONAL = "PROMOTIONAL"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    REGULATORY = "REGULATORY"
    MARKETING = "MARKETING"
    REMINDER = "REMINDER"
    ALERT = "ALERT"


class NotificationChannel(Enum):
    """Notification delivery channels."""
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    IN_APP = "IN_APP"
    WHATSAPP = "WHATSAPP"
    VOICE = "VOICE"
    POSTAL = "POSTAL"


class NotificationStatus(Enum):
    """Notification processing status."""
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TemplateType(Enum):
    """Template types for notifications."""
    PLAIN_TEXT = "PLAIN_TEXT"
    HTML = "HTML"
    RICH_TEXT = "RICH_TEXT"
    JSON = "JSON"


@dataclass
class NotificationRecipient:
    """Notification recipient information."""
    customer_id: UUID
    channel: NotificationChannel
    address: str  # Email, phone number, device token, etc.
    preferences: Dict[str, Any] = field(default_factory=dict)
    is_verified: bool = True
    
    def __post_init__(self):
        if not self.address:
            raise ValueError("Recipient address is required")


@dataclass
class NotificationContent:
    """Notification content with template support."""
    subject: Optional[str] = None
    body: str = ""
    template_id: Optional[str] = None
    template_variables: Dict[str, Any] = field(default_factory=dict)
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.body and not self.template_id:
            raise ValueError("Either body or template_id is required")


@dataclass
class DeliverySettings:
    """Notification delivery settings."""
    retry_count: int = 3
    retry_delay_seconds: int = 60
    expiry_hours: int = 24
    batch_size: int = 100
    rate_limit_per_minute: int = 1000
    delivery_window_start: Optional[str] = None  # "09:00"
    delivery_window_end: Optional[str] = None    # "21:00"
    timezone: str = "UTC"


class NotificationTemplate:
    """
    Notification template for reusable content.
    
    Supports variable substitution and multi-channel templates.
    """
    
    def __init__(
        self,
        template_id: Optional[UUID] = None,
        name: str = "",
        type: TemplateType = TemplateType.PLAIN_TEXT,
        category: str = ""
    ):
        self.template_id = template_id or uuid4()
        self.name = name
        self.type = type
        self.category = category
        self.subject_template: Optional[str] = None
        self.body_template: str = ""
        self.channel_specific: Dict[NotificationChannel, Dict[str, str]] = {}
        self.variables: List[str] = []
        self.is_active = True
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version = 1
    
    def add_channel_template(
        self, 
        channel: NotificationChannel, 
        subject: Optional[str], 
        body: str
    ) -> None:
        """Add channel-specific template."""
        self.channel_specific[channel] = {
            "subject": subject,
            "body": body
        }
        self.updated_at = datetime.utcnow()
    
    def render(
        self, 
        channel: NotificationChannel, 
        variables: Dict[str, Any]
    ) -> NotificationContent:
        """Render template with variables for specific channel."""
        # Get channel-specific template or fallback to default
        if channel in self.channel_specific:
            template_data = self.channel_specific[channel]
            subject_template = template_data.get("subject")
            body_template = template_data["body"]
        else:
            subject_template = self.subject_template
            body_template = self.body_template
        
        # Simple variable substitution (in production, use proper template engine)
        subject = None
        if subject_template:
            subject = subject_template.format(**variables)
        
        body = body_template.format(**variables)
        
        return NotificationContent(
            subject=subject,
            body=body,
            template_id=str(self.template_id),
            template_variables=variables
        )


class Notification:
    """
    Notification aggregate root.
    
    Represents a notification to be sent through various channels
    with tracking and delivery confirmation.
    """
    
    def __init__(
        self,
        notification_id: Optional[UUID] = None,
        type: NotificationType = NotificationType.TRANSACTIONAL,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ):
        self.notification_id = notification_id or uuid4()
        self.type = type
        self.priority = priority
        self.status = NotificationStatus.CREATED
        self.recipients: List[NotificationRecipient] = []
        self.content = NotificationContent()
        self.delivery_settings = DeliverySettings()
        self.scheduled_at: Optional[datetime] = None
        self.sent_at: Optional[datetime] = None
        self.delivered_at: Optional[datetime] = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.created_by: Optional[UUID] = None
        self.correlation_id: Optional[str] = None  # For tracking related notifications
        self.events: List[DomainEvent] = []
        self.delivery_attempts: List['DeliveryAttempt'] = []
        self.tags: List[str] = []
        self.reference_id: Optional[str] = None  # External reference
    
    def add_recipient(self, recipient: NotificationRecipient) -> None:
        """Add a recipient to the notification."""
        if recipient not in self.recipients:
            self.recipients.append(recipient)
            self.updated_at = datetime.utcnow()
    
    def set_content(self, content: NotificationContent) -> None:
        """Set notification content."""
        self.content = content
        self.updated_at = datetime.utcnow()
    
    def schedule(self, scheduled_at: datetime) -> None:
        """Schedule notification for later delivery."""
        if scheduled_at <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        
        self.scheduled_at = scheduled_at
        self.status = NotificationStatus.QUEUED
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = NotificationScheduled(
            notification_id=self.notification_id,
            scheduled_at=scheduled_at,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def queue(self) -> None:
        """Queue notification for immediate processing."""
        if self.status != NotificationStatus.CREATED:
            raise ValueError("Can only queue created notifications")
        
        if not self.recipients:
            raise ValueError("Cannot queue notification without recipients")
        
        self.status = NotificationStatus.QUEUED
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = NotificationQueued(
            notification_id=self.notification_id,
            recipient_count=len(self.recipients),
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def start_processing(self) -> None:
        """Mark notification as being processed."""
        if self.status != NotificationStatus.QUEUED:
            raise ValueError("Can only process queued notifications")
        
        self.status = NotificationStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_sent(self) -> None:
        """Mark notification as sent."""
        if self.status != NotificationStatus.PROCESSING:
            raise ValueError("Can only mark processing notifications as sent")
        
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = NotificationSent(
            notification_id=self.notification_id,
            sent_at=self.sent_at,
            recipient_count=len(self.recipients),
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def mark_delivered(self, delivery_confirmation: Dict[str, Any] = None) -> None:
        """Mark notification as delivered."""
        if self.status != NotificationStatus.SENT:
            raise ValueError("Can only mark sent notifications as delivered")
        
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = NotificationDelivered(
            notification_id=self.notification_id,
            delivered_at=self.delivered_at,
            confirmation=delivery_confirmation or {},
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def mark_failed(self, error_message: str, is_retryable: bool = True) -> None:
        """Mark notification as failed."""
        self.status = NotificationStatus.FAILED
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = NotificationFailed(
            notification_id=self.notification_id,
            error_message=error_message,
            is_retryable=is_retryable,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def cancel(self, reason: str) -> None:
        """Cancel the notification."""
        if self.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED]:
            raise ValueError("Cannot cancel sent or delivered notifications")
        
        self.status = NotificationStatus.CANCELLED
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = NotificationCancelled(
            notification_id=self.notification_id,
            reason=reason,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def add_delivery_attempt(self, attempt: 'DeliveryAttempt') -> None:
        """Add a delivery attempt record."""
        self.delivery_attempts.append(attempt)
        self.updated_at = datetime.utcnow()
    
    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        if self.status != NotificationStatus.FAILED:
            return False
        
        return len(self.delivery_attempts) < self.delivery_settings.retry_count
    
    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if not self.created_at:
            return False
        
        expiry_time = self.created_at + datetime.timedelta(
            hours=self.delivery_settings.expiry_hours
        )
        return datetime.utcnow() > expiry_time


@dataclass
class DeliveryAttempt:
    """Record of a notification delivery attempt."""
    attempt_id: UUID = field(default_factory=uuid4)
    attempted_at: datetime = field(default_factory=datetime.utcnow)
    channel: NotificationChannel = NotificationChannel.EMAIL
    recipient_address: str = ""
    success: bool = False
    error_message: Optional[str] = None
    response_data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[int] = None


class NotificationPreference:
    """
    Customer notification preferences.
    
    Manages customer preferences for different types
    of notifications and channels.
    """
    
    def __init__(self, customer_id: UUID):
        self.customer_id = customer_id
        self.preferences: Dict[NotificationType, Dict[NotificationChannel, bool]] = {}
        self.global_opt_out = False
        self.quiet_hours_start: Optional[str] = None  # "22:00"
        self.quiet_hours_end: Optional[str] = None    # "08:00"
        self.timezone = "UTC"
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def set_preference(
        self, 
        notification_type: NotificationType, 
        channel: NotificationChannel, 
        enabled: bool
    ) -> None:
        """Set preference for notification type and channel."""
        if notification_type not in self.preferences:
            self.preferences[notification_type] = {}
        
        self.preferences[notification_type][channel] = enabled
        self.updated_at = datetime.utcnow()
    
    def is_enabled(
        self, 
        notification_type: NotificationType, 
        channel: NotificationChannel
    ) -> bool:
        """Check if notification type and channel is enabled."""
        if self.global_opt_out:
            return False
        
        return self.preferences.get(notification_type, {}).get(channel, True)
    
    def set_quiet_hours(self, start_time: str, end_time: str) -> None:
        """Set quiet hours when notifications should not be sent."""
        self.quiet_hours_start = start_time
        self.quiet_hours_end = end_time
        self.updated_at = datetime.utcnow()
    
    def is_in_quiet_hours(self, check_time: datetime = None) -> bool:
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        check_time = check_time or datetime.utcnow()
        current_time = check_time.strftime("%H:%M")
        
        return self.quiet_hours_start <= current_time <= self.quiet_hours_end


# Domain Events
@dataclass(frozen=True)
class NotificationScheduled(DomainEvent):
    """Event emitted when notification is scheduled."""
    notification_id: UUID
    scheduled_at: datetime


@dataclass(frozen=True)
class NotificationQueued(DomainEvent):
    """Event emitted when notification is queued."""
    notification_id: UUID
    recipient_count: int


@dataclass(frozen=True)
class NotificationSent(DomainEvent):
    """Event emitted when notification is sent."""
    notification_id: UUID
    sent_at: datetime
    recipient_count: int


@dataclass(frozen=True)
class NotificationDelivered(DomainEvent):
    """Event emitted when notification is delivered."""
    notification_id: UUID
    delivered_at: datetime
    confirmation: Dict[str, Any]


@dataclass(frozen=True)
class NotificationFailed(DomainEvent):
    """Event emitted when notification fails."""
    notification_id: UUID
    error_message: str
    is_retryable: bool


@dataclass(frozen=True)
class NotificationCancelled(DomainEvent):
    """Event emitted when notification is cancelled."""
    notification_id: UUID
    reason: str


# Export public interface
__all__ = [
    "Notification",
    "NotificationTemplate",
    "NotificationPreference",
    "NotificationType",
    "NotificationChannel",
    "NotificationStatus",
    "NotificationPriority",
    "TemplateType",
    "NotificationRecipient",
    "NotificationContent",
    "DeliverySettings",
    "DeliveryAttempt",
    "NotificationScheduled",
    "NotificationQueued", 
    "NotificationSent",
    "NotificationDelivered",
    "NotificationFailed",
    "NotificationCancelled"
]
