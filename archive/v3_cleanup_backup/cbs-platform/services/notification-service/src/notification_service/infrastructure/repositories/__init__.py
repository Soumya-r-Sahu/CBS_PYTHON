"""
Notification Service Repository Implementations

This module provides repository implementations for notification data access
using SQLAlchemy ORM with comprehensive querying capabilities.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import SQLAlchemyError

from ..database import (
    NotificationModel, NotificationTemplateModel, NotificationDeliveryLogModel,
    NotificationPreferenceModel, NotificationChannelModel, NotificationQueueModel,
    NotificationStatisticsModel, NotificationType, NotificationStatus, 
    NotificationPriority, NotificationCategory
)


class SQLNotificationRepository:
    """SQL implementation of notification repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_notification(self, notification_data: Dict[str, Any]) -> NotificationModel:
        """Create a new notification"""
        try:
            notification = NotificationModel(
                message_id=notification_data.get('message_id') or f"MSG_{uuid.uuid4().hex[:8]}",
                recipient_id=notification_data['recipient_id'],
                recipient_type=notification_data.get('recipient_type', 'customer'),
                notification_type=NotificationType(notification_data['notification_type']),
                category=NotificationCategory(notification_data['category']),
                priority=NotificationPriority(notification_data.get('priority', 'normal')),
                title=notification_data.get('title'),
                message=notification_data['message'],
                html_content=notification_data.get('html_content'),
                template_id=notification_data.get('template_id'),
                template_data=notification_data.get('template_data'),
                channel_config=notification_data.get('channel_config'),
                delivery_address=notification_data.get('delivery_address'),
                max_attempts=notification_data.get('max_attempts', 3),
                source_service=notification_data.get('source_service'),
                correlation_id=notification_data.get('correlation_id'),
                reference_type=notification_data.get('reference_type'),
                reference_id=notification_data.get('reference_id'),
                metadata=notification_data.get('metadata'),
                scheduled_at=notification_data.get('scheduled_at'),
                expires_at=notification_data.get('expires_at')
            )
            
            self.session.add(notification)
            self.session.commit()
            self.session.refresh(notification)
            return notification
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error creating notification: {str(e)}")
    
    def get_notification_by_id(self, notification_id: uuid.UUID) -> Optional[NotificationModel]:
        """Get notification by ID"""
        return self.session.query(NotificationModel).filter(
            NotificationModel.notification_id == notification_id
        ).first()
    
    def get_notification_by_message_id(self, message_id: str) -> Optional[NotificationModel]:
        """Get notification by message ID"""
        return self.session.query(NotificationModel).filter(
            NotificationModel.message_id == message_id
        ).first()
    
    def update_notification_status(self, notification_id: uuid.UUID, status: NotificationStatus, 
                                 delivery_details: Optional[Dict[str, Any]] = None) -> bool:
        """Update notification status"""
        try:
            notification = self.get_notification_by_id(notification_id)
            if not notification:
                return False
            
            notification.status = status
            notification.updated_at = datetime.utcnow()
            
            if delivery_details:
                if status == NotificationStatus.DELIVERED:
                    notification.delivered_at = delivery_details.get('delivered_at', datetime.utcnow())
                elif status == NotificationStatus.FAILED:
                    notification.attempts += 1
                    notification.last_attempt_at = datetime.utcnow()
            
            self.session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error updating notification status: {str(e)}")
    
    def get_pending_notifications(self, limit: int = 100, 
                                notification_type: Optional[NotificationType] = None) -> List[NotificationModel]:
        """Get pending notifications for processing"""
        query = self.session.query(NotificationModel).filter(
            NotificationModel.status == NotificationStatus.PENDING,
            or_(
                NotificationModel.scheduled_at.is_(None),
                NotificationModel.scheduled_at <= datetime.utcnow()
            ),
            or_(
                NotificationModel.expires_at.is_(None),
                NotificationModel.expires_at > datetime.utcnow()
            ),
            NotificationModel.attempts < NotificationModel.max_attempts
        )
        
        if notification_type:
            query = query.filter(NotificationModel.notification_type == notification_type)
        
        return query.order_by(
            desc(NotificationModel.priority.in_([NotificationPriority.CRITICAL, NotificationPriority.URGENT])),
            asc(NotificationModel.created_at)
        ).limit(limit).all()
    
    def get_notifications_by_recipient(self, recipient_id: str, 
                                     limit: int = 50, offset: int = 0) -> List[NotificationModel]:
        """Get notifications for a specific recipient"""
        return self.session.query(NotificationModel).filter(
            NotificationModel.recipient_id == recipient_id
        ).order_by(desc(NotificationModel.created_at)).offset(offset).limit(limit).all()
    
    def get_failed_notifications_for_retry(self, retry_after_minutes: int = 5) -> List[NotificationModel]:
        """Get failed notifications eligible for retry"""
        retry_time = datetime.utcnow() - timedelta(minutes=retry_after_minutes)
        
        return self.session.query(NotificationModel).filter(
            NotificationModel.status == NotificationStatus.FAILED,
            NotificationModel.attempts < NotificationModel.max_attempts,
            or_(
                NotificationModel.last_attempt_at.is_(None),
                NotificationModel.last_attempt_at <= retry_time
            ),
            or_(
                NotificationModel.expires_at.is_(None),
                NotificationModel.expires_at > datetime.utcnow()
            )
        ).all()
    
    def search_notifications(self, filters: Dict[str, Any], 
                           limit: int = 50, offset: int = 0) -> Tuple[List[NotificationModel], int]:
        """Search notifications with filters"""
        query = self.session.query(NotificationModel)
        
        # Apply filters
        if filters.get('recipient_id'):
            query = query.filter(NotificationModel.recipient_id == filters['recipient_id'])
        
        if filters.get('notification_type'):
            query = query.filter(NotificationModel.notification_type == filters['notification_type'])
        
        if filters.get('category'):
            query = query.filter(NotificationModel.category == filters['category'])
        
        if filters.get('status'):
            query = query.filter(NotificationModel.status == filters['status'])
        
        if filters.get('priority'):
            query = query.filter(NotificationModel.priority == filters['priority'])
        
        if filters.get('source_service'):
            query = query.filter(NotificationModel.source_service == filters['source_service'])
        
        if filters.get('reference_type'):
            query = query.filter(NotificationModel.reference_type == filters['reference_type'])
        
        if filters.get('reference_id'):
            query = query.filter(NotificationModel.reference_id == filters['reference_id'])
        
        if filters.get('date_from'):
            query = query.filter(NotificationModel.created_at >= filters['date_from'])
        
        if filters.get('date_to'):
            query = query.filter(NotificationModel.created_at <= filters['date_to'])
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        notifications = query.order_by(desc(NotificationModel.created_at)).offset(offset).limit(limit).all()
        
        return notifications, total_count
    
    def delete_old_notifications(self, days_old: int = 90) -> int:
        """Delete old notifications to manage storage"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted_count = self.session.query(NotificationModel).filter(
            NotificationModel.created_at < cutoff_date,
            NotificationModel.status.in_([NotificationStatus.DELIVERED, NotificationStatus.CANCELLED])
        ).delete()
        
        self.session.commit()
        return deleted_count


class SQLNotificationTemplateRepository:
    """SQL implementation of notification template repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_template(self, template_data: Dict[str, Any]) -> NotificationTemplateModel:
        """Create a new notification template"""
        try:
            template = NotificationTemplateModel(
                template_id=template_data['template_id'],
                name=template_data['name'],
                description=template_data.get('description'),
                category=NotificationCategory(template_data['category']),
                notification_type=NotificationType(template_data['notification_type']),
                title_template=template_data.get('title_template'),
                message_template=template_data['message_template'],
                html_template=template_data.get('html_template'),
                default_priority=NotificationPriority(template_data.get('default_priority', 'normal')),
                max_attempts=template_data.get('max_attempts', 3),
                retry_delay_minutes=template_data.get('retry_delay_minutes', 5),
                expiry_hours=template_data.get('expiry_hours', 24),
                variables=template_data.get('variables'),
                validation_schema=template_data.get('validation_schema'),
                version=template_data.get('version', '1.0'),
                created_by=template_data.get('created_by')
            )
            
            self.session.add(template)
            self.session.commit()
            self.session.refresh(template)
            return template
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error creating template: {str(e)}")
    
    def get_template_by_id(self, template_id: str) -> Optional[NotificationTemplateModel]:
        """Get template by ID"""
        return self.session.query(NotificationTemplateModel).filter(
            NotificationTemplateModel.template_id == template_id,
            NotificationTemplateModel.is_active == True
        ).first()
    
    def get_templates_by_category(self, category: NotificationCategory, 
                                notification_type: Optional[NotificationType] = None) -> List[NotificationTemplateModel]:
        """Get templates by category"""
        query = self.session.query(NotificationTemplateModel).filter(
            NotificationTemplateModel.category == category,
            NotificationTemplateModel.is_active == True
        )
        
        if notification_type:
            query = query.filter(NotificationTemplateModel.notification_type == notification_type)
        
        return query.all()
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Update template"""
        try:
            template = self.get_template_by_id(template_id)
            if not template:
                return False
            
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = datetime.utcnow()
            self.session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error updating template: {str(e)}")


class SQLNotificationDeliveryLogRepository:
    """SQL implementation of notification delivery log repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_delivery_log(self, log_data: Dict[str, Any]) -> NotificationDeliveryLogModel:
        """Create a new delivery log entry"""
        try:
            log_entry = NotificationDeliveryLogModel(
                notification_id=log_data['notification_id'],
                attempt_number=log_data['attempt_number'],
                delivery_status=NotificationStatus(log_data['delivery_status']),
                provider_name=log_data.get('provider_name'),
                provider_message_id=log_data.get('provider_message_id'),
                provider_response=log_data.get('provider_response'),
                sent_at=log_data.get('sent_at'),
                delivered_at=log_data.get('delivered_at'),
                response_time_ms=log_data.get('response_time_ms'),
                error_code=log_data.get('error_code'),
                error_message=log_data.get('error_message'),
                retry_after=log_data.get('retry_after'),
                delivery_cost=log_data.get('delivery_cost'),
                currency=log_data.get('currency', 'INR')
            )
            
            self.session.add(log_entry)
            self.session.commit()
            self.session.refresh(log_entry)
            return log_entry
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error creating delivery log: {str(e)}")
    
    def get_delivery_logs_by_notification(self, notification_id: uuid.UUID) -> List[NotificationDeliveryLogModel]:
        """Get delivery logs for a notification"""
        return self.session.query(NotificationDeliveryLogModel).filter(
            NotificationDeliveryLogModel.notification_id == notification_id
        ).order_by(desc(NotificationDeliveryLogModel.created_at)).all()
    
    def get_delivery_statistics(self, date_from: datetime, date_to: datetime, 
                              provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Get delivery statistics for a date range"""
        query = self.session.query(NotificationDeliveryLogModel).filter(
            NotificationDeliveryLogModel.created_at.between(date_from, date_to)
        )
        
        if provider_name:
            query = query.filter(NotificationDeliveryLogModel.provider_name == provider_name)
        
        logs = query.all()
        
        total_attempts = len(logs)
        successful_deliveries = sum(1 for log in logs if log.delivery_status == NotificationStatus.DELIVERED)
        failed_deliveries = sum(1 for log in logs if log.delivery_status == NotificationStatus.FAILED)
        
        total_cost = sum(log.delivery_cost or 0 for log in logs)
        
        response_times = [log.response_time_ms for log in logs if log.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'total_attempts': total_attempts,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'success_rate': (successful_deliveries / total_attempts * 100) if total_attempts > 0 else 0,
            'total_cost': float(total_cost),
            'average_response_time_ms': avg_response_time
        }


class SQLNotificationPreferenceRepository:
    """SQL implementation of notification preference repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_or_update_preferences(self, preference_data: Dict[str, Any]) -> NotificationPreferenceModel:
        """Create or update user notification preferences"""
        try:
            # Check if preferences already exist
            existing = self.session.query(NotificationPreferenceModel).filter(
                NotificationPreferenceModel.user_id == preference_data['user_id'],
                NotificationPreferenceModel.user_type == preference_data.get('user_type', 'customer')
            ).first()
            
            if existing:
                # Update existing preferences
                for key, value in preference_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                preference = existing
            else:
                # Create new preferences
                preference = NotificationPreferenceModel(**preference_data)
                self.session.add(preference)
            
            self.session.commit()
            self.session.refresh(preference)
            return preference
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error creating/updating preferences: {str(e)}")
    
    def get_user_preferences(self, user_id: str, user_type: str = 'customer') -> Optional[NotificationPreferenceModel]:
        """Get user notification preferences"""
        return self.session.query(NotificationPreferenceModel).filter(
            NotificationPreferenceModel.user_id == user_id,
            NotificationPreferenceModel.user_type == user_type
        ).first()
    
    def is_notification_allowed(self, user_id: str, category: NotificationCategory, 
                              notification_type: NotificationType) -> bool:
        """Check if notification is allowed based on user preferences"""
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            return True  # Default to allowing notifications
        
        # Check channel preference
        channel_enabled = True
        if notification_type == NotificationType.SMS:
            channel_enabled = preferences.sms_enabled
        elif notification_type == NotificationType.EMAIL:
            channel_enabled = preferences.email_enabled
        elif notification_type == NotificationType.PUSH:
            channel_enabled = preferences.push_enabled
        elif notification_type == NotificationType.IN_APP:
            channel_enabled = preferences.in_app_enabled
        
        if not channel_enabled:
            return False
        
        # Check category preference
        category_enabled = True
        if category == NotificationCategory.TRANSACTION:
            category_enabled = preferences.transaction_notifications
        elif category == NotificationCategory.ACCOUNT:
            category_enabled = preferences.account_notifications
        elif category == NotificationCategory.SECURITY:
            category_enabled = preferences.security_notifications
        elif category == NotificationCategory.PAYMENT:
            category_enabled = preferences.payment_notifications
        elif category == NotificationCategory.LOAN:
            category_enabled = preferences.loan_notifications
        elif category == NotificationCategory.MARKETING:
            category_enabled = preferences.marketing_notifications
        elif category == NotificationCategory.SYSTEM:
            category_enabled = preferences.system_notifications
        
        return category_enabled


class SQLNotificationChannelRepository:
    """SQL implementation of notification channel repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_active_channels_by_type(self, notification_type: NotificationType) -> List[NotificationChannelModel]:
        """Get active channels for notification type"""
        return self.session.query(NotificationChannelModel).filter(
            NotificationChannelModel.channel_type == notification_type,
            NotificationChannelModel.is_active == True
        ).order_by(asc(NotificationChannelModel.priority_order)).all()
    
    def get_default_channel(self, notification_type: NotificationType) -> Optional[NotificationChannelModel]:
        """Get default channel for notification type"""
        return self.session.query(NotificationChannelModel).filter(
            NotificationChannelModel.channel_type == notification_type,
            NotificationChannelModel.is_active == True,
            NotificationChannelModel.is_default == True
        ).first()
    
    def update_channel_health(self, channel_id: str, health_status: str, 
                            error_rate: float) -> bool:
        """Update channel health status"""
        try:
            channel = self.session.query(NotificationChannelModel).filter(
                NotificationChannelModel.channel_id == channel_id
            ).first()
            
            if channel:
                channel.health_status = health_status
                channel.error_rate_percentage = error_rate
                channel.last_health_check = datetime.utcnow()
                self.session.commit()
                return True
            
            return False
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Error updating channel health: {str(e)}")


# Export all repositories
__all__ = [
    'SQLNotificationRepository',
    'SQLNotificationTemplateRepository', 
    'SQLNotificationDeliveryLogRepository',
    'SQLNotificationPreferenceRepository',
    'SQLNotificationChannelRepository'
]
