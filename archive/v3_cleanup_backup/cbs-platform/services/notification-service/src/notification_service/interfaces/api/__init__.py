"""
Notification Service API Controllers

This module provides REST API endpoints for the notification service
using FastAPI with comprehensive notification management functionality.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from ..application.services.notification_services import (
    NotificationService, NotificationRequest, NotificationResponse
)
from ..infrastructure.database import DatabaseManager, NotificationType, NotificationCategory, NotificationPriority
from ..infrastructure.repositories import (
    SQLNotificationRepository, SQLNotificationTemplateRepository,
    SQLNotificationDeliveryLogRepository, SQLNotificationPreferenceRepository,
    SQLNotificationChannelRepository
)


# Pydantic models for API
class NotificationCreateRequest(BaseModel):
    """Request model for creating notifications"""
    recipient_id: str = Field(..., description="Recipient identifier")
    notification_type: str = Field(..., description="Type of notification (sms, email, push, etc.)")
    category: str = Field(..., description="Notification category (transaction, account, etc.)")
    message: str = Field(..., description="Notification message content")
    title: Optional[str] = Field(None, description="Notification title")
    template_id: Optional[str] = Field(None, description="Template identifier")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Template data for rendering")
    priority: str = Field("normal", description="Notification priority")
    source_service: Optional[str] = Field(None, description="Source service name")
    reference_type: Optional[str] = Field(None, description="Reference entity type")
    reference_id: Optional[str] = Field(None, description="Reference entity ID")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule notification for future delivery")
    expires_at: Optional[datetime] = Field(None, description="Notification expiry time")
    delivery_address: Optional[str] = Field(None, description="Delivery address (phone/email/token)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('notification_type')
    def validate_notification_type(cls, v):
        try:
            NotificationType(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid notification type: {v}")
    
    @validator('category')
    def validate_category(cls, v):
        try:
            NotificationCategory(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid category: {v}")
    
    @validator('priority')
    def validate_priority(cls, v):
        try:
            NotificationPriority(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid priority: {v}")


class BulkNotificationRequest(BaseModel):
    """Request model for bulk notifications"""
    notifications: List[NotificationCreateRequest] = Field(..., description="List of notifications to create")


class NotificationSearchRequest(BaseModel):
    """Request model for searching notifications"""
    recipient_id: Optional[str] = None
    notification_type: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    source_service: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")


class NotificationPreferenceRequest(BaseModel):
    """Request model for notification preferences"""
    user_id: str = Field(..., description="User identifier")
    user_type: str = Field("customer", description="User type")
    sms_enabled: bool = Field(True, description="Enable SMS notifications")
    email_enabled: bool = Field(True, description="Enable email notifications")
    push_enabled: bool = Field(True, description="Enable push notifications")
    in_app_enabled: bool = Field(True, description="Enable in-app notifications")
    transaction_notifications: bool = Field(True, description="Enable transaction notifications")
    account_notifications: bool = Field(True, description="Enable account notifications")
    security_notifications: bool = Field(True, description="Enable security notifications")
    payment_notifications: bool = Field(True, description="Enable payment notifications")
    loan_notifications: bool = Field(True, description="Enable loan notifications")
    marketing_notifications: bool = Field(False, description="Enable marketing notifications")
    system_notifications: bool = Field(True, description="Enable system notifications")
    phone_number: Optional[str] = Field(None, description="Phone number for SMS")
    email_address: Optional[str] = Field(None, description="Email address")
    device_tokens: Optional[List[str]] = Field(None, description="Device tokens for push notifications")
    preferred_language: str = Field("en", description="Preferred language")
    timezone: str = Field("Asia/Kolkata", description="Timezone")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")
    max_sms_per_day: int = Field(10, description="Maximum SMS per day")
    max_email_per_day: int = Field(20, description="Maximum emails per day")
    max_push_per_day: int = Field(50, description="Maximum push notifications per day")


class NotificationTemplateRequest(BaseModel):
    """Request model for notification templates"""
    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: str = Field(..., description="Template category")
    notification_type: str = Field(..., description="Notification type")
    title_template: Optional[str] = Field(None, description="Title template")
    message_template: str = Field(..., description="Message template")
    html_template: Optional[str] = Field(None, description="HTML template")
    default_priority: str = Field("normal", description="Default priority")
    max_attempts: int = Field(3, description="Maximum delivery attempts")
    retry_delay_minutes: int = Field(5, description="Retry delay in minutes")
    expiry_hours: int = Field(24, description="Expiry time in hours")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    validation_schema: Optional[Dict[str, Any]] = Field(None, description="Validation schema")
    version: str = Field("1.0", description="Template version")
    created_by: Optional[str] = Field(None, description="Created by user")


# Database dependency
def get_database():
    """Get database session"""
    # This would be configured with actual database URL
    db_manager = DatabaseManager("postgresql://user:pass@localhost/cbs_notifications")
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


# Service dependency
def get_notification_service(db: Session = Depends(get_database)) -> NotificationService:
    """Get notification service instance"""
    notification_repo = SQLNotificationRepository(db)
    template_repo = SQLNotificationTemplateRepository(db)
    delivery_log_repo = SQLNotificationDeliveryLogRepository(db)
    preference_repo = SQLNotificationPreferenceRepository(db)
    channel_repo = SQLNotificationChannelRepository(db)
    
    return NotificationService(
        notification_repo, template_repo, delivery_log_repo,
        preference_repo, channel_repo
    )


# Create FastAPI app
app = FastAPI(
    title="CBS Notification Service API",
    description="Core Banking System Notification Service API",
    version="2.0.0",
    docs_url="/api/v2/notifications/docs",
    redoc_url="/api/v2/notifications/redoc"
)


@app.post("/api/v2/notifications", response_model=Dict[str, Any])
async def create_notification(
    request: NotificationCreateRequest,
    background_tasks: BackgroundTasks,
    service: NotificationService = Depends(get_notification_service)
):
    """Create and send a notification"""
    try:
        notification_request = NotificationRequest(
            recipient_id=request.recipient_id,
            notification_type=request.notification_type,
            category=request.category,
            message=request.message,
            title=request.title,
            template_id=request.template_id,
            template_data=request.template_data,
            priority=request.priority,
            source_service=request.source_service,
            reference_type=request.reference_type,
            reference_id=request.reference_id,
            scheduled_at=request.scheduled_at,
            expires_at=request.expires_at,
            delivery_address=request.delivery_address,
            metadata=request.metadata
        )
        
        response = service.send_notification(notification_request)
        
        if response.success:
            return {
                "success": True,
                "message": "Notification created successfully",
                "data": {
                    "message_id": response.message_id,
                    "notification_id": response.notification_id,
                    "delivery_status": response.delivery_status
                }
            }
        else:
            raise HTTPException(status_code=400, detail=response.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/notifications/bulk", response_model=Dict[str, Any])
async def create_bulk_notifications(
    request: BulkNotificationRequest,
    background_tasks: BackgroundTasks,
    service: NotificationService = Depends(get_notification_service)
):
    """Create and send bulk notifications"""
    try:
        notification_requests = []
        for req in request.notifications:
            notification_requests.append(NotificationRequest(
                recipient_id=req.recipient_id,
                notification_type=req.notification_type,
                category=req.category,
                message=req.message,
                title=req.title,
                template_id=req.template_id,
                template_data=req.template_data,
                priority=req.priority,
                source_service=req.source_service,
                reference_type=req.reference_type,
                reference_id=req.reference_id,
                scheduled_at=req.scheduled_at,
                expires_at=req.expires_at,
                delivery_address=req.delivery_address,
                metadata=req.metadata
            ))
        
        responses = service.send_bulk_notifications(notification_requests)
        
        successful = sum(1 for r in responses if r.success)
        failed = len(responses) - successful
        
        return {
            "success": True,
            "message": f"Processed {len(responses)} notifications",
            "data": {
                "total": len(responses),
                "successful": successful,
                "failed": failed,
                "results": [
                    {
                        "success": r.success,
                        "message_id": r.message_id,
                        "notification_id": r.notification_id,
                        "error_message": r.error_message
                    }
                    for r in responses
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v2/notifications/search", response_model=Dict[str, Any])
async def search_notifications(
    recipient_id: Optional[str] = Query(None),
    notification_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    source_service: Optional[str] = Query(None),
    reference_type: Optional[str] = Query(None),
    reference_id: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: NotificationService = Depends(get_notification_service)
):
    """Search notifications with filters"""
    try:
        filters = {
            'recipient_id': recipient_id,
            'notification_type': notification_type,
            'category': category,
            'status': status,
            'priority': priority,
            'source_service': source_service,
            'reference_type': reference_type,
            'reference_id': reference_id,
            'date_from': date_from,
            'date_to': date_to
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        result = service.query_notifications.search_notifications(filters, page, page_size)
        
        return {
            "success": True,
            "message": "Notifications retrieved successfully",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v2/notifications/recipient/{recipient_id}", response_model=Dict[str, Any])
async def get_notifications_by_recipient(
    recipient_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: NotificationService = Depends(get_notification_service)
):
    """Get notifications for a specific recipient"""
    try:
        result = service.query_notifications.get_notifications_by_recipient(
            recipient_id, page, page_size
        )
        
        return {
            "success": True,
            "message": "Notifications retrieved successfully",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v2/notifications/{notification_id}", response_model=Dict[str, Any])
async def get_notification_details(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """Get detailed notification information"""
    try:
        notification_uuid = uuid.UUID(notification_id)
        result = service.query_notifications.get_notification_details(notification_uuid)
        
        if not result:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "success": True,
            "message": "Notification details retrieved successfully",
            "data": result
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/notifications/preferences", response_model=Dict[str, Any])
async def create_or_update_preferences(
    request: NotificationPreferenceRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Create or update notification preferences"""
    try:
        preference_data = request.dict()
        preference = service.preference_repo.create_or_update_preferences(preference_data)
        
        return {
            "success": True,
            "message": "Notification preferences updated successfully",
            "data": {
                "preference_id": str(preference.preference_id),
                "user_id": preference.user_id,
                "updated_at": preference.updated_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v2/notifications/preferences/{user_id}", response_model=Dict[str, Any])
async def get_user_preferences(
    user_id: str,
    user_type: str = Query("customer"),
    service: NotificationService = Depends(get_notification_service)
):
    """Get user notification preferences"""
    try:
        preferences = service.preference_repo.get_user_preferences(user_id, user_type)
        
        if not preferences:
            raise HTTPException(status_code=404, detail="User preferences not found")
        
        return {
            "success": True,
            "message": "User preferences retrieved successfully",
            "data": {
                "preference_id": str(preferences.preference_id),
                "user_id": preferences.user_id,
                "user_type": preferences.user_type,
                "sms_enabled": preferences.sms_enabled,
                "email_enabled": preferences.email_enabled,
                "push_enabled": preferences.push_enabled,
                "in_app_enabled": preferences.in_app_enabled,
                "transaction_notifications": preferences.transaction_notifications,
                "account_notifications": preferences.account_notifications,
                "security_notifications": preferences.security_notifications,
                "payment_notifications": preferences.payment_notifications,
                "loan_notifications": preferences.loan_notifications,
                "marketing_notifications": preferences.marketing_notifications,
                "system_notifications": preferences.system_notifications,
                "phone_number": preferences.phone_number,
                "email_address": preferences.email_address,
                "device_tokens": preferences.device_tokens,
                "preferred_language": preferences.preferred_language,
                "timezone": preferences.timezone,
                "quiet_hours_start": preferences.quiet_hours_start,
                "quiet_hours_end": preferences.quiet_hours_end,
                "created_at": preferences.created_at.isoformat(),
                "updated_at": preferences.updated_at.isoformat() if preferences.updated_at else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/notifications/templates", response_model=Dict[str, Any])
async def create_template(
    request: NotificationTemplateRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Create a notification template"""
    try:
        template_data = request.dict()
        template = service.template_repo.create_template(template_data)
        
        return {
            "success": True,
            "message": "Notification template created successfully",
            "data": {
                "template_id": template.template_id,
                "name": template.name,
                "created_at": template.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v2/notifications/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """Get notification template"""
    try:
        template = service.template_repo.get_template_by_id(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "success": True,
            "message": "Template retrieved successfully",
            "data": {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "category": template.category.value,
                "notification_type": template.notification_type.value,
                "title_template": template.title_template,
                "message_template": template.message_template,
                "html_template": template.html_template,
                "default_priority": template.default_priority.value,
                "max_attempts": template.max_attempts,
                "retry_delay_minutes": template.retry_delay_minutes,
                "expiry_hours": template.expiry_hours,
                "variables": template.variables,
                "validation_schema": template.validation_schema,
                "is_active": template.is_active,
                "version": template.version,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat() if template.updated_at else None,
                "created_by": template.created_by
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/notifications/process-pending", response_model=Dict[str, Any])
async def process_pending_notifications(
    limit: int = Query(100, ge=1, le=1000),
    background_tasks: BackgroundTasks,
    service: NotificationService = Depends(get_notification_service)
):
    """Process pending notifications"""
    try:
        def process_notifications():
            return service.process_pending_notifications(limit)
        
        background_tasks.add_task(process_notifications)
        
        return {
            "success": True,
            "message": f"Processing up to {limit} pending notifications in background",
            "data": {
                "limit": limit,
                "status": "processing"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/notifications/retry-failed", response_model=Dict[str, Any])
async def retry_failed_notifications(
    background_tasks: BackgroundTasks,
    service: NotificationService = Depends(get_notification_service)
):
    """Retry failed notifications"""
    try:
        def retry_notifications():
            return service.retry_failed_notifications()
        
        background_tasks.add_task(retry_notifications)
        
        return {
            "success": True,
            "message": "Retrying failed notifications in background",
            "data": {
                "status": "retrying"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v2/notifications/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "message": "Notification service is healthy",
        "data": {
            "service": "notification-service",
            "version": "2.0.0",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@app.get("/api/v2/notifications/metrics", response_model=Dict[str, Any])
async def get_metrics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    service: NotificationService = Depends(get_notification_service)
):
    """Get notification metrics"""
    try:
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=7)
        if not date_to:
            date_to = datetime.utcnow()
        
        metrics = service.delivery_log_repo.get_delivery_statistics(date_from, date_to)
        
        return {
            "success": True,
            "message": "Metrics retrieved successfully",
            "data": {
                "period": {
                    "from": date_from.isoformat(),
                    "to": date_to.isoformat()
                },
                "metrics": metrics
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Export FastAPI app
__all__ = ['app']
