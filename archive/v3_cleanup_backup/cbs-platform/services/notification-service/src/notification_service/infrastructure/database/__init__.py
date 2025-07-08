"""
Notification Service Database Models

This module contains all database models for the notification service,
implementing comprehensive notification management functionality.
"""

import enum
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, 
    JSON, Index, ForeignKey, Enum as SQLEnum, 
    Numeric, create_engine, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID

# Base class for all models
Base = declarative_base()


class NotificationType(enum.Enum):
    """Notification type enumeration"""
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationStatus(enum.Enum):
    """Notification status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class NotificationPriority(enum.Enum):
    """Notification priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationCategory(enum.Enum):
    """Notification category enumeration"""
    TRANSACTION = "transaction"
    ACCOUNT = "account"
    SECURITY = "security"
    PAYMENT = "payment"
    LOAN = "loan"
    SYSTEM = "system"
    MARKETING = "marketing"
    ALERT = "alert"


class NotificationModel(Base):
    """Notification database model"""
    __tablename__ = 'notifications'

    # Primary key
    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core notification details
    message_id = Column(String(100), unique=True, nullable=False, index=True)
    recipient_id = Column(String(50), nullable=False, index=True)
    recipient_type = Column(String(20), nullable=False)  # customer, admin, system
    
    # Notification metadata
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    category = Column(SQLEnum(NotificationCategory), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Content
    title = Column(String(200))
    message = Column(Text, nullable=False)
    html_content = Column(Text)
    template_id = Column(String(50))
    template_data = Column(JSON)
    
    # Delivery details
    channel_config = Column(JSON)  # SMS: phone, Email: email, Push: device_token
    delivery_address = Column(String(255))  # actual phone/email/device_token
    
    # Tracking
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_attempt_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    
    # Metadata
    source_service = Column(String(50))
    correlation_id = Column(String(100), index=True)
    reference_type = Column(String(50))  # transaction, account, loan, etc.
    reference_id = Column(String(100))
    metadata = Column(JSON)
    
    # Scheduling
    scheduled_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    templates = relationship("NotificationTemplateModel", back_populates="notifications")
    delivery_logs = relationship("NotificationDeliveryLogModel", back_populates="notification", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_notification_recipient', 'recipient_id', 'recipient_type'),
        Index('idx_notification_status_priority', 'status', 'priority'),
        Index('idx_notification_category_type', 'category', 'notification_type'),
        Index('idx_notification_reference', 'reference_type', 'reference_id'),
        Index('idx_notification_scheduled', 'scheduled_at', 'status'),
        Index('idx_notification_created', 'created_at'),
    )


class NotificationTemplateModel(Base):
    """Notification template database model"""
    __tablename__ = 'notification_templates'

    # Primary key
    template_id = Column(String(50), primary_key=True)
    
    # Template details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(SQLEnum(NotificationCategory), nullable=False)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    
    # Content templates
    title_template = Column(String(200))
    message_template = Column(Text, nullable=False)
    html_template = Column(Text)
    
    # Configuration
    default_priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    max_attempts = Column(Integer, default=3)
    retry_delay_minutes = Column(Integer, default=5)
    expiry_hours = Column(Integer, default=24)
    
    # Metadata
    variables = Column(JSON)  # List of template variables
    validation_schema = Column(JSON)
    
    # Status
    is_active = Column(Boolean, default=True)
    version = Column(String(10), default="1.0")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50))
    
    # Relationships
    notifications = relationship("NotificationModel", back_populates="templates")

    # Indexes
    __table_args__ = (
        Index('idx_template_category_type', 'category', 'notification_type'),
        Index('idx_template_active', 'is_active'),
    )


class NotificationDeliveryLogModel(Base):
    """Notification delivery log database model"""
    __tablename__ = 'notification_delivery_logs'

    # Primary key
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    notification_id = Column(UUID(as_uuid=True), ForeignKey('notifications.notification_id'), nullable=False)
    
    # Delivery attempt details
    attempt_number = Column(Integer, nullable=False)
    delivery_status = Column(SQLEnum(NotificationStatus), nullable=False)
    
    # Gateway/Provider details
    provider_name = Column(String(50))
    provider_message_id = Column(String(100))
    provider_response = Column(JSON)
    
    # Delivery metrics
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    response_time_ms = Column(Integer)
    
    # Error handling
    error_code = Column(String(20))
    error_message = Column(Text)
    retry_after = Column(DateTime)
    
    # Cost tracking
    delivery_cost = Column(Numeric(10, 4))
    currency = Column(String(3), default='INR')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    notification = relationship("NotificationModel", back_populates="delivery_logs")

    # Indexes
    __table_args__ = (
        Index('idx_delivery_log_notification', 'notification_id'),
        Index('idx_delivery_log_status', 'delivery_status'),
        Index('idx_delivery_log_provider', 'provider_name'),
        Index('idx_delivery_log_created', 'created_at'),
    )


class NotificationPreferenceModel(Base):
    """User notification preferences database model"""
    __tablename__ = 'notification_preferences'

    # Primary key
    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User identification
    user_id = Column(String(50), nullable=False, index=True)
    user_type = Column(String(20), nullable=False)  # customer, admin
    
    # Channel preferences
    sms_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    
    # Category preferences
    transaction_notifications = Column(Boolean, default=True)
    account_notifications = Column(Boolean, default=True)
    security_notifications = Column(Boolean, default=True)
    payment_notifications = Column(Boolean, default=True)
    loan_notifications = Column(Boolean, default=True)
    marketing_notifications = Column(Boolean, default=False)
    system_notifications = Column(Boolean, default=True)
    
    # Contact details
    phone_number = Column(String(15))
    email_address = Column(String(100))
    device_tokens = Column(JSON)  # List of device tokens for push notifications
    
    # Delivery preferences
    preferred_language = Column(String(5), default='en')
    timezone = Column(String(50), default='Asia/Kolkata')
    quiet_hours_start = Column(String(5))  # Format: HH:MM
    quiet_hours_end = Column(String(5))    # Format: HH:MM
    
    # Frequency limits
    max_sms_per_day = Column(Integer, default=10)
    max_email_per_day = Column(Integer, default=20)
    max_push_per_day = Column(Integer, default=50)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_preference_user', 'user_id', 'user_type'),
        Index('idx_preference_phone', 'phone_number'),
        Index('idx_preference_email', 'email_address'),
    )


class NotificationChannelModel(Base):
    """Notification channel configuration database model"""
    __tablename__ = 'notification_channels'

    # Primary key
    channel_id = Column(String(50), primary_key=True)
    
    # Channel details
    channel_name = Column(String(100), nullable=False)
    channel_type = Column(SQLEnum(NotificationType), nullable=False)
    provider_name = Column(String(50), nullable=False)
    
    # Configuration
    configuration = Column(JSON, nullable=False)  # Provider-specific config
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    rate_limit_per_day = Column(Integer, default=10000)
    
    # Status and metrics
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    priority_order = Column(Integer, default=1)
    
    # Health monitoring
    last_health_check = Column(DateTime)
    health_status = Column(String(20), default='unknown')
    error_rate_percentage = Column(Numeric(5, 2), default=0.0)
    
    # Costs
    cost_per_message = Column(Numeric(10, 4))
    currency = Column(String(3), default='INR')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_channel_type_active', 'channel_type', 'is_active'),
        Index('idx_channel_default', 'is_default'),
        Index('idx_channel_priority', 'priority_order'),
    )


class NotificationQueueModel(Base):
    """Notification queue for bulk processing"""
    __tablename__ = 'notification_queue'

    # Primary key
    queue_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Queue details
    batch_id = Column(String(100), index=True)
    notification_id = Column(UUID(as_uuid=True), ForeignKey('notifications.notification_id'))
    
    # Processing details
    queue_status = Column(String(20), default='queued', index=True)
    priority = Column(Integer, default=1)
    retry_count = Column(Integer, default=0)
    
    # Scheduling
    scheduled_for = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Worker assignment
    worker_id = Column(String(50))
    locked_at = Column(DateTime)
    lock_expires_at = Column(DateTime)
    
    # Error tracking
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_queue_status_priority', 'queue_status', 'priority'),
        Index('idx_queue_scheduled', 'scheduled_for'),
        Index('idx_queue_batch', 'batch_id'),
        Index('idx_queue_worker', 'worker_id'),
    )


class NotificationStatisticsModel(Base):
    """Daily notification statistics"""
    __tablename__ = 'notification_statistics'

    # Primary key
    stat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    date = Column(DateTime, nullable=False, index=True)
    hour = Column(Integer)  # Optional for hourly stats
    
    # Grouping dimensions
    notification_type = Column(SQLEnum(NotificationType))
    category = Column(SQLEnum(NotificationCategory))
    channel_id = Column(String(50))
    
    # Metrics
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    total_pending = Column(Integer, default=0)
    
    # Performance metrics
    avg_delivery_time_ms = Column(Integer)
    min_delivery_time_ms = Column(Integer)
    max_delivery_time_ms = Column(Integer)
    
    # Cost metrics
    total_cost = Column(Numeric(12, 4), default=0.0)
    currency = Column(String(3), default='INR')
    
    # Error analysis
    error_rate_percentage = Column(Numeric(5, 2), default=0.0)
    common_errors = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_stats_date_type', 'date', 'notification_type'),
        Index('idx_stats_category', 'category'),
        Index('idx_stats_channel', 'channel_id'),
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
    'NotificationModel',
    'NotificationTemplateModel',
    'NotificationDeliveryLogModel',
    'NotificationPreferenceModel',
    'NotificationChannelModel',
    'NotificationQueueModel',
    'NotificationStatisticsModel',
    'NotificationType',
    'NotificationStatus',
    'NotificationPriority',
    'NotificationCategory',
    'DatabaseManager'
]
