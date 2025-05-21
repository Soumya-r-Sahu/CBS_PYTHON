"""
Notification Service for Mobile Banking API

Handles sending various types of notifications to customers
"""

import logging
from typing import Dict, Any, Optional, List
from database.python.common.database_operations import DatabaseConnection
import datetime
import json


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
# Set up logging
logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for sending notifications to customers
    """
    
    def __init__(self, database_connection):
        """
        Initialize the notification service
        
        Args:
            database_connection: Database connection object
        """
        self.database_connection = database_connection
        
    def send_transaction_notification(self, customer_id: str, data: Dict[str, Any]) -> bool:
        """
        Send transaction notification to customer
        
        Args:
            customer_id: Customer's unique identifier
            data: Transaction data
            
        Returns:
            bool: Success status
        """
        message = self._build_transaction_message(data)
        
        return self.send_notification(
            customer_id=customer_id,
            notification_type="TRANSACTION",
            message=message,
            channel="SMS",
            data=data
        )
        
    def send_upi_notification(self, customer_id: str, data: Dict[str, Any]) -> bool:
        """
        Send UPI transaction notification to customer
        
        Args:
            customer_id: Customer's unique identifier
            data: UPI transaction data
            
        Returns:
            bool: Success status
        """
        message = self._build_upi_message(data)
        
        return self.send_notification(
            customer_id=customer_id,
            notification_type="UPI_TRANSACTION",
            message=message,
            channel="SMS",
            data=data
        )
        
    def send_security_alert(self, customer_id: str, data: Dict[str, Any]) -> bool:
        """
        Send security alert notification to customer
        
        Args:
            customer_id: Customer's unique identifier
            data: Security alert data
            
        Returns:
            bool: Success status
        """
        message = self._build_security_message(data)
        
        return self.send_notification(
            customer_id=customer_id,
            notification_type="SECURITY_ALERT",
            message=message,
            channel="EMAIL",  # Security alerts go to email by default
            data=data
        )
        
    def send_notification(self, customer_id: str, notification_type: str,
                        message: str, channel: str = "SMS",
                        data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send notification to customer
        
        Args:
            customer_id: Customer's unique identifier
            notification_type: Type of notification
            message: Notification message
            channel: Notification channel (SMS, EMAIL, PUSH)
            data: Additional data for the notification
            
        Returns:
            bool: Success status
        """
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor()
            
            # Get internal customer ID from customer_id
            cursor.execute(
                """
                SELECT id FROM customers
                WHERE customer_id = %s
                """,
                (customer_id,)
            )
            
            result = cursor.fetchone()
            if not result:
                logger.error(f"Customer not found for notification: {customer_id}")
                return False
                
            internal_customer_id = result[0]
            
            # Record notification
            cursor.execute(
                """
                INSERT INTO notifications
                (customer_id, notification_type, message, channel, data, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    internal_customer_id,
                    notification_type,
                    message,
                    channel,
                    json.dumps(data) if data else None,
                    "SENT"
                )
            )
            
            conn.commit()
            
            # In a real implementation, we would integrate with SMS/email/push services
            logger.info(f"Notification sent to {customer_id} via {channel}: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
            
    def _build_transaction_message(self, data: Dict[str, Any]) -> str:
        """
        Build transaction notification message
        
        Args:
            data: Transaction data
            
        Returns:
            str: Formatted message
        """
        transaction_type = data.get('transaction_type', '')
        amount = data.get('amount', 0)
        account = data.get('account_number', '')
        
        if 'DEBIT' in transaction_type or 'WITHDRAWAL' in transaction_type:
            return f"INR {amount} debited from your account {self._mask_account(account)}. Balance: INR {data.get('balance_after', 0)}"
        elif 'CREDIT' in transaction_type or 'DEPOSIT' in transaction_type:
            return f"INR {amount} credited to your account {self._mask_account(account)}. Balance: INR {data.get('balance_after', 0)}"
        else:
            return f"Transaction of INR {amount} processed for your account {self._mask_account(account)}. Ref: {data.get('reference_number', '')}"
            
    def _build_upi_message(self, data: Dict[str, Any]) -> str:
        """
        Build UPI notification message
        
        Args:
            data: UPI transaction data
            
        Returns:
            str: Formatted message
        """
        amount = data.get('amount', 0)
        sender = data.get('sender_upi_id', '')
        receiver = data.get('receiver_upi_id', '')
        
        if 'sender_upi_id' in data and data.get('is_debit', False):
            return f"UPI Payment: INR {amount} sent to {receiver}. Ref: {data.get('reference_number', '')}"
        elif 'receiver_upi_id' in data and not data.get('is_debit', True):
            return f"UPI Payment: INR {amount} received from {sender}. Ref: {data.get('reference_number', '')}"
        else:
            return f"UPI Transaction: INR {amount} processed. Ref: {data.get('reference_number', '')}"
            
    def _build_security_message(self, data: Dict[str, Any]) -> str:
        """
        Build security notification message
        
        Args:
            data: Security alert data
            
        Returns:
            str: Formatted message
        """
        alert_type = data.get('alert_type', '')
        
        if alert_type == 'LOGIN_ATTEMPT':
            return f"Security Alert: Login attempt from new device detected at {data.get('timestamp', '')}."
        elif alert_type == 'PASSWORD_CHANGE':
            return f"Your password was changed at {data.get('timestamp', '')}. If this wasn't you, please contact customer service."
        elif alert_type == 'PIN_CHANGE':
            return f"Your {data.get('pin_type', 'PIN')} was changed at {data.get('timestamp', '')}. If this wasn't you, please contact customer service."
        else:
            return f"Security Alert: Unusual activity detected on your account. Please review your recent transactions."
            
    def _mask_account(self, account_number: str) -> str:
        """
        Mask account number for security
        
        Args:
            account_number: Full account number
            
        Returns:
            str: Masked account number
        """
        if not account_number or len(account_number) < 6:
            return account_number
            
        return f"XX{account_number[-4:]}"
