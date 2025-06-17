"""
Notification Service Application Services

This module contains the core business logic and use cases for the notification service,
implementing comprehensive notification processing functionality.
"""

import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..infrastructure.database import (
    NotificationType, NotificationStatus, NotificationPriority, NotificationCategory
)
from ..infrastructure.repositories import (
    SQLNotificationRepository, SQLNotificationTemplateRepository,
    SQLNotificationDeliveryLogRepository, SQLNotificationPreferenceRepository,
    SQLNotificationChannelRepository
)


@dataclass
class NotificationRequest:
    """Notification request data structure"""
    recipient_id: str
    notification_type: str
    category: str
    message: str
    title: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    priority: str = "normal"
    source_service: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    delivery_address: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class NotificationResponse:
    """Notification response data structure"""
    success: bool
    message_id: Optional[str] = None
    notification_id: Optional[str] = None
    error_message: Optional[str] = None
    delivery_status: Optional[str] = None


class CreateNotificationUseCase:
    """Use case for creating notifications"""
    
    def __init__(self, notification_repo: SQLNotificationRepository,
                 template_repo: SQLNotificationTemplateRepository,
                 preference_repo: SQLNotificationPreferenceRepository):
        self.notification_repo = notification_repo
        self.template_repo = template_repo
        self.preference_repo = preference_repo
    
    def execute(self, request: NotificationRequest) -> NotificationResponse:
        """Execute notification creation"""
        try:
            # Validate request
            if not self._validate_request(request):
                return NotificationResponse(
                    success=False,
                    error_message="Invalid notification request"
                )
            
            # Check user preferences
            if not self._check_user_preferences(request):
                return NotificationResponse(
                    success=False,
                    error_message="Notification blocked by user preferences"
                )
            
            # Process template if provided
            message, title, html_content = self._process_template(request)
            
            # Prepare notification data
            notification_data = {
                'recipient_id': request.recipient_id,
                'notification_type': request.notification_type,
                'category': request.category,
                'priority': request.priority,
                'title': title or request.title,
                'message': message,
                'html_content': html_content,
                'template_id': request.template_id,
                'template_data': request.template_data,
                'delivery_address': request.delivery_address,
                'source_service': request.source_service,
                'reference_type': request.reference_type,
                'reference_id': request.reference_id,
                'scheduled_at': request.scheduled_at,
                'expires_at': request.expires_at or self._calculate_expiry(),
                'metadata': request.metadata
            }
            
            # Create notification
            notification = self.notification_repo.create_notification(notification_data)
            
            return NotificationResponse(
                success=True,
                message_id=notification.message_id,
                notification_id=str(notification.notification_id),
                delivery_status="pending"
            )
            
        except Exception as e:
            return NotificationResponse(
                success=False,
                error_message=f"Failed to create notification: {str(e)}"
            )
    
    def _validate_request(self, request: NotificationRequest) -> bool:
        """Validate notification request"""
        if not request.recipient_id or not request.message:
            return False
        
        try:
            NotificationType(request.notification_type)
            NotificationCategory(request.category)
            NotificationPriority(request.priority)
            return True
        except ValueError:
            return False
    
    def _check_user_preferences(self, request: NotificationRequest) -> bool:
        """Check if notification is allowed by user preferences"""
        return self.preference_repo.is_notification_allowed(
            request.recipient_id,
            NotificationCategory(request.category),
            NotificationType(request.notification_type)
        )
    
    def _process_template(self, request: NotificationRequest) -> Tuple[str, Optional[str], Optional[str]]:
        """Process notification template"""
        message = request.message
        title = request.title
        html_content = None
        
        if request.template_id:
            template = self.template_repo.get_template_by_id(request.template_id)
            if template:
                # Simple template processing (in production, use proper template engine)
                template_data = request.template_data or {}
                
                message = self._render_template(template.message_template, template_data)
                if template.title_template:
                    title = self._render_template(template.title_template, template_data)
                if template.html_template:
                    html_content = self._render_template(template.html_template, template_data)
        
        return message, title, html_content
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Simple template rendering (replace with proper template engine)"""
        result = template
        for key, value in data.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
    
    def _calculate_expiry(self) -> datetime:
        """Calculate default expiry time"""
        return datetime.utcnow() + timedelta(hours=24)


class ProcessNotificationUseCase:
    """Use case for processing notifications"""
    
    def __init__(self, notification_repo: SQLNotificationRepository,
                 delivery_log_repo: SQLNotificationDeliveryLogRepository,
                 channel_repo: SQLNotificationChannelRepository):
        self.notification_repo = notification_repo
        self.delivery_log_repo = delivery_log_repo
        self.channel_repo = channel_repo
        self.delivery_providers = {}  # Will be injected with actual providers
    
    def set_delivery_providers(self, providers: Dict[str, Any]):
        """Set notification delivery providers"""
        self.delivery_providers = providers
    
    def execute(self, notification_id: uuid.UUID) -> NotificationResponse:
        """Execute notification processing"""
        try:
            # Get notification
            notification = self.notification_repo.get_notification_by_id(notification_id)
            if not notification:
                return NotificationResponse(
                    success=False,
                    error_message="Notification not found"
                )
            
            # Check if already processed
            if notification.status != NotificationStatus.PENDING:
                return NotificationResponse(
                    success=True,
                    message_id=notification.message_id,
                    delivery_status=notification.status.value
                )
            
            # Get delivery channel
            channels = self.channel_repo.get_active_channels_by_type(notification.notification_type)
            if not channels:
                return NotificationResponse(
                    success=False,
                    error_message=f"No active channels for {notification.notification_type.value}"
                )
            
            # Attempt delivery
            delivery_result = self._attempt_delivery(notification, channels[0])
            
            # Update notification status
            if delivery_result['success']:
                self.notification_repo.update_notification_status(
                    notification_id, 
                    NotificationStatus.SENT,
                    {'delivered_at': datetime.utcnow()}
                )
                status = "sent"
            else:
                self.notification_repo.update_notification_status(
                    notification_id,
                    NotificationStatus.FAILED
                )
                status = "failed"
            
            # Log delivery attempt
            self._log_delivery_attempt(notification, delivery_result)
            
            return NotificationResponse(
                success=delivery_result['success'],
                message_id=notification.message_id,
                notification_id=str(notification_id),
                delivery_status=status,
                error_message=delivery_result.get('error_message')
            )
            
        except Exception as e:
            return NotificationResponse(
                success=False,
                error_message=f"Failed to process notification: {str(e)}"
            )
    
    def _attempt_delivery(self, notification, channel) -> Dict[str, Any]:
        """Attempt notification delivery"""
        provider_name = channel.provider_name
        provider = self.delivery_providers.get(provider_name)
        
        if not provider:
            return {
                'success': False,
                'error_message': f"Provider {provider_name} not available",
                'provider_name': provider_name
            }
        
        try:
            # Call provider delivery method
            start_time = datetime.utcnow()
            
            if notification.notification_type == NotificationType.SMS:
                result = provider.send_sms(
                    phone_number=notification.delivery_address,
                    message=notification.message
                )
            elif notification.notification_type == NotificationType.EMAIL:
                result = provider.send_email(
                    email=notification.delivery_address,
                    subject=notification.title or "Notification",
                    message=notification.message,
                    html_content=notification.html_content
                )
            elif notification.notification_type == NotificationType.PUSH:
                result = provider.send_push(
                    device_token=notification.delivery_address,
                    title=notification.title or "Notification",
                    message=notification.message,
                    data=notification.metadata
                )
            else:
                return {
                    'success': False,
                    'error_message': f"Unsupported notification type: {notification.notification_type.value}",
                    'provider_name': provider_name
                }
            
            end_time = datetime.utcnow()
            response_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                'success': result.get('success', False),
                'provider_message_id': result.get('message_id'),
                'provider_response': result,
                'response_time_ms': response_time,
                'provider_name': provider_name,
                'sent_at': start_time,
                'error_message': result.get('error_message')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'provider_name': provider_name
            }
    
    def _log_delivery_attempt(self, notification, delivery_result):
        """Log delivery attempt"""
        log_data = {
            'notification_id': notification.notification_id,
            'attempt_number': notification.attempts + 1,
            'delivery_status': NotificationStatus.SENT if delivery_result['success'] else NotificationStatus.FAILED,
            'provider_name': delivery_result.get('provider_name'),
            'provider_message_id': delivery_result.get('provider_message_id'),
            'provider_response': delivery_result.get('provider_response'),
            'sent_at': delivery_result.get('sent_at'),
            'response_time_ms': delivery_result.get('response_time_ms'),
            'error_message': delivery_result.get('error_message')
        }
        
        self.delivery_log_repo.create_delivery_log(log_data)


class BulkNotificationUseCase:
    """Use case for bulk notification processing"""
    
    def __init__(self, create_notification_usecase: CreateNotificationUseCase):
        self.create_notification_usecase = create_notification_usecase
    
    def execute(self, requests: List[NotificationRequest]) -> List[NotificationResponse]:
        """Execute bulk notification creation"""
        responses = []
        
        for request in requests:
            response = self.create_notification_usecase.execute(request)
            responses.append(response)
        
        return responses


class NotificationQueryUseCase:
    """Use case for querying notifications"""
    
    def __init__(self, notification_repo: SQLNotificationRepository,
                 delivery_log_repo: SQLNotificationDeliveryLogRepository):
        self.notification_repo = notification_repo
        self.delivery_log_repo = delivery_log_repo
    
    def get_notifications_by_recipient(self, recipient_id: str, 
                                     page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get notifications for a recipient"""
        offset = (page - 1) * page_size
        notifications = self.notification_repo.get_notifications_by_recipient(
            recipient_id, page_size, offset
        )
        
        return {
            'notifications': [self._format_notification(n) for n in notifications],
            'page': page,
            'page_size': page_size,
            'total_count': len(notifications)  # Simplified for this implementation
        }
    
    def search_notifications(self, filters: Dict[str, Any], 
                           page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Search notifications with filters"""
        offset = (page - 1) * page_size
        notifications, total_count = self.notification_repo.search_notifications(
            filters, page_size, offset
        )
        
        return {
            'notifications': [self._format_notification(n) for n in notifications],
            'page': page,
            'page_size': page_size,
            'total_count': total_count
        }
    
    def get_notification_details(self, notification_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get detailed notification information"""
        notification = self.notification_repo.get_notification_by_id(notification_id)
        if not notification:
            return None
        
        delivery_logs = self.delivery_log_repo.get_delivery_logs_by_notification(notification_id)
        
        return {
            'notification': self._format_notification(notification),
            'delivery_logs': [self._format_delivery_log(log) for log in delivery_logs]
        }
    
    def _format_notification(self, notification) -> Dict[str, Any]:
        """Format notification for API response"""
        return {
            'notification_id': str(notification.notification_id),
            'message_id': notification.message_id,
            'recipient_id': notification.recipient_id,
            'notification_type': notification.notification_type.value,
            'category': notification.category.value,
            'priority': notification.priority.value,
            'status': notification.status.value,
            'title': notification.title,
            'message': notification.message,
            'attempts': notification.attempts,
            'max_attempts': notification.max_attempts,
            'created_at': notification.created_at.isoformat(),
            'updated_at': notification.updated_at.isoformat() if notification.updated_at else None,
            'delivered_at': notification.delivered_at.isoformat() if notification.delivered_at else None,
            'source_service': notification.source_service,
            'reference_type': notification.reference_type,
            'reference_id': notification.reference_id
        }
    
    def _format_delivery_log(self, log) -> Dict[str, Any]:
        """Format delivery log for API response"""
        return {
            'log_id': str(log.log_id),
            'attempt_number': log.attempt_number,
            'delivery_status': log.delivery_status.value,
            'provider_name': log.provider_name,
            'provider_message_id': log.provider_message_id,
            'sent_at': log.sent_at.isoformat() if log.sent_at else None,
            'delivered_at': log.delivered_at.isoformat() if log.delivered_at else None,
            'response_time_ms': log.response_time_ms,
            'error_code': log.error_code,
            'error_message': log.error_message,
            'created_at': log.created_at.isoformat()
        }


class NotificationService:
    """Main notification service orchestrating all use cases"""
    
    def __init__(self, notification_repo: SQLNotificationRepository,
                 template_repo: SQLNotificationTemplateRepository,
                 delivery_log_repo: SQLNotificationDeliveryLogRepository,
                 preference_repo: SQLNotificationPreferenceRepository,
                 channel_repo: SQLNotificationChannelRepository):
        
        self.notification_repo = notification_repo
        self.template_repo = template_repo
        self.delivery_log_repo = delivery_log_repo
        self.preference_repo = preference_repo
        self.channel_repo = channel_repo
        
        # Initialize use cases
        self.create_notification = CreateNotificationUseCase(
            notification_repo, template_repo, preference_repo
        )
        self.process_notification = ProcessNotificationUseCase(
            notification_repo, delivery_log_repo, channel_repo
        )
        self.bulk_notification = BulkNotificationUseCase(self.create_notification)
        self.query_notifications = NotificationQueryUseCase(
            notification_repo, delivery_log_repo
        )
    
    def send_notification(self, request: NotificationRequest) -> NotificationResponse:
        """Send a single notification"""
        # Create notification
        create_response = self.create_notification.execute(request)
        if not create_response.success:
            return create_response
        
        # Process notification if not scheduled
        if not request.scheduled_at:
            notification_id = uuid.UUID(create_response.notification_id)
            return self.process_notification.execute(notification_id)
        
        return create_response
    
    def send_bulk_notifications(self, requests: List[NotificationRequest]) -> List[NotificationResponse]:
        """Send bulk notifications"""
        return self.bulk_notification.execute(requests)
    
    def process_pending_notifications(self, limit: int = 100) -> Dict[str, Any]:
        """Process pending notifications"""
        pending = self.notification_repo.get_pending_notifications(limit)
        
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for notification in pending:
            try:
                response = self.process_notification.execute(notification.notification_id)
                results['processed'] += 1
                
                if response.success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    if response.error_message:
                        results['errors'].append({
                            'notification_id': str(notification.notification_id),
                            'error': response.error_message
                        })
                        
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'notification_id': str(notification.notification_id),
                    'error': str(e)
                })
        
        return results
    
    def retry_failed_notifications(self) -> Dict[str, Any]:
        """Retry failed notifications"""
        failed = self.notification_repo.get_failed_notifications_for_retry()
        
        results = {
            'retried': 0,
            'successful': 0,
            'failed': 0
        }
        
        for notification in failed:
            response = self.process_notification.execute(notification.notification_id)
            results['retried'] += 1
            
            if response.success:
                results['successful'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    def set_delivery_providers(self, providers: Dict[str, Any]):
        """Set notification delivery providers"""
        self.process_notification.set_delivery_providers(providers)


# Export main service and data classes
__all__ = [
    'NotificationService',
    'NotificationRequest',
    'NotificationResponse',
    'CreateNotificationUseCase',
    'ProcessNotificationUseCase',
    'BulkNotificationUseCase',
    'NotificationQueryUseCase'
]
