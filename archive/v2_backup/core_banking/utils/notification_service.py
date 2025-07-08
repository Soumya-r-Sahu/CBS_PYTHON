"""
Notification Service

Handles sending notifications to customers through various channels.
"""

import logging
from typing import Optional, Dict, Any, List

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications to customers via various channels"""
    
    def __init__(self):
        """Initialize the notification service"""
        self.sms_enabled = True
        self.email_enabled = True
        self.push_enabled = True
    
    def send_email(self, recipient: str, subject: str, message: str, 
                 attachments: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Send an email notification
        
        Args:
            recipient: Email address of the recipient
            subject: Email subject
            message: Email message body
            attachments: Optional list of attachments
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            if not recipient or not self.email_enabled:
                return False
                
            # In a real implementation, this would use an email service
            logger.info(f"Sending email to {recipient}: {subject}")
            
            # Simulate email sending
            logger.debug(f"Email content: {message}")
            if attachments:
                logger.debug(f"With {len(attachments)} attachments")
            
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Send an SMS notification
        
        Args:
            phone_number: Recipient's phone number
            message: SMS message content
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            if not phone_number or not self.sms_enabled:
                return False
                
            # In a real implementation, this would use an SMS gateway
            logger.info(f"Sending SMS to {phone_number}")
            logger.debug(f"SMS content: {message}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False
    
    def send_push_notification(self, device_token: str, title: str, 
                             body: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a push notification
        
        Args:
            device_token: Device token for push notification
            title: Notification title
            body: Notification body
            data: Optional data payload
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            if not device_token or not self.push_enabled:
                return False
                
            # In a real implementation, this would use a push notification service
            logger.info(f"Sending push notification to device {device_token}")
            logger.debug(f"Title: {title}, Body: {body}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to send push notification: {str(e)}")
            return False

# Create a singleton instance
notification_service = NotificationService()
