"""
SMS Notification Service

This module implements the notification service interface using SMS.
"""

import logging
import requests
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

from ...application.interfaces.notification_service import NotificationServiceInterface


class SmsNotificationService(NotificationServiceInterface):
    """SMS implementation of notification service"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize notification service with configuration
        
        Args:
            config: SMS configuration dictionary
        """
        self.config = config
        self.api_url = config.get('sms_api_url', 'https://sms-gateway.example.com/api/send')
        self.api_key = config.get('sms_api_key', '')
        self.sender_id = config.get('sender_id', 'BANKNAME')
        self.logger = logging.getLogger(__name__)
    
    def _send_sms(self, phone_number: str, message: str) -> bool:
        """
        Send SMS to customer
        
        Args:
            phone_number: Customer phone number
            message: SMS content
            
        Returns:
            True if SMS sent successfully, False otherwise
        """
        try:
            # Prepare payload for SMS API
            payload = {
                'api_key': self.api_key,
                'sender_id': self.sender_id,
                'phone': phone_number,
                'message': message
            }
            
            # Make API call to SMS gateway
            response = requests.post(self.api_url, json=payload, timeout=10)
            
            # Check if SMS was sent successfully
            if response.status_code == 200 and response.json().get('status') == 'success':
                return True
            else:
                self.logger.error(f"SMS API returned error: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending SMS: {e}")
            return False
    
    def _get_customer_phone(self, account_number: str) -> str:
        """
        Get customer phone number for account
        
        Args:
            account_number: Account number
            
        Returns:
            Customer phone number
        """
        # In a real implementation, this would query the database
        # For now, we'll just return a placeholder
        return f"+1234567890"  # Placeholder phone number
    
    def _format_amount(self, amount: Decimal) -> str:
        """Format amount for display in SMS"""
        return f"{float(amount):,.2f}"
    
    def send_withdrawal_notification(
        self,
        account_number: str,
        amount: Decimal,
        transaction_id: str,
        balance: Decimal,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send withdrawal notification via SMS
        
        Args:
            account_number: Account number
            amount: Withdrawal amount
            transaction_id: Transaction ID
            balance: Remaining balance
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        phone = self._get_customer_phone(account_number)
        message = (
            f"ALERT: ATM withdrawal of ${self._format_amount(amount)} from Acct "
            f"...{account_number[-4:]} on {timestamp.strftime('%d-%b-%y %H:%M')}. "
            f"Bal: ${self._format_amount(balance)}. Ref: {transaction_id[:8]}"
        )
        
        return self._send_sms(phone, message)
    
    def send_deposit_notification(
        self,
        account_number: str,
        amount: Decimal,
        transaction_id: str,
        balance: Decimal,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send deposit notification via SMS
        
        Args:
            account_number: Account number
            amount: Deposit amount
            transaction_id: Transaction ID
            balance: Updated balance
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        phone = self._get_customer_phone(account_number)
        message = (
            f"ALERT: ATM deposit of ${self._format_amount(amount)} to Acct "
            f"...{account_number[-4:]} on {timestamp.strftime('%d-%b-%y %H:%M')}. "
            f"Bal: ${self._format_amount(balance)}. Ref: {transaction_id[:8]}"
        )
        
        return self._send_sms(phone, message)
    
    def send_balance_notification(
        self,
        account_number: str,
        balance: Decimal,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send balance inquiry notification via SMS
        
        Args:
            account_number: Account number
            balance: Account balance
            timestamp: Inquiry timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        phone = self._get_customer_phone(account_number)
        message = (
            f"ALERT: Balance inquiry on Acct "
            f"...{account_number[-4:]} at {timestamp.strftime('%H:%M')}. "
            f"Avail Bal: ${self._format_amount(balance)}"
        )
        
        return self._send_sms(phone, message)
    
    def send_pin_change_notification(
        self,
        account_number: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send PIN change notification via SMS
        
        Args:
            account_number: Account number
            timestamp: Change timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        phone = self._get_customer_phone(account_number)
        message = (
            f"ALERT: PIN changed for card linked to Acct "
            f"...{account_number[-4:]} on {timestamp.strftime('%d-%b-%y %H:%M')}. "
            f"If not done by you, call customer service immediately."
        )
        
        return self._send_sms(phone, message)
    
    def send_transaction_notification(
        self,
        account_number: str,
        transaction_type: str,
        amount: Decimal,
        transaction_id: str,
        balance: Optional[Decimal] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send generic transaction notification via SMS
        
        Args:
            account_number: Account number
            transaction_type: Type of transaction
            amount: Transaction amount
            transaction_id: Transaction ID
            balance: Account balance after transaction
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if transaction_type.lower() == "withdrawal":
            return self.send_withdrawal_notification(
                account_number, amount, transaction_id, balance or Decimal('0'), timestamp
            )
        elif transaction_type.lower() == "deposit":
            return self.send_deposit_notification(
                account_number, amount, transaction_id, balance or Decimal('0'), timestamp
            )
        
        # Generic notification for other types
        if timestamp is None:
            timestamp = datetime.now()
        
        phone = self._get_customer_phone(account_number)
        message = (
            f"ALERT: {transaction_type.upper()} of ${self._format_amount(amount)} "
            f"on Acct ...{account_number[-4:]} at {timestamp.strftime('%d-%b-%y %H:%M')}. "
        )
        
        if balance:
            message += f"Bal: ${self._format_amount(balance)}. "
            
        message += f"Ref: {transaction_id[:8]}"
        
        return self._send_sms(phone, message)
