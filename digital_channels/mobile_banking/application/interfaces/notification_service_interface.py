"""
Notification service interface for the Mobile Banking domain.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any
from uuid import UUID

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class NotificationType(Enum):
    """Types of notifications that can be sent."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    TRANSACTION_SUCCESS = "transaction_success"
    TRANSACTION_FAILURE = "transaction_failure"
    PASSWORD_CHANGE = "password_change"
    SECURITY_ALERT = "security_alert"
    SESSION_EXPIRED = "session_expired"
    NEW_DEVICE_LOGIN = "new_device_login"


class NotificationServiceInterface(ABC):
    """Interface for notification service operations."""
    
    @abstractmethod
    def send_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        details: Dict[str, Any],
        delivery_channel: str = "sms"
    ) -> bool:
        """
        Send a notification to a user.
        
        Args:
            user_id: The ID of the user to notify
            notification_type: The type of notification to send
            details: Details about the notification
            delivery_channel: The channel to deliver the notification through (sms, email, push)
            
        Returns:
            True if notification was sent, False otherwise
        """
        pass
    
    @abstractmethod
    def send_sms(
        self,
        phone_number: str,
        message: str
    ) -> bool:
        """
        Send an SMS to a phone number.
        
        Args:
            phone_number: The phone number to send to
            message: The message to send
            
        Returns:
            True if SMS was sent, False otherwise
        """
        pass
    
    @abstractmethod
    def send_push_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Dict[str, Any] = None
    ) -> bool:
        """
        Send a push notification to a device.
        
        Args:
            device_token: The device token to send to
            title: The title of the notification
            body: The body of the notification
            data: Additional data to include
            
        Returns:
            True if push notification was sent, False otherwise
        """
        pass
    
    @abstractmethod
    def send_email(
        self,
        email_address: str,
        subject: str,
        body: str,
        html_body: str = None,
        attachments: Dict[str, bytes] = None
    ) -> bool:
        """
        Send an email to an email address.
        
        Args:
            email_address: The email address to send to
            subject: The subject of the email
            body: The plaintext body of the email
            html_body: The HTML body of the email
            attachments: A dictionary of attachment names to attachment content
            
        Returns:
            True if email was sent, False otherwise
        """
        pass
