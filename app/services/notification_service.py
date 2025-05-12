"""
Core Banking System Unified Notification Service

A comprehensive notification service that handles various notifications to customers
through different channels (SMS, Email, Push Notifications) with proper tracking,
formatting, and delivery mechanisms.

The service follows a singleton pattern and supports:
- Transaction notifications
- Security alerts
- Card-related notifications
- Account-related notifications
- UPI transaction notifications
- Marketing and promotional notifications
- Service notifications
"""

import logging
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from enum import Enum
from functools import wraps

from app.config.config_loader import config
from database.connection import DatabaseConnection
from app.lib.id_generator import generate_notification_id

# Set up logging
logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Notification channels"""
    SMS = "SMS"
    EMAIL = "EMAIL"
    PUSH = "PUSH"
    ALL = "ALL"  # For sending via all available channels

class NotificationType(Enum):
    """Types of notifications"""
    TRANSACTION = "TRANSACTION"
    SECURITY = "SECURITY"
    ACCOUNT = "ACCOUNT"
    CARD = "CARD"
    UPI = "UPI"
    MARKETING = "MARKETING"
    SERVICE = "SERVICE"

class NotificationPriority(Enum):
    """Priority levels for notifications"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class NotificationStatus(Enum):
    """Status of the notification"""
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    READ = "READ"

def log_notification(func):
    """Decorator to log notification attempts"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            notification_type = kwargs.get('notification_type', 'UNKNOWN')
            customer_id = kwargs.get('customer_id', 'UNKNOWN')
            channel = kwargs.get('channel', 'UNKNOWN')
            
            logger.info(f"Sending {notification_type} notification to {customer_id} via {channel}")
            result = func(*args, **kwargs)
            
            if result:
                logger.info(f"Successfully sent {notification_type} notification to {customer_id} via {channel}")
            else:
                logger.warning(f"Failed to send {notification_type} notification to {customer_id} via {channel}")
                
            return result
        except Exception as e:
            logger.error(f"Error in notification function {func.__name__}: {str(e)}")
            # Re-raise the exception for the caller to handle
            raise
            
    return wrapper

class NotificationService:
    """
    Comprehensive service for sending and tracking notifications to customers
    Implementation follows the Singleton pattern
    """
    
    _instance = None
    
    def __new__(cls, database_connection=None):
        """Ensure only one instance of NotificationService exists"""
        if cls._instance is None:
            cls._instance = super(NotificationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, database_connection=None):
        """
        Initialize the notification service
        
        Args:
            database_connection: Database connection object (optional)
        """
        # Only initialize once
        if self._initialized:
            return
            
        self._initialized = True
        
        # Initialize database connection
        self.database_connection = database_connection or DatabaseConnection()
        
        # Email configuration
        self.email_config = {
            'smtp_server': config.get('notifications.email.smtp_server', 'smtp.example.com'),
            'smtp_port': config.get('notifications.email.smtp_port', 587),
            'sender_email': config.get('notifications.email.sender_email', 'noreply@bank.com'),
            'sender_name': config.get('notifications.email.sender_name', 'Core Banking System'),
            'username': config.get('notifications.email.username', ''),
            'password': config.get('notifications.email.password', '')
        }
        
        # SMS configuration
        self.sms_config = {
            'api_url': config.get('notifications.sms.api_url', ''),
            'api_key': config.get('notifications.sms.api_key', ''),
            'sender_id': config.get('notifications.sms.sender_id', 'BANKID')
        }
        
        # Push notification configuration
        self.push_config = {
            'api_url': config.get('notifications.push.api_url', ''),
            'api_key': config.get('notifications.push.api_key', ''),
            'app_id': config.get('notifications.push.app_id', '')
        }
        
        # Notification template configuration
        self.template_config = {
            'use_templates': config.get('notifications.templates.enabled', False),
            'template_dir': config.get('notifications.templates.directory', 'templates/notifications')
        }
        
        # Settings for notification channels
        self.settings = {
            'high_priority_channels': [NotificationChannel.SMS, NotificationChannel.PUSH],
            'critical_priority_channels': [NotificationChannel.SMS, NotificationChannel.EMAIL, NotificationChannel.PUSH],
            'default_channel': NotificationChannel.SMS,
            'retry_failed': config.get('notifications.retry_failed', True),
            'max_retries': config.get('notifications.max_retries', 3),
            'store_notifications': config.get('notifications.store_in_db', True)
        }
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
    
    def send_transaction_notification(self, 
                                    customer_id: str, 
                                    data: Dict[str, Any],
                                    channel: Union[str, NotificationChannel] = None) -> bool:
        """
        Send a transaction notification to a customer
        
        Args:
            customer_id: Customer's unique identifier
            data: Transaction data containing details like amount, type, account number
            channel: Notification channel to use
            
        Returns:
            bool: Success status
        """
        # Determine message and notification data
        message = self._build_transaction_message(data)
        notification_data = {
            'customer_id': customer_id,
            'notification_type': NotificationType.TRANSACTION.value,
            'message': message,
            'channel': channel or self.settings['default_channel'].value,
            'priority': self._determine_transaction_priority(data),
            'data': data
        }
        
        # Send notification through appropriate channel(s)
        return self.send_notification(**notification_data)
    
    def send_security_alert(self, 
                          customer_id: str, 
                          data: Dict[str, Any],
                          channel: Union[str, NotificationChannel] = NotificationChannel.EMAIL.value) -> bool:
        """
        Send a security alert notification to a customer
        
        Args:
            customer_id: Customer's unique identifier
            data: Security alert data
            channel: Notification channel to use
            
        Returns:
            bool: Success status
        """
        # Security alerts are high priority
        priority = NotificationPriority.HIGH.value
        if data.get('alert_type') in ['UNAUTHORIZED_ACCESS', 'FRAUD_DETECTION']:
            priority = NotificationPriority.CRITICAL.value
        
        message = self._build_security_message(data)
        notification_data = {
            'customer_id': customer_id,
            'notification_type': NotificationType.SECURITY.value,
            'message': message,
            'channel': channel,
            'priority': priority,
            'data': data
        }
        
        # For critical security alerts, send through all channels
        if priority == NotificationPriority.CRITICAL.value:
            notification_data['channel'] = NotificationChannel.ALL.value
        
        return self.send_notification(**notification_data)
    
    def send_account_notification(self, 
                               customer_id: str, 
                               data: Dict[str, Any],
                               channel: Union[str, NotificationChannel] = None) -> bool:
        """
        Send an account-related notification to a customer
        
        Args:
            customer_id: Customer's unique identifier
            data: Account notification data
            channel: Notification channel to use
            
        Returns:
            bool: Success status
        """
        message = self._build_account_message(data)
        notification_data = {
            'customer_id': customer_id,
            'notification_type': NotificationType.ACCOUNT.value,
            'message': message,
            'channel': channel or self.settings['default_channel'].value,
            'priority': self._determine_account_priority(data),
            'data': data
        }
        
        return self.send_notification(**notification_data)
    
    def send_card_notification(self, 
                            customer_id: str, 
                            data: Dict[str, Any],
                            channel: Union[str, NotificationChannel] = None) -> bool:
        """
        Send a card-related notification to a customer
        
        Args:
            customer_id: Customer's unique identifier
            data: Card notification data
            channel: Notification channel to use
            
        Returns:
            bool: Success status
        """
        message = self._build_card_message(data)
        notification_data = {
            'customer_id': customer_id,
            'notification_type': NotificationType.CARD.value,
            'message': message,
            'channel': channel or self.settings['default_channel'].value,
            'priority': self._determine_card_priority(data),
            'data': data
        }
        
        return self.send_notification(**notification_data)
    
    def send_upi_notification(self, 
                           customer_id: str, 
                           data: Dict[str, Any],
                           channel: Union[str, NotificationChannel] = None) -> bool:
        """
        Send a UPI transaction notification to a customer
        
        Args:
            customer_id: Customer's unique identifier
            data: UPI notification data
            channel: Notification channel to use
            
        Returns:
            bool: Success status
        """
        message = self._build_upi_message(data)
        notification_data = {
            'customer_id': customer_id,
            'notification_type': NotificationType.UPI.value,
            'message': message,
            'channel': channel or self.settings['default_channel'].value,
            'priority': NotificationPriority.MEDIUM.value,
            'data': data
        }
        
        return self.send_notification(**notification_data)
    
    @log_notification
    def send_notification(self,
                        customer_id: str,
                        notification_type: str,
                        message: str,
                        channel: str = NotificationChannel.SMS.value,
                        priority: str = NotificationPriority.MEDIUM.value,
                        data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send notification to customer through specified channel
        
        Args:
            customer_id: Customer's unique identifier
            notification_type: Type of notification
            message: Notification message
            channel: Notification channel (SMS, EMAIL, PUSH)
            priority: Notification priority
            data: Additional data for the notification
            
        Returns:
            bool: Success status
        """
        try:
            # Get customer contact info from database
            customer_info = self._get_customer_info(customer_id)
            if not customer_info:
                self.logger.error(f"Customer not found for notification: {customer_id}")
                return False
            
            # Generate notification ID for tracking
            notification_id = generate_notification_id()
            
            # Store notification in database
            if self.settings['store_notifications']:
                self._store_notification(
                    notification_id=notification_id,
                    customer_id=customer_id,
                    notification_type=notification_type,
                    message=message,
                    channel=channel,
                    priority=priority,
                    data=data
                )
            
            # Send notification through all channels if ALL specified
            if channel == NotificationChannel.ALL.value:
                success = False
                
                # Try email
                if customer_info.get('email'):
                    email_success = self._send_email_notification(
                        recipient=customer_info['email'],
                        subject=self._generate_subject(notification_type, data),
                        message=message,
                        notification_type=notification_type,
                        data=data
                    )
                    success = success or email_success
                
                # Try SMS
                if customer_info.get('phone'):
                    sms_success = self._send_sms_notification(
                        phone_number=customer_info['phone'],
                        message=message
                    )
                    success = success or sms_success
                
                # Try push notification
                if customer_info.get('device_token'):
                    push_success = self._send_push_notification(
                        device_token=customer_info['device_token'],
                        title=self._generate_subject(notification_type, data),
                        message=message,
                        data=data
                    )
                    success = success or push_success
                
                return success
            
            # Send through specified channel
            if channel == NotificationChannel.EMAIL.value:
                if not customer_info.get('email'):
                    self.logger.warning(f"No email address found for customer {customer_id}")
                    return False
                return self._send_email_notification(
                    recipient=customer_info['email'],
                    subject=self._generate_subject(notification_type, data),
                    message=message,
                    notification_type=notification_type,
                    data=data
                )
            
            elif channel == NotificationChannel.SMS.value:
                if not customer_info.get('phone'):
                    self.logger.warning(f"No phone number found for customer {customer_id}")
                    return False
                return self._send_sms_notification(
                    phone_number=customer_info['phone'],
                    message=message
                )
            
            elif channel == NotificationChannel.PUSH.value:
                if not customer_info.get('device_token'):
                    self.logger.warning(f"No device token found for customer {customer_id}")
                    return False
                return self._send_push_notification(
                    device_token=customer_info['device_token'],
                    title=self._generate_subject(notification_type, data),
                    message=message,
                    data=data
                )
            
            else:
                self.logger.error(f"Invalid notification channel: {channel}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def send_transaction_alert(self, customer_data: Dict, transaction_data: Dict) -> bool:
        """
        Backward compatibility method for sending transaction alerts
        
        Args:
            customer_data: Dict containing customer contact information
            transaction_data: Dict containing transaction details
            
        Returns:
            bool: True if at least one notification was sent successfully
        """
        email_sent = False
        sms_sent = False
        
        # Format account number for display
        account_masked = f"XXXX{transaction_data.get('account_number', '')[-4:]}"
        amount = transaction_data.get('amount', 0.0)
        transaction_type = transaction_data.get('type', 'transaction')
        date_time = transaction_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # SMS message
        sms_message = (
            f"INR {amount:.2f} {transaction_type} on A/c {account_masked} on "
            f"{date_time}. Avl Bal INR {transaction_data.get('balance', 0.0):.2f}"
        )
        
        # Email subject and message
        email_subject = f"Transaction Alert - {transaction_type.title()}"
        email_message = (
            f"Dear Customer,\n\n"
            f"A {transaction_type} of INR {amount:.2f} has been made on your account "
            f"ending with {account_masked} on {date_time}.\n\n"
            f"Available Balance: INR {transaction_data.get('balance', 0.0):.2f}\n\n"
            f"If you did not authorize this transaction, please contact our customer "
            f"support immediately.\n\n"
            f"Thank you,\nBank Team"
        )
        
        # Send notifications
        if 'email' in customer_data and customer_data.get('email'):
            email_sent = self._send_email_notification(
                recipient=customer_data['email'], 
                subject=email_subject, 
                message=email_message
            )
        
        if 'phone_number' in customer_data and customer_data.get('phone_number'):
            sms_sent = self._send_sms_notification(
                phone_number=customer_data['phone_number'], 
                message=sms_message
            )
        
        return email_sent or sms_sent

    def _send_email_notification(self, recipient: str, subject: str, message: str,
                               html_message: Optional[str] = None,
                               notification_type: Optional[str] = None,
                               data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send email notification
        
        Args:
            recipient: Email address of the recipient
            subject: Email subject
            message: Plain text message
            html_message: HTML version of the message (optional)
            notification_type: Type of notification (for template selection)
            data: Additional data for templates
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Use template if available
            if self.template_config['use_templates'] and notification_type and data:
                html_message = self._get_email_template(notification_type, data)
            
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_config['sender_name']} <{self.email_config['sender_email']}>"
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Add plain text version
            msg.attach(MIMEText(message, 'plain'))
            
            # Add HTML version if provided
            if html_message:
                msg.attach(MIMEText(html_message, 'html'))
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                if self.email_config['username'] and self.email_config['password']:
                    server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            
            self.logger.info(f"Email sent to {recipient}: {subject}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient}: {str(e)}")
            return False
    
    def _send_sms_notification(self, phone_number: str, message: str) -> bool:
        """
        Send SMS notification
        
        Args:
            phone_number: Recipient's phone number
            message: SMS message
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not self.sms_config['api_url'] or not self.sms_config['api_key']:
                self.logger.warning("SMS API configuration is incomplete")
                return False
            
            payload = {
                'recipient': phone_number,
                'message': message,
                'sender_id': self.sms_config['sender_id']
            }
            
            headers = {
                'Authorization': f"Bearer {self.sms_config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.post(self.sms_config['api_url'], json=payload, headers=headers)
            response.raise_for_status()
            
            self.logger.info(f"SMS sent to {phone_number}: {message[:30]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False
    
    def _send_push_notification(self, device_token: str, title: str, message: str, 
                              data: Optional[Dict] = None) -> bool:
        """
        Send push notification to mobile device
        
        Args:
            device_token: Device token for push notification
            title: Notification title
            message: Notification body
            data: Additional data to include
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not self.push_config['api_url'] or not self.push_config['api_key']:
                self.logger.warning("Push notification API configuration is incomplete")
                return False
                
            payload = {
                'app_id': self.push_config['app_id'],
                'include_player_ids': [device_token],
                'headings': {'en': title},
                'contents': {'en': message},
                'data': data or {}
            }
            
            headers = {
                'Authorization': f"Basic {self.push_config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.post(self.push_config['api_url'], json=payload, headers=headers)
            response.raise_for_status()
            
            self.logger.info(f"Push notification sent to device {device_token}: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send push notification to {device_token}: {str(e)}")
            return False
    
    def _store_notification(self, notification_id: str, customer_id: str, 
                          notification_type: str, message: str, 
                          channel: str, priority: str, 
                          data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store notification in database for tracking and history
        
        Args:
            notification_id: Unique identifier for the notification
            customer_id: Customer's unique identifier
            notification_type: Type of notification
            message: Notification message
            channel: Delivery channel used
            priority: Notification priority
            data: Additional notification data
            
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
                self.logger.error(f"Customer not found for notification: {customer_id}")
                return False
                
            internal_customer_id = result[0]
            
            # Record notification
            cursor.execute(
                """
                INSERT INTO notifications
                (id, customer_id, notification_type, message, channel, priority, data, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    notification_id,
                    internal_customer_id,
                    notification_type,
                    message,
                    channel,
                    priority,
                    json.dumps(data) if data else None,
                    NotificationStatus.SENT.value
                )
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing notification: {str(e)}")
            return False
    
    def _get_customer_info(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer contact information from database
        
        Args:
            customer_id: Customer's unique identifier
            
        Returns:
            Dict: Customer information including contact details
        """
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT c.id, c.first_name, c.last_name, c.email, c.phone, 
                       p.device_token, p.notification_preferences
                FROM customers c
                LEFT JOIN customer_preferences p ON c.id = p.customer_id
                WHERE c.customer_id = %s
                """,
                (customer_id,)
            )
            
            customer = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return customer or {}
            
        except Exception as e:
            self.logger.error(f"Error retrieving customer info: {str(e)}")
            return {}
    
    def get_notification_history(self, customer_id: str, 
                               notification_type: Optional[str] = None,
                               limit: int = 20, 
                               offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get notification history for a customer
        
        Args:
            customer_id: Customer's unique identifier
            notification_type: Filter by notification type (optional)
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            
        Returns:
            List[Dict]: List of notification records
        """
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
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
                self.logger.error(f"Customer not found for notification history: {customer_id}")
                return []
                
            internal_customer_id = result[0]
            
            # Build query based on parameters
            query = """
            SELECT id, notification_type, message, channel, status, 
                   created_at, sent_at, read_at
            FROM notifications
            WHERE customer_id = %s
            """
            params = [internal_customer_id]
            
            if notification_type:
                query += " AND notification_type = %s"
                params.append(notification_type)
                
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            notifications = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return notifications
            
        except Exception as e:
            self.logger.error(f"Error retrieving notification history: {str(e)}")
            return []
    
    def mark_notification_as_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read
        
        Args:
            notification_id: Unique identifier of the notification
            
        Returns:
            bool: Success status
        """
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE notifications
                SET status = %s, read_at = NOW()
                WHERE id = %s
                """,
                (NotificationStatus.READ.value, notification_id)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    def update_customer_preferences(self, customer_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update customer notification preferences
        
        Args:
            customer_id: Customer's unique identifier
            preferences: Notification preferences
            
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
                self.logger.error(f"Customer not found for preference update: {customer_id}")
                return False
                
            internal_customer_id = result[0]
            
            # Check if preferences record exists
            cursor.execute(
                """
                SELECT customer_id FROM customer_preferences
                WHERE customer_id = %s
                """,
                (internal_customer_id,)
            )
            
            if cursor.fetchone():
                # Update existing preferences
                cursor.execute(
                    """
                    UPDATE customer_preferences
                    SET notification_preferences = %s,
                        updated_at = NOW()
                    WHERE customer_id = %s
                    """,
                    (json.dumps(preferences), internal_customer_id)
                )
            else:
                # Insert new preferences
                cursor.execute(
                    """
                    INSERT INTO customer_preferences
                    (customer_id, notification_preferences, created_at)
                    VALUES (%s, %s, NOW())
                    """,
                    (internal_customer_id, json.dumps(preferences))
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating customer preferences: {str(e)}")
            return False
    
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
        masked_account = self._mask_account(account)
        reference = data.get('reference_number', '')
        balance = data.get('balance_after', data.get('balance', 0))
        currency = data.get('currency', 'INR')
        date_time = data.get('timestamp', datetime.now().strftime('%d-%m-%Y %H:%M'))
        
        # Different message formats based on transaction type
        if any(t in transaction_type.upper() for t in ['DEBIT', 'WITHDRAWAL', 'PAYMENT']):
            return f"{currency} {amount:,.2f} debited from your account {masked_account} on {date_time}. Ref: {reference}. Avl bal: {currency} {balance:,.2f}"
        
        elif any(t in transaction_type.upper() for t in ['CREDIT', 'DEPOSIT', 'REFUND']):
            return f"{currency} {amount:,.2f} credited to your account {masked_account} on {date_time}. Ref: {reference}. Avl bal: {currency} {balance:,.2f}"
        
        elif 'TRANSFER' in transaction_type.upper():
            beneficiary = data.get('beneficiary_name', 'beneficiary')
            return f"{currency} {amount:,.2f} transferred to {beneficiary} from your account {masked_account} on {date_time}. Ref: {reference}. Avl bal: {currency} {balance:,.2f}"
        
        else:
            return f"Transaction of {currency} {amount:,.2f} processed on {date_time} for your account {masked_account}. Ref: {reference}. Avl bal: {currency} {balance:,.2f}"
    
    def _build_security_message(self, data: Dict[str, Any]) -> str:
        """
        Build security notification message
        
        Args:
            data: Security alert data
            
        Returns:
            str: Formatted message
        """
        alert_type = data.get('alert_type', '').upper()
        timestamp = data.get('timestamp', datetime.now().strftime('%d-%m-%Y %H:%M'))
        
        if alert_type == 'LOGIN_ATTEMPT':
            device = data.get('device', 'unknown device')
            location = data.get('location', 'unknown location')
            return f"Security Alert: Login attempt from new device '{device}' at {location} on {timestamp}. If this wasn't you, please contact customer service immediately."
        
        elif alert_type == 'PASSWORD_CHANGE':
            return f"Your account password was changed on {timestamp}. If this wasn't you, please contact customer service immediately at {self._get_support_number()}."
        
        elif alert_type == 'PIN_CHANGE':
            pin_type = data.get('pin_type', 'PIN').upper()
            return f"Your {pin_type} was changed on {timestamp}. If this wasn't you, please contact customer service immediately at {self._get_support_number()}."
        
        elif alert_type == 'UNAUTHORIZED_ACCESS':
            return f"URGENT SECURITY ALERT: Unauthorized access detected to your account on {timestamp}. Your account has been temporarily locked. Please contact customer service immediately at {self._get_support_number()}."
        
        elif alert_type == 'FRAUD_DETECTION':
            return f"URGENT SECURITY ALERT: Suspicious activity detected on your account on {timestamp}. Please verify recent transactions and contact customer service immediately at {self._get_support_number()}."
        
        else:
            return f"Security Alert: Unusual activity detected on your account on {timestamp}. Please review your recent transactions and contact us if you notice anything suspicious."
    
    def _build_account_message(self, data: Dict[str, Any]) -> str:
        """
        Build account notification message
        
        Args:
            data: Account notification data
            
        Returns:
            str: Formatted message
        """
        notification_subtype = data.get('notification_subtype', '').upper()
        account_number = data.get('account_number', '')
        masked_account = self._mask_account(account_number)
        
        if notification_subtype == 'ACCOUNT_CREATED':
            account_type = data.get('account_type', 'bank account')
            return f"Welcome! Your new {account_type} with account number {masked_account} has been successfully created. Visit our nearest branch for your welcome kit."
        
        elif notification_subtype == 'ACCOUNT_ACTIVATED':
            return f"Your account {masked_account} has been activated. You can now perform transactions using this account."
        
        elif notification_subtype == 'ACCOUNT_DEACTIVATED':
            reason = data.get('reason', 'bank policy')
            return f"Your account {masked_account} has been deactivated due to {reason}. Please contact our customer support for assistance."
        
        elif notification_subtype == 'ACCOUNT_CLOSED':
            reason = data.get('reason', '')
            reason_text = f" due to {reason}" if reason else ""
            return f"Your account {masked_account} has been closed{reason_text}. If you did not request this action, please contact customer service immediately."
        
        elif notification_subtype == 'BALANCE_BELOW_MINIMUM':
            current_balance = data.get('current_balance', 0)
            min_balance = data.get('min_balance', 0)
            currency = data.get('currency', 'INR')
            return f"Alert: Your account {masked_account} balance ({currency} {current_balance:,.2f}) is below the minimum required balance of {currency} {min_balance:,.2f}. Please deposit funds to avoid charges."
        
        elif notification_subtype == 'INTEREST_CREDITED':
            amount = data.get('amount', 0)
            currency = data.get('currency', 'INR')
            return f"Interest of {currency} {amount:,.2f} has been credited to your account {masked_account}."
        
        else:
            return f"Notification regarding your account {masked_account}. Please check your account statement for details."
    
    def _build_card_message(self, data: Dict[str, Any]) -> str:
        """
        Build card notification message
        
        Args:
            data: Card notification data
            
        Returns:
            str: Formatted message
        """
        notification_subtype = data.get('notification_subtype', '').upper()
        card_number = data.get('card_number', '')
        masked_card = self._mask_card_number(card_number)
        card_type = data.get('card_type', 'card')
        
        if notification_subtype == 'CARD_ISSUED':
            return f"Your new {card_type} card {masked_card} has been issued. You will receive it within 7-10 business days."
        
        elif notification_subtype == 'CARD_ACTIVATED':
            return f"Your {card_type} card {masked_card} has been successfully activated. You can now use your card for transactions."
        
        elif notification_subtype == 'CARD_BLOCKED':
            reason = data.get('reason', '')
            reason_text = f" due to {reason}" if reason else ""
            return f"Your {card_type} card {masked_card} has been blocked{reason_text}. Please contact customer service for assistance."
        
        elif notification_subtype == 'CARD_UNBLOCKED':
            return f"Your {card_type} card {masked_card} has been unblocked and is now ready for use."
        
        elif notification_subtype == 'PIN_CHANGED':
            return f"The PIN for your {card_type} card {masked_card} has been changed successfully. If you did not authorize this change, please contact customer service immediately."
        
        elif notification_subtype == 'LIMIT_UPDATED':
            old_limit = data.get('old_limit', {})
            new_limit = data.get('new_limit', {})
            limit_type = data.get('limit_type', 'transaction')
            currency = data.get('currency', 'INR')
            
            # Format message based on available limit information
            if old_limit and new_limit:
                old_value = old_limit.get(limit_type, 0)
                new_value = new_limit.get(limit_type, 0)
                return f"Your {card_type} card {masked_card} {limit_type} limit has been updated from {currency} {old_value:,.2f} to {currency} {new_value:,.2f}."
            else:
                # If we only have new limit information
                for limit_name, limit_value in new_limit.items():
                    return f"Your {card_type} card {masked_card} {limit_name} limit has been set to {currency} {limit_value:,.2f}."
                
                return f"Your {card_type} card {masked_card} limits have been updated. Check your card details for more information."
        
        elif notification_subtype == 'INTERNATIONAL_USAGE':
            status = "enabled" if data.get('enabled', False) else "disabled"
            return f"International usage for your {card_type} card {masked_card} has been {status}."
        
        elif notification_subtype == 'CONTACTLESS_USAGE':
            status = "enabled" if data.get('enabled', False) else "disabled"
            return f"Contactless payments for your {card_type} card {masked_card} has been {status}."
        
        elif notification_subtype == 'EXPIRY_REMINDER':
            expiry_date = data.get('expiry_date', '')
            return f"Your {card_type} card {masked_card} will expire on {expiry_date}. A new card will be issued automatically."
        
        else:
            return f"Notification regarding your {card_type} card {masked_card}. Please check your card statement for details."
    
    def _build_upi_message(self, data: Dict[str, Any]) -> str:
        """
        Build UPI notification message
        
        Args:
            data: UPI notification data
            
        Returns:
            str: Formatted message
        """
        amount = data.get('amount', 0)
        currency = data.get('currency', 'INR')
        reference = data.get('reference_number', '')
        timestamp = data.get('timestamp', datetime.now().strftime('%d-%m-%Y %H:%M'))
        
        # Check transaction type
        if data.get('is_debit', False):
            receiver = data.get('receiver_upi_id', '')
            receiver_name = data.get('receiver_name', receiver)
            return f"{currency} {amount:,.2f} paid to {receiver_name} on {timestamp}. UPI Ref: {reference}"
        
        elif 'receiver_upi_id' in data:
            sender = data.get('sender_upi_id', '')
            sender_name = data.get('sender_name', sender)
            return f"{currency} {amount:,.2f} received from {sender_name} on {timestamp}. UPI Ref: {reference}"
        
        elif data.get('notification_subtype', '').upper() == 'UPI_REGISTRATION':
            upi_id = data.get('upi_id', '')
            return f"Your UPI ID {upi_id} has been successfully registered. You can now make and receive UPI payments."
        
        else:
            return f"UPI Transaction: {currency} {amount:,.2f} on {timestamp}. UPI Ref: {reference}"
    
    def _determine_transaction_priority(self, data: Dict[str, Any]) -> str:
        """
        Determine priority level for transaction notification
        
        Args:
            data: Transaction data
            
        Returns:
            str: Priority level
        """
        amount = float(data.get('amount', 0))
        is_international = data.get('is_international', False)
        is_large = amount >= config.get('notifications.large_transaction_threshold', 10000)
        is_suspicious = data.get('is_suspicious', False)
        
        if is_suspicious:
            return NotificationPriority.HIGH.value
        elif is_international or is_large:
            return NotificationPriority.MEDIUM.value
        else:
            return NotificationPriority.LOW.value
    
    def _determine_account_priority(self, data: Dict[str, Any]) -> str:
        """
        Determine priority level for account notification
        
        Args:
            data: Account notification data
            
        Returns:
            str: Priority level
        """
        notification_subtype = data.get('notification_subtype', '').upper()
        
        high_priority_types = ['ACCOUNT_DEACTIVATED', 'ACCOUNT_CLOSED', 'SUSPICIOUS_ACTIVITY']
        medium_priority_types = ['BALANCE_BELOW_MINIMUM', 'ACCOUNT_ACTIVATED', 'OVERDRAFT']
        
        if notification_subtype in high_priority_types:
            return NotificationPriority.HIGH.value
        elif notification_subtype in medium_priority_types:
            return NotificationPriority.MEDIUM.value
        else:
            return NotificationPriority.LOW.value
    
    def _determine_card_priority(self, data: Dict[str, Any]) -> str:
        """
        Determine priority level for card notification
        
        Args:
            data: Card notification data
            
        Returns:
            str: Priority level
        """
        notification_subtype = data.get('notification_subtype', '').upper()
        
        high_priority_types = ['CARD_BLOCKED', 'SUSPICIOUS_TRANSACTION', 'PIN_CHANGED']
        medium_priority_types = ['LIMIT_UPDATED', 'INTERNATIONAL_USAGE', 'CONTACTLESS_USAGE']
        
        if notification_subtype in high_priority_types:
            return NotificationPriority.HIGH.value
        elif notification_subtype in medium_priority_types:
            return NotificationPriority.MEDIUM.value
        else:
            return NotificationPriority.LOW.value
    
    def _generate_subject(self, notification_type: str, data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate email subject based on notification type and data
        
        Args:
            notification_type: Type of notification
            data: Notification data
            
        Returns:
            str: Email subject
        """
        if not data:
            data = {}
        
        if notification_type == NotificationType.TRANSACTION.value:
            transaction_type = data.get('transaction_type', 'Transaction')
            return f"Transaction Alert: {transaction_type}"
        
        elif notification_type == NotificationType.SECURITY.value:
            alert_type = data.get('alert_type', '').upper()
            if alert_type in ['UNAUTHORIZED_ACCESS', 'FRAUD_DETECTION']:
                return f"URGENT: Security Alert - {alert_type.replace('_', ' ').title()}"
            else:
                return f"Security Alert - {alert_type.replace('_', ' ').title()}"
        
        elif notification_type == NotificationType.ACCOUNT.value:
            subtype = data.get('notification_subtype', '').upper()
            return f"Account Alert: {subtype.replace('_', ' ').title()}"
        
        elif notification_type == NotificationType.CARD.value:
            subtype = data.get('notification_subtype', '').upper()
            card_type = data.get('card_type', 'Card')
            return f"{card_type} Alert: {subtype.replace('_', ' ').title()}"
        
        elif notification_type == NotificationType.UPI.value:
            if data.get('is_debit', False):
                return "UPI Payment Sent"
            else:
                return "UPI Payment Received"
        
        else:
            return f"Bank Notification: {notification_type.replace('_', ' ').title()}"
    
    def _get_email_template(self, notification_type: str, data: Dict[str, Any]) -> str:
        """
        Get HTML email template for notification
        
        Args:
            notification_type: Type of notification
            data: Template data
            
        Returns:
            str: HTML template with data filled in
        """
        # This is a placeholder - in a real implementation, this would load HTML templates
        # from files and fill them with data using a template engine
        
        # Basic HTML template
        template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{self._generate_subject(notification_type, data)}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #0056b3; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; border: 1px solid #ddd; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Core Banking System</h2>
                </div>
                <div class="content">
                    <p>Dear Customer,</p>
                    <p>{self._build_notification_content(notification_type, data)}</p>
                    <p>If you did not authorize this action, please contact our customer service immediately.</p>
                    <p>Thank you for banking with us.</p>
                    <p>Regards,<br>Core Banking System</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>For assistance, contact our customer service at {self._get_support_number()}.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return template
    
    def _build_notification_content(self, notification_type: str, data: Dict[str, Any]) -> str:
        """
        Build detailed HTML content for email notification
        
        Args:
            notification_type: Type of notification
            data: Notification data
            
        Returns:
            str: HTML content
        """
        # This would be more elaborate in a real implementation
        if notification_type == NotificationType.TRANSACTION.value:
            return self._build_transaction_message(data).replace('\n', '<br>')
        elif notification_type == NotificationType.SECURITY.value:
            return self._build_security_message(data).replace('\n', '<br>')
        elif notification_type == NotificationType.ACCOUNT.value:
            return self._build_account_message(data).replace('\n', '<br>')
        elif notification_type == NotificationType.CARD.value:
            return self._build_card_message(data).replace('\n', '<br>')
        elif notification_type == NotificationType.UPI.value:
            return self._build_upi_message(data).replace('\n', '<br>')
        else:
            return "Please check your banking app for details."
    
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
    
    def _mask_card_number(self, card_number: str) -> str:
        """
        Mask card number for security
        
        Args:
            card_number: Full card number
            
        Returns:
            str: Masked card number
        """
        if not card_number or len(card_number) < 10:
            return "XXXX"
            
        if len(card_number) >= 16:
            # Standard credit/debit card format
            return f"XXXX XXXX XXXX {card_number[-4:]}"
        else:
            # For shorter card numbers
            return f"XXXX...{card_number[-4:]}"
    
    def _get_support_number(self) -> str:
        """
        Get customer support phone number
        
        Returns:
            str: Support phone number
        """
        return config.get('customer_support.phone', '1800-XXX-XXXX')

# Create singleton instance
notification_service = NotificationService()
