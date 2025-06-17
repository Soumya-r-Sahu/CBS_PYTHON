"""
Event System Framework
Shared event handling utilities for all services
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types for the banking system"""
    
    # Customer Events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    CUSTOMER_KYC_COMPLETED = "customer.kyc.completed"
    CUSTOMER_KYC_FAILED = "customer.kyc.failed"
    
    # Account Events
    ACCOUNT_CREATED = "account.created"
    ACCOUNT_UPDATED = "account.updated"
    ACCOUNT_CLOSED = "account.closed"
    ACCOUNT_FROZEN = "account.frozen"
    ACCOUNT_UNFROZEN = "account.unfrozen"
    
    # Transaction Events
    TRANSACTION_INITIATED = "transaction.initiated"
    TRANSACTION_COMPLETED = "transaction.completed"
    TRANSACTION_FAILED = "transaction.failed"
    TRANSACTION_REVERSED = "transaction.reversed"
    
    # Payment Events
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # Loan Events
    LOAN_APPLICATION_SUBMITTED = "loan.application.submitted"
    LOAN_APPLICATION_APPROVED = "loan.application.approved"
    LOAN_APPLICATION_REJECTED = "loan.application.rejected"
    LOAN_DISBURSED = "loan.disbursed"
    LOAN_PAYMENT_RECEIVED = "loan.payment.received"
    LOAN_PAYMENT_OVERDUE = "loan.payment.overdue"
    
    # Notification Events
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"
    
    # Audit Events
    AUDIT_LOG_CREATED = "audit.log.created"
    
    # System Events
    SYSTEM_HEALTH_CHECK = "system.health.check"
    SYSTEM_ERROR = "system.error"


class EventPriority(str, Enum):
    """Event priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DomainEvent(BaseModel):
    """Base domain event model"""
    
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    aggregate_id: str
    aggregate_type: str
    version: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.MEDIUM
    source_service: str
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventHandler:
    """Base event handler interface"""
    
    async def handle(self, event: DomainEvent) -> None:
        """Handle the event"""
        raise NotImplementedError


class EventBus:
    """In-memory event bus for local event handling"""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
    
    def subscribe(self, event_type: EventType, handler: EventHandler):
        """Subscribe handler to specific event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def subscribe_all(self, handler: EventHandler):
        """Subscribe handler to all events"""
        self._global_handlers.append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler):
        """Unsubscribe handler from event type"""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    async def publish(self, event: DomainEvent):
        """Publish event to all subscribers"""
        logger.info(f"Publishing event: {event.event_type} for {event.aggregate_type}:{event.aggregate_id}")
        
        # Handle specific event type handlers
        handlers = self._handlers.get(event.event_type, [])
        
        # Add global handlers
        handlers.extend(self._global_handlers)
        
        # Execute all handlers
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._handle_event_safely(handler, event))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _handle_event_safely(self, handler: EventHandler, event: DomainEvent):
        """Handle event with error handling"""
        try:
            await handler.handle(event)
        except Exception as e:
            logger.error(f"Error handling event {event.event_type} with {handler.__class__.__name__}: {str(e)}")


class EventStore:
    """Simple in-memory event store for development"""
    
    def __init__(self):
        self._events: List[DomainEvent] = []
    
    async def save_event(self, event: DomainEvent):
        """Save event to store"""
        self._events.append(event)
        logger.debug(f"Saved event: {event.event_id}")
    
    async def get_events(
        self, 
        aggregate_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> List[DomainEvent]:
        """Get events with optional filtering"""
        events = self._events.copy()
        
        if aggregate_id:
            events = [e for e in events if e.aggregate_id == aggregate_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if from_timestamp:
            events = [e for e in events if e.timestamp >= from_timestamp]
        
        if to_timestamp:
            events = [e for e in events if e.timestamp <= to_timestamp]
        
        return sorted(events, key=lambda e: e.timestamp)
    
    async def get_aggregate_events(self, aggregate_id: str) -> List[DomainEvent]:
        """Get all events for a specific aggregate"""
        return await self.get_events(aggregate_id=aggregate_id)


class EventPublisher:
    """Event publisher for services"""
    
    def __init__(self, event_bus: EventBus, event_store: Optional[EventStore] = None):
        self.event_bus = event_bus
        self.event_store = event_store
    
    async def publish(self, event: DomainEvent):
        """Publish event to bus and optionally store it"""
        if self.event_store:
            await self.event_store.save_event(event)
        
        await self.event_bus.publish(event)


# Common Event Handlers

class LoggingEventHandler(EventHandler):
    """Handler that logs all events"""
    
    async def handle(self, event: DomainEvent):
        logger.info(f"Event: {event.event_type} | Aggregate: {event.aggregate_type}:{event.aggregate_id} | User: {event.user_id}")


class AuditEventHandler(EventHandler):
    """Handler that creates audit logs for events"""
    
    def __init__(self, audit_service):
        self.audit_service = audit_service
    
    async def handle(self, event: DomainEvent):
        # Create audit log entry
        audit_data = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "aggregate_id": event.aggregate_id,
            "aggregate_type": event.aggregate_type,
            "user_id": event.user_id,
            "timestamp": event.timestamp,
            "data": event.data
        }
        
        # This would typically call an audit service
        logger.info(f"Audit: {json.dumps(audit_data, default=str)}")


# Event Factory Functions

def create_customer_event(
    event_type: EventType,
    customer_id: str,
    user_id: str,
    source_service: str,
    data: Dict[str, Any],
    correlation_id: Optional[str] = None
) -> DomainEvent:
    """Create customer-related event"""
    return DomainEvent(
        event_type=event_type,
        aggregate_id=customer_id,
        aggregate_type="customer",
        source_service=source_service,
        user_id=user_id,
        correlation_id=correlation_id,
        data=data
    )


def create_account_event(
    event_type: EventType,
    account_id: str,
    user_id: str,
    source_service: str,
    data: Dict[str, Any],
    correlation_id: Optional[str] = None
) -> DomainEvent:
    """Create account-related event"""
    return DomainEvent(
        event_type=event_type,
        aggregate_id=account_id,
        aggregate_type="account",
        source_service=source_service,
        user_id=user_id,
        correlation_id=correlation_id,
        data=data
    )


def create_transaction_event(
    event_type: EventType,
    transaction_id: str,
    user_id: str,
    source_service: str,
    data: Dict[str, Any],
    priority: EventPriority = EventPriority.HIGH,
    correlation_id: Optional[str] = None
) -> DomainEvent:
    """Create transaction-related event"""
    return DomainEvent(
        event_type=event_type,
        aggregate_id=transaction_id,
        aggregate_type="transaction",
        source_service=source_service,
        user_id=user_id,
        priority=priority,
        correlation_id=correlation_id,
        data=data
    )


def create_payment_event(
    event_type: EventType,
    payment_id: str,
    user_id: str,
    source_service: str,
    data: Dict[str, Any],
    priority: EventPriority = EventPriority.HIGH,
    correlation_id: Optional[str] = None
) -> DomainEvent:
    """Create payment-related event"""
    return DomainEvent(
        event_type=event_type,
        aggregate_id=payment_id,
        aggregate_type="payment",
        source_service=source_service,
        user_id=user_id,
        priority=priority,
        correlation_id=correlation_id,
        data=data
    )
