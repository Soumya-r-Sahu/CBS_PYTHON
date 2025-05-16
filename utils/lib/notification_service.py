"""
Notification Service

Provides functionality for sending notifications via various channels (email, SMS, push notifications).
Used by the Core Banking System for alerts and notifications.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for sending notifications through various channels
    """
    
    def __init__(self):
        """Initialize notification service"""
        logger.info("Notification service initialized")
    
    def send_email(self, recipient: str, subject: str, message: str, 
                  attachments: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send email notification
        
        Args:
            recipient: Email address of the recipient
            subject: Email subject
            message: Email body
            attachments: Optional dictionary of attachments
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            # Mock implementation - in real system this would send actual emails
            logger.info(f"EMAIL to {recipient}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Send SMS notification
        
        Args:
            phone_number: Recipient phone number
            message: SMS message content
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            # Mock implementation - in real system this would send actual SMS
            logger.info(f"SMS to {phone_number}: {message[:20]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False
    
    def send_push_notification(self, user_id: str, title: str, 
                             message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send push notification
        
        Args:
            user_id: User ID to send notification to
            title: Notification title
            message: Notification message
            data: Optional data payload
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            # Mock implementation - in real system this would send actual push notification
            logger.info(f"PUSH to {user_id}: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {str(e)}")
            return False
    
    def send_transaction_alert(self, customer_data: Dict[str, Any], 
                             transaction_data: Dict[str, Any]) -> bool:
        """
        Send transaction alert via appropriate channels based on customer preferences
        
        Args:
            customer_data: Customer contact information and preferences
            transaction_data: Transaction details
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            success = False
            
            # Format the transaction message
            account = transaction_data.get('account_number', '')[-4:] 
            tx_type = transaction_data.get('type', 'Transaction')
            amount = transaction_data.get('amount', 0)
            balance = transaction_data.get('balance', 0)
            
            # Email notification
            if customer_data.get('email'):
                email = customer_data['email']
                subject = f"Transaction Alert: {tx_type}"
                message = f"""
                Transaction Type: {tx_type}
                Account: XXXX{account}
                Amount: {amount}
                Date/Time: {transaction_data.get('timestamp', '')}
                Available Balance: {balance}
                """
                email_sent = self.send_email(email, subject, message)
                success = success or email_sent
            
            # SMS notification
            if customer_data.get('phone_number'):
                phone = customer_data['phone_number']
                message = f"Alert: {tx_type} of {amount} on Acc XXXX{account}. Bal: {balance}. {transaction_data.get('timestamp', '')[:10]}"
                sms_sent = self.send_sms(phone, message)
                success = success or sms_sent
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send transaction alert: {str(e)}")
            return False


# Singleton instance
notification_service = NotificationService()
