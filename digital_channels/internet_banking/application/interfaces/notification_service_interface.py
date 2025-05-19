"""
Notification service interface for the Internet Banking domain.
This interface defines methods for sending notifications to users.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class NotificationType(Enum):
    """Types of notifications that can be sent."""
    LOGIN_ALERT = "login_alert"
    SECURITY_ALERT = "security_alert"
    PASSWORD_RESET = "password_reset"
    TRANSACTION_CONFIRMATION = "transaction_confirmation"
    FEATURE_ANNOUNCEMENT = "feature_announcement"
    ACCOUNT_UPDATE = "account_update"


class NotificationServiceInterface(ABC):
    """Interface for notification operations."""
    
    @abstractmethod
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        message: str,
        notification_type: NotificationType,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            message: Email message content
            notification_type: Type of notification being sent
            template_id: Optional template identifier
            template_data: Optional data for template rendering
            
        Returns:
            Boolean indicating if the email was sent successfully
        """
        pass
    
    @abstractmethod
    def send_sms(
        self, 
        phone_number: str, 
        message: str,
        notification_type: NotificationType
    ) -> bool:
        """
        Send an SMS notification.
        
        Args:
            phone_number: Recipient phone number
            message: SMS message content
            notification_type: Type of notification being sent
            
        Returns:
            Boolean indicating if the SMS was sent successfully
        """
        pass
    
    @abstractmethod
    def send_push_notification(
        self, 
        device_token: str, 
        title: str,
        message: str,
        notification_type: NotificationType,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a push notification.
        
        Args:
            device_token: Device token for push notification
            title: Notification title
            message: Notification message
            notification_type: Type of notification being sent
            additional_data: Optional additional data for the notification
            
        Returns:
            Boolean indicating if the notification was sent successfully
        """
        pass
