"""
SMS Notification Service

This module provides implementation of notification service using SMS.
"""

import logging
import requests
from decimal import Decimal
from typing import Dict, Any, Optional

from ...interfaces.notification_service import NotificationServiceInterface


class SmsNotificationService(NotificationServiceInterface):
    """SMS implementation of notification service"""
    
    def __init__(
        self,
        sms_api_url: str,
        sms_api_key: str,
        sms_sender_id: str,
        customer_phone_provider
    ):
        """
        Initialize SMS notification service
        
        Args:
            sms_api_url: SMS API URL
            sms_api_key: SMS API key
            sms_sender_id: SMS sender ID
            customer_phone_provider: Provider for getting customer phone number
        """
        self.sms_api_url = sms_api_url
        self.sms_api_key = sms_api_key
        self.sms_sender_id = sms_sender_id
        self.customer_phone_provider = customer_phone_provider
        self.logger = logging.getLogger(__name__)
    
    def send_transaction_notification(self,
                                    account_number: str,
                                    transaction_type: str,
                                    amount: Decimal,
                                    balance: Decimal,
                                    timestamp: str,
                                    reference_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a notification for a transaction via SMS
        
        Args:
            account_number: The account number
            transaction_type: The transaction type
            amount: The transaction amount
            balance: The account balance after the transaction
            timestamp: The transaction timestamp
            reference_id: Optional reference ID
            
        Returns:
            Dictionary with notification result
        """
        try:
            customer_phone = self._get_customer_phone(account_number)
            if not customer_phone:
                return {
                    "success": False,
                    "message": f"Customer phone not found for account {account_number}"
                }
            
            # Format amount and balance for SMS
            formatted_amount = f"{amount:,.2f}"
            formatted_balance = f"{balance:,.2f}"
            
            # Create concise SMS message
            message = (
                f"Transaction: {transaction_type} "
                f"of {formatted_amount} on Acc: {self._mask_account_number(account_number)}. "
                f"Balance: {formatted_balance}. "
                f"Time: {timestamp[:16]}. "  # Shorter timestamp format
                f"Ref: {reference_id or 'N/A'}"
            )
            
            self._send_sms(customer_phone, message)
            
            return {
                "success": True,
                "message": f"Transaction notification SMS sent to {self._mask_phone(customer_phone)}"
            }
        except Exception as e:
            self.logger.error(f"Error sending transaction SMS notification: {e}")
            return {
                "success": False,
                "message": f"Failed to send transaction SMS notification: {str(e)}"
            }
    
    def send_account_status_notification(self,
                                       account_number: str,
                                       status: str,
                                       timestamp: str,
                                       reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a notification for an account status change via SMS
        
        Args:
            account_number: The account number
            status: The new status
            timestamp: The timestamp of the change
            reason: Optional reason for the status change
            
        Returns:
            Dictionary with notification result
        """
        try:
            customer_phone = self._get_customer_phone(account_number)
            if not customer_phone:
                return {
                    "success": False,
                    "message": f"Customer phone not found for account {account_number}"
                }
            
            # Create concise SMS message
            message = (
                f"Account: {self._mask_account_number(account_number)} "
                f"status changed to {status}. "
                f"Time: {timestamp[:16]}. "  # Shorter timestamp format
            )
            
            if reason:
                # Add reason if provided, but keep it concise
                short_reason = reason if len(reason) <= 50 else reason[:47] + "..."
                message += f"Reason: {short_reason}"
            
            self._send_sms(customer_phone, message)
            
            return {
                "success": True,
                "message": f"Account status notification SMS sent to {self._mask_phone(customer_phone)}"
            }
        except Exception as e:
            self.logger.error(f"Error sending account status SMS notification: {e}")
            return {
                "success": False,
                "message": f"Failed to send account status SMS notification: {str(e)}"
            }
    
    def _get_customer_phone(self, account_number: str) -> Optional[str]:
        """
        Get customer phone number from account number
        
        Args:
            account_number: The account number
            
        Returns:
            Customer phone number
        """
        try:
            # Use the customer phone provider to get the phone number
            # This could be a service or repository that maps account numbers to customer phones
            return self.customer_phone_provider.get_phone_by_account(account_number)
        except Exception as e:
            self.logger.error(f"Error getting customer phone: {e}")
            return None
    
    def _send_sms(self, to_phone: str, message: str) -> bool:
        """
        Send an SMS
        
        Args:
            to_phone: Recipient phone number
            message: SMS message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                'apikey': self.sms_api_key,
                'sender': self.sms_sender_id,
                'to': to_phone,
                'message': message,
                'format': 'json'
            }
            
            response = requests.post(self.sms_api_url, data=payload)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            return True
        except Exception as e:
            self.logger.error(f"Error sending SMS: {e}")
            return False
    
    def _mask_account_number(self, account_number: str) -> str:
        """
        Mask account number for security
        
        Args:
            account_number: Full account number
            
        Returns:
            Masked account number
        """
        if len(account_number) <= 4:
            return account_number
            
        return "X" * (len(account_number) - 4) + account_number[-4:]
    
    def _mask_phone(self, phone: str) -> str:
        """
        Mask phone number for security
        
        Args:
            phone: Full phone number
            
        Returns:
            Masked phone number
        """
        if len(phone) <= 4:
            return phone
            
        return "X" * (len(phone) - 4) + phone[-4:]
