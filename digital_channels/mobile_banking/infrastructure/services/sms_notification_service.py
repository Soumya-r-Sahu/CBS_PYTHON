"""
SMS notification service implementation for Mobile Banking.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
import requests

from ...application.interfaces.notification_service_interface import NotificationServiceInterface, NotificationType
from ...application.interfaces.mobile_user_repository_interface import MobileUserRepositoryInterface


class SMSNotificationService(NotificationServiceInterface):
    """SMS implementation of the notification service."""
    
    def __init__(
        self, 
        user_repository: MobileUserRepositoryInterface,
        api_key: str,
        sender_id: str,
        use_mock: bool = False
    ):
        """
        Initialize the service.
        
        Args:
            user_repository: Repository for user operations
            api_key: API key for SMS service
            sender_id: Sender ID for SMS messages
            use_mock: Whether to use mock implementation
        """
        self._user_repository = user_repository
        self._api_key = api_key
        self._sender_id = sender_id
        self._use_mock = use_mock
        self._logger = logging.getLogger(__name__)
    
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
        if delivery_channel != "sms":
            self._logger.warning(f"Requested channel {delivery_channel} not supported by SMSNotificationService")
            return False
        
        # Get the user
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            self._logger.error(f"User not found for notification: {user_id}")
            return False
        
        # Get the user's mobile number
        phone_number = user.mobile_number
        if not phone_number:
            self._logger.error(f"No mobile number found for user: {user_id}")
            return False
        
        # Generate message from template
        message = self._generate_message(notification_type, details, user.full_name)
        
        # Send the SMS
        return self.send_sms(phone_number, message)
    
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
        # Log the message
        self._logger.info(f"Sending SMS to {phone_number}: {message}")
        
        # If using mock implementation, just log and return success
        if self._use_mock:
            self._logger.info("Using mock SMS implementation")
            return True
        
        # In a real implementation, would call an SMS API
        try:
            # Example SMS API call (not actual implementation)
            response = requests.post(
                "https://api.smsgateway.com/send",
                json={
                    "apiKey": self._api_key,
                    "senderId": self._sender_id,
                    "to": phone_number,
                    "message": message
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") == "success":
                self._logger.info(f"SMS sent successfully to {phone_number}")
                return True
            else:
                self._logger.error(f"Failed to send SMS: {result.get('error')}")
                return False
                
        except Exception as e:
            self._logger.error(f"Exception sending SMS: {str(e)}")
            return False
    
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
        self._logger.warning("Push notifications not implemented in SMSNotificationService")
        return False
    
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
        self._logger.warning("Email notifications not implemented in SMSNotificationService")
        return False
    
    def _generate_message(
        self, 
        notification_type: NotificationType, 
        details: Dict[str, Any],
        user_name: str
    ) -> str:
        """
        Generate a message from a template.
        
        Args:
            notification_type: The type of notification
            details: Details about the notification
            user_name: The name of the user
            
        Returns:
            The generated message
        """
        # Notification templates
        templates = {
            NotificationType.LOGIN_SUCCESS: 
                f"Dear {user_name}, you have successfully logged in to your Mobile Banking account at {details.get('time', 'now')}. "
                f"If this wasn't you, please contact us immediately.",
            
            NotificationType.LOGIN_FAILURE:
                f"Dear {user_name}, there was a failed login attempt on your Mobile Banking account at {details.get('time', 'now')}. "
                f"If this wasn't you, please ignore this message.",
            
            NotificationType.TRANSACTION_SUCCESS:
                f"Dear {user_name}, your transaction of {details.get('amount', 0)} with reference {details.get('reference_number', 'N/A')} "
                f"has been successfully processed at {details.get('time', 'now')}.",
            
            NotificationType.TRANSACTION_FAILURE:
                f"Dear {user_name}, your transaction of {details.get('amount', 0)} with reference {details.get('reference_number', 'N/A')} "
                f"has failed at {details.get('time', 'now')}. Reason: {details.get('reason', 'Unknown')}",
            
            NotificationType.PASSWORD_CHANGE:
                f"Dear {user_name}, your Mobile Banking password was changed at {details.get('time', 'now')}. "
                f"If this wasn't you, please contact us immediately.",
            
            NotificationType.SECURITY_ALERT:
                f"Security Alert: {details.get('message', 'There is a security alert on your account.')}",
            
            NotificationType.SESSION_EXPIRED:
                f"Dear {user_name}, your Mobile Banking session has expired at {details.get('time', 'now')}. "
                f"Please log in again to continue.",
            
            NotificationType.NEW_DEVICE_LOGIN:
                f"Dear {user_name}, a new device was used to log in to your Mobile Banking account at {details.get('time', 'now')}. "
                f"Device: {details.get('device', 'Unknown')}. If this wasn't you, please contact us immediately."
        }
        
        # Get the template for this notification type
        template = templates.get(notification_type, "Notification from your bank.")
        
        # Add standard footer
        footer = "\nCBS Mobile Banking. Do not reply to this message."
        
        return template + footer
