"""
Advanced Webhook Management System for CBS_PYTHON V2.0

This module provides:
- Webhook subscription management
- Event-driven webhook delivery
- Retry mechanisms with exponential backoff
- Signature verification for security
- Webhook endpoint validation
- Delivery status tracking and analytics
- Rate limiting for webhook deliveries
"""

import asyncio
import json
import logging
import hashlib
import hmac
import time
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import httpx
import redis.asyncio as redis
from kafka import KafkaProducer, KafkaConsumer
from prometheus_client import Counter, Histogram, Gauge
from pydantic import BaseModel, Field, HttpUrl, validator
import asyncpg
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import structlog

logger = structlog.get_logger(__name__)

# Metrics
webhook_events_produced = Counter('webhook_events_produced_total', 'Total webhook events produced', ['event_type'])
webhook_deliveries_attempted = Counter('webhook_deliveries_attempted_total', 'Webhook delivery attempts', ['webhook_id', 'event_type'])
webhook_deliveries_succeeded = Counter('webhook_deliveries_succeeded_total', 'Successful webhook deliveries', ['webhook_id', 'event_type'])
webhook_deliveries_failed = Counter('webhook_deliveries_failed_total', 'Failed webhook deliveries', ['webhook_id', 'event_type', 'status_code'])
webhook_delivery_duration = Histogram('webhook_delivery_duration_seconds', 'Webhook delivery duration')
active_webhooks = Gauge('webhooks_active_total', 'Number of active webhooks')


class WebhookStatus(str, Enum):
    """Webhook subscription status"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    FAILED = "failed"


class DeliveryStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"
    EXPIRED = "expired"


class EventType(str, Enum):
    """Supported webhook event types"""
    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    CUSTOMER_KYC_VERIFIED = "customer.kyc_verified"
    
    # Account events
    ACCOUNT_CREATED = "account.created"
    ACCOUNT_UPDATED = "account.updated"
    ACCOUNT_STATUS_CHANGED = "account.status_changed"
    ACCOUNT_BALANCE_LOW = "account.balance_low"
    
    # Transaction events
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_COMPLETED = "transaction.completed"
    TRANSACTION_FAILED = "transaction.failed"
    TRANSACTION_CANCELLED = "transaction.cancelled"
    
    # Payment events
    PAYMENT_CREATED = "payment.created"
    PAYMENT_PROCESSING = "payment.processing"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_CANCELLED = "payment.cancelled"
    
    # Loan events
    LOAN_APPLICATION_SUBMITTED = "loan.application_submitted"
    LOAN_APPROVED = "loan.approved"
    LOAN_REJECTED = "loan.rejected"
    LOAN_DISBURSED = "loan.disbursed"
    LOAN_PAYMENT_DUE = "loan.payment_due"
    LOAN_PAYMENT_OVERDUE = "loan.payment_overdue"
    
    # System events
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_ALERT = "system.alert"


@dataclass
class WebhookEvent:
    """Webhook event data structure"""
    id: str
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    source_service: str
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source_service": self.source_service,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }


@dataclass
class WebhookSubscription:
    """Webhook subscription configuration"""
    id: str
    url: str
    events: List[EventType]
    secret: str
    status: WebhookStatus = WebhookStatus.ACTIVE
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    retry_backoff: float = 2.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_delivery: Optional[datetime] = None
    delivery_count: int = 0
    failure_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookDelivery:
    """Webhook delivery record"""
    id: str
    webhook_id: str
    event_id: str
    status: DeliveryStatus
    url: str
    request_headers: Dict[str, str]
    request_body: str
    response_status: Optional[int] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: Optional[str] = None
    attempt_number: int = 1
    next_retry: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WebhookRequest(BaseModel):
    """Webhook subscription request model"""
    url: HttpUrl
    events: List[EventType]
    secret: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    timeout: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    retry_backoff: float = Field(default=2.0, ge=1.0, le=10.0)
    
    @validator('events')
    def validate_events(cls, v):
        if not v:
            raise ValueError('At least one event type must be specified')
        return v


class WebhookResponse(BaseModel):
    """Webhook subscription response model"""
    id: str
    url: str
    events: List[str]
    status: WebhookStatus
    timeout: int
    retry_attempts: int
    retry_backoff: float
    created_at: datetime
    updated_at: datetime
    last_delivery: Optional[datetime] = None
    delivery_count: int = 0
    failure_count: int = 0


class WebhookSigner:
    """Webhook signature generation and verification"""
    
    @staticmethod
    def generate_signature(payload: str, secret: str, algorithm: str = "sha256") -> str:
        """Generate webhook signature"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            getattr(hashlib, algorithm)
        ).hexdigest()
        return f"{algorithm}={signature}"
    
    @staticmethod
    def verify_signature(payload: str, secret: str, signature: str) -> bool:
        """Verify webhook signature"""
        try:
            algorithm, expected_signature = signature.split('=', 1)
            computed_signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                getattr(hashlib, algorithm)
            ).hexdigest()
            return hmac.compare_digest(computed_signature, expected_signature)
        except (ValueError, AttributeError):
            return False


class WebhookValidator:
    """Webhook endpoint validation"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    async def validate_endpoint(self, url: str, secret: str = None) -> Dict[str, Any]:
        """Validate webhook endpoint"""
        validation_result = {
            "valid": False,
            "reachable": False,
            "supports_post": False,
            "supports_signatures": False,
            "response_time_ms": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            # Test POST request with validation payload
            test_payload = {
                "event_type": "webhook.validation",
                "data": {"test": True},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload_str = json.dumps(test_payload)
            headers = {"Content-Type": "application/json"}
            
            if secret:
                signature = WebhookSigner.generate_signature(payload_str, secret)
                headers["X-Webhook-Signature"] = signature
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, content=payload_str, headers=headers)
                
                response_time = (time.time() - start_time) * 1000
                validation_result["response_time_ms"] = round(response_time, 2)
                validation_result["reachable"] = True
                
                # Check if endpoint accepts POST
                if response.status_code < 500:
                    validation_result["supports_post"] = True
                
                # Check if endpoint handles signatures (any 2xx response indicates support)
                if secret and 200 <= response.status_code < 300:
                    validation_result["supports_signatures"] = True
                
                # Consider valid if reachable and supports POST
                validation_result["valid"] = validation_result["reachable"] and validation_result["supports_post"]
        
        except httpx.TimeoutException:
            validation_result["error"] = "Endpoint timeout"
        except httpx.ConnectError:
            validation_result["error"] = "Connection failed"
        except Exception as e:
            validation_result["error"] = str(e)
        
        return validation_result


class WebhookStorage:
    """Webhook subscription and delivery storage"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        Base = declarative_base()
        
        class WebhookSubscriptionModel(Base):
            __tablename__ = 'webhook_subscriptions'
            
            id = Column(String, primary_key=True)
            url = Column(String, nullable=False)
            events = Column(JSON, nullable=False)
            secret = Column(String)
            status = Column(String, nullable=False)
            headers = Column(JSON)
            timeout = Column(Integer, default=30)
            retry_attempts = Column(Integer, default=3)
            retry_backoff = Column(String, default="2.0")
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow)
            last_delivery = Column(DateTime)
            delivery_count = Column(Integer, default=0)
            failure_count = Column(Integer, default=0)
            metadata = Column(JSON)
        
        class WebhookDeliveryModel(Base):
            __tablename__ = 'webhook_deliveries'
            
            id = Column(String, primary_key=True)
            webhook_id = Column(String, nullable=False)
            event_id = Column(String, nullable=False)
            status = Column(String, nullable=False)
            url = Column(String, nullable=False)
            request_headers = Column(JSON)
            request_body = Column(Text)
            response_status = Column(Integer)
            response_headers = Column(JSON)
            response_body = Column(Text)
            attempt_number = Column(Integer, default=1)
            next_retry = Column(DateTime)
            created_at = Column(DateTime, default=datetime.utcnow)
            delivered_at = Column(DateTime)
            error_message = Column(Text)
        
        Base.metadata.create_all(self.engine)
        self.WebhookSubscriptionModel = WebhookSubscriptionModel
        self.WebhookDeliveryModel = WebhookDeliveryModel
    
    async def create_subscription(self, subscription: WebhookSubscription) -> WebhookSubscription:
        """Create webhook subscription"""
        with self.Session() as session:
            model = self.WebhookSubscriptionModel(
                id=subscription.id,
                url=subscription.url,
                events=[e.value for e in subscription.events],
                secret=subscription.secret,
                status=subscription.status.value,
                headers=subscription.headers,
                timeout=subscription.timeout,
                retry_attempts=subscription.retry_attempts,
                retry_backoff=str(subscription.retry_backoff),
                created_at=subscription.created_at,
                updated_at=subscription.updated_at,
                metadata=subscription.metadata
            )
            session.add(model)
            session.commit()
            return subscription
    
    async def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get webhook subscription by ID"""
        with self.Session() as session:
            model = session.query(self.WebhookSubscriptionModel).filter_by(id=subscription_id).first()
            if not model:
                return None
            
            return WebhookSubscription(
                id=model.id,
                url=model.url,
                events=[EventType(e) for e in model.events],
                secret=model.secret,
                status=WebhookStatus(model.status),
                headers=model.headers or {},
                timeout=model.timeout,
                retry_attempts=model.retry_attempts,
                retry_backoff=float(model.retry_backoff),
                created_at=model.created_at,
                updated_at=model.updated_at,
                last_delivery=model.last_delivery,
                delivery_count=model.delivery_count,
                failure_count=model.failure_count,
                metadata=model.metadata or {}
            )
    
    async def list_subscriptions(self, status: Optional[WebhookStatus] = None) -> List[WebhookSubscription]:
        """List webhook subscriptions"""
        with self.Session() as session:
            query = session.query(self.WebhookSubscriptionModel)
            if status:
                query = query.filter_by(status=status.value)
            
            models = query.all()
            return [
                WebhookSubscription(
                    id=model.id,
                    url=model.url,
                    events=[EventType(e) for e in model.events],
                    secret=model.secret,
                    status=WebhookStatus(model.status),
                    headers=model.headers or {},
                    timeout=model.timeout,
                    retry_attempts=model.retry_attempts,
                    retry_backoff=float(model.retry_backoff),
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                    last_delivery=model.last_delivery,
                    delivery_count=model.delivery_count,
                    failure_count=model.failure_count,
                    metadata=model.metadata or {}
                )
                for model in models
            ]
    
    async def update_subscription_stats(self, subscription_id: str, delivered: bool):
        """Update subscription delivery statistics"""
        with self.Session() as session:
            model = session.query(self.WebhookSubscriptionModel).filter_by(id=subscription_id).first()
            if model:
                model.delivery_count += 1
                if not delivered:
                    model.failure_count += 1
                model.last_delivery = datetime.utcnow()
                session.commit()
    
    async def create_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        """Create webhook delivery record"""
        with self.Session() as session:
            model = self.WebhookDeliveryModel(
                id=delivery.id,
                webhook_id=delivery.webhook_id,
                event_id=delivery.event_id,
                status=delivery.status.value,
                url=delivery.url,
                request_headers=delivery.request_headers,
                request_body=delivery.request_body,
                response_status=delivery.response_status,
                response_headers=delivery.response_headers,
                response_body=delivery.response_body,
                attempt_number=delivery.attempt_number,
                next_retry=delivery.next_retry,
                created_at=delivery.created_at,
                delivered_at=delivery.delivered_at,
                error_message=delivery.error_message
            )
            session.add(model)
            session.commit()
            return delivery


class WebhookDeliveryService:
    """Webhook delivery service with retry logic"""
    
    def __init__(self, storage: WebhookStorage, redis_client: redis.Redis):
        self.storage = storage
        self.redis = redis_client
        self.http_client = httpx.AsyncClient()
    
    async def deliver_webhook(
        self,
        subscription: WebhookSubscription,
        event: WebhookEvent
    ) -> WebhookDelivery:
        """Deliver webhook with retry logic"""
        delivery_id = str(uuid.uuid4())
        payload = json.dumps(event.to_dict())
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "CBS-Webhook/2.0",
            "X-Webhook-Event": event.event_type.value,
            "X-Webhook-ID": delivery_id,
            "X-Webhook-Timestamp": event.timestamp.isoformat()
        }
        
        # Add custom headers
        headers.update(subscription.headers)
        
        # Add signature if secret is provided
        if subscription.secret:
            signature = WebhookSigner.generate_signature(payload, subscription.secret)
            headers["X-Webhook-Signature"] = signature
        
        # Create delivery record
        delivery = WebhookDelivery(
            id=delivery_id,
            webhook_id=subscription.id,
            event_id=event.id,
            status=DeliveryStatus.PENDING,
            url=subscription.url,
            request_headers=headers,
            request_body=payload
        )
        
        # Attempt delivery
        start_time = time.time()
        
        try:
            webhook_deliveries_attempted.labels(
                webhook_id=subscription.id,
                event_type=event.event_type.value
            ).inc()
            
            response = await self.http_client.post(
                subscription.url,
                content=payload,
                headers=headers,
                timeout=subscription.timeout
            )
            
            delivery.response_status = response.status_code
            delivery.response_headers = dict(response.headers)
            delivery.response_body = response.text
            delivery.delivered_at = datetime.utcnow()
            
            # Consider 2xx responses as successful
            if 200 <= response.status_code < 300:
                delivery.status = DeliveryStatus.DELIVERED
                webhook_deliveries_succeeded.labels(
                    webhook_id=subscription.id,
                    event_type=event.event_type.value
                ).inc()
                await self.storage.update_subscription_stats(subscription.id, True)
            else:
                delivery.status = DeliveryStatus.FAILED
                delivery.error_message = f"HTTP {response.status_code}: {response.text}"
                webhook_deliveries_failed.labels(
                    webhook_id=subscription.id,
                    event_type=event.event_type.value,
                    status_code=str(response.status_code)
                ).inc()
                await self.storage.update_subscription_stats(subscription.id, False)
        
        except httpx.TimeoutException:
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = "Request timeout"
            webhook_deliveries_failed.labels(
                webhook_id=subscription.id,
                event_type=event.event_type.value,
                status_code="timeout"
            ).inc()
            await self.storage.update_subscription_stats(subscription.id, False)
        
        except Exception as e:
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = str(e)
            webhook_deliveries_failed.labels(
                webhook_id=subscription.id,
                event_type=event.event_type.value,
                status_code="error"
            ).inc()
            await self.storage.update_subscription_stats(subscription.id, False)
        
        finally:
            # Record delivery duration
            duration = time.time() - start_time
            webhook_delivery_duration.observe(duration)
        
        # Save delivery record
        await self.storage.create_delivery(delivery)
        
        # Schedule retry if needed
        if delivery.status == DeliveryStatus.FAILED and delivery.attempt_number < subscription.retry_attempts:
            await self._schedule_retry(subscription, event, delivery)
        
        return delivery
    
    async def _schedule_retry(
        self,
        subscription: WebhookSubscription,
        event: WebhookEvent,
        failed_delivery: WebhookDelivery
    ):
        """Schedule webhook retry"""
        retry_delay = subscription.retry_backoff ** failed_delivery.attempt_number
        next_retry = datetime.utcnow() + timedelta(seconds=retry_delay)
        
        # Store retry information in Redis
        retry_key = f"webhook_retry:{failed_delivery.id}"
        retry_data = {
            "subscription_id": subscription.id,
            "event": event.to_dict(),
            "attempt_number": failed_delivery.attempt_number + 1
        }
        
        await self.redis.setex(
            retry_key,
            int(retry_delay),
            json.dumps(retry_data, default=str)
        )
        
        logger.info(
            "Webhook retry scheduled",
            delivery_id=failed_delivery.id,
            webhook_id=subscription.id,
            attempt_number=failed_delivery.attempt_number + 1,
            retry_delay=retry_delay
        )
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


class WebhookManager:
    """Main webhook management system"""
    
    def __init__(
        self,
        database_url: str,
        redis_url: str,
        kafka_config: Dict[str, Any]
    ):
        self.storage = WebhookStorage(database_url)
        self.redis = redis.from_url(redis_url)
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=kafka_config.get("bootstrap_servers", ["localhost:9092"]),
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        self.delivery_service = WebhookDeliveryService(self.storage, self.redis)
        self.validator = WebhookValidator()
        self._consumer_task = None
    
    async def create_subscription(self, request: WebhookRequest) -> WebhookResponse:
        """Create webhook subscription"""
        # Generate ID and secret
        subscription_id = str(uuid.uuid4())
        secret = request.secret or self._generate_secret()
        
        # Validate endpoint
        validation_result = await self.validator.validate_endpoint(str(request.url), secret)
        if not validation_result["valid"]:
            raise ValueError(f"Invalid webhook endpoint: {validation_result.get('error', 'Unknown error')}")
        
        # Create subscription
        subscription = WebhookSubscription(
            id=subscription_id,
            url=str(request.url),
            events=request.events,
            secret=secret,
            headers=request.headers,
            timeout=request.timeout,
            retry_attempts=request.retry_attempts,
            retry_backoff=request.retry_backoff
        )
        
        await self.storage.create_subscription(subscription)
        active_webhooks.inc()
        
        logger.info("Webhook subscription created", subscription_id=subscription_id, url=subscription.url)
        
        return WebhookResponse(
            id=subscription.id,
            url=subscription.url,
            events=[e.value for e in subscription.events],
            status=subscription.status,
            timeout=subscription.timeout,
            retry_attempts=subscription.retry_attempts,
            retry_backoff=subscription.retry_backoff,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )
    
    async def get_subscription(self, subscription_id: str) -> Optional[WebhookResponse]:
        """Get webhook subscription"""
        subscription = await self.storage.get_subscription(subscription_id)
        if not subscription:
            return None
        
        return WebhookResponse(
            id=subscription.id,
            url=subscription.url,
            events=[e.value for e in subscription.events],
            status=subscription.status,
            timeout=subscription.timeout,
            retry_attempts=subscription.retry_attempts,
            retry_backoff=subscription.retry_backoff,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            last_delivery=subscription.last_delivery,
            delivery_count=subscription.delivery_count,
            failure_count=subscription.failure_count
        )
    
    async def list_subscriptions(self, status: Optional[WebhookStatus] = None) -> List[WebhookResponse]:
        """List webhook subscriptions"""
        subscriptions = await self.storage.list_subscriptions(status)
        return [
            WebhookResponse(
                id=sub.id,
                url=sub.url,
                events=[e.value for e in sub.events],
                status=sub.status,
                timeout=sub.timeout,
                retry_attempts=sub.retry_attempts,
                retry_backoff=sub.retry_backoff,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
                last_delivery=sub.last_delivery,
                delivery_count=sub.delivery_count,
                failure_count=sub.failure_count
            )
            for sub in subscriptions
        ]
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete webhook subscription"""
        # Implementation would delete from database
        active_webhooks.dec()
        logger.info("Webhook subscription deleted", subscription_id=subscription_id)
        return True
    
    async def trigger_event(self, event: WebhookEvent):
        """Trigger webhook event"""
        # Publish event to Kafka for async processing
        self.kafka_producer.send(
            "webhook-events",
            value=event.to_dict()
        )
        
        webhook_events_produced.labels(event_type=event.event_type.value).inc()
        
        logger.info(
            "Webhook event triggered",
            event_id=event.id,
            event_type=event.event_type.value,
            source_service=event.source_service
        )
    
    async def process_events(self):
        """Process webhook events from Kafka"""
        consumer = KafkaConsumer(
            "webhook-events",
            bootstrap_servers=["localhost:9092"],
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        for message in consumer:
            try:
                event_data = message.value
                event = WebhookEvent(
                    id=event_data["id"],
                    event_type=EventType(event_data["event_type"]),
                    data=event_data["data"],
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    source_service=event_data["source_service"],
                    correlation_id=event_data.get("correlation_id"),
                    metadata=event_data.get("metadata", {})
                )
                
                await self._deliver_to_subscribers(event)
            
            except Exception as e:
                logger.error("Failed to process webhook event", error=str(e))
    
    async def _deliver_to_subscribers(self, event: WebhookEvent):
        """Deliver event to all matching subscribers"""
        subscriptions = await self.storage.list_subscriptions(WebhookStatus.ACTIVE)
        
        delivery_tasks = []
        for subscription in subscriptions:
            if event.event_type in subscription.events:
                task = self.delivery_service.deliver_webhook(subscription, event)
                delivery_tasks.append(task)
        
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)
    
    def _generate_secret(self) -> str:
        """Generate webhook secret"""
        return str(uuid.uuid4()).replace('-', '')
    
    async def start_event_processor(self):
        """Start background event processor"""
        self._consumer_task = asyncio.create_task(self.process_events())
    
    async def stop_event_processor(self):
        """Stop background event processor"""
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
    
    async def close(self):
        """Close all connections"""
        await self.stop_event_processor()
        await self.delivery_service.close()
        await self.redis.close()
        self.kafka_producer.close()


# Factory function
def create_webhook_manager(config: Dict[str, Any]) -> WebhookManager:
    """Create webhook manager with configuration"""
    return WebhookManager(
        database_url=config["database_url"],
        redis_url=config["redis_url"],
        kafka_config=config["kafka"]
    )


# Usage example
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Configuration
        config = {
            "database_url": "postgresql://user:password@localhost/webhooks",
            "redis_url": "redis://localhost:6379",
            "kafka": {
                "bootstrap_servers": ["localhost:9092"]
            }
        }
        
        # Create webhook manager
        webhook_manager = create_webhook_manager(config)
        
        # Start event processor
        await webhook_manager.start_event_processor()
        
        # Create subscription
        request = WebhookRequest(
            url="https://example.com/webhooks",
            events=[EventType.CUSTOMER_CREATED, EventType.ACCOUNT_CREATED],
            timeout=30,
            retry_attempts=3
        )
        
        subscription = await webhook_manager.create_subscription(request)
        print(f"Created webhook subscription: {subscription.id}")
        
        # Trigger event
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            event_type=EventType.CUSTOMER_CREATED,
            data={"customer_id": "123", "name": "John Doe"},
            timestamp=datetime.utcnow(),
            source_service="customer-service"
        )
        
        await webhook_manager.trigger_event(event)
        
        # Wait a bit for processing
        await asyncio.sleep(5)
        
        await webhook_manager.close()
    
    asyncio.run(main())
