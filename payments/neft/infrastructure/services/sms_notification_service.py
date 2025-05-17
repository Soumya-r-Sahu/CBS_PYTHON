"""
NEFT SMS Notification Service.
Implementation of the NEFTNotificationServiceInterface using SMS.
"""
import logging
import time
from typing import Dict, Any, Optional

from ...domain.entities.neft_transaction import NEFTTransaction
from ...application.interfaces.neft_notification_service_interface import NEFTNotificationServiceInterface


class SMSNotificationService(NEFTNotificationServiceInterface):
    """SMS implementation of NEFT notification service."""
    
    def __init__(self, config: Dict[str, Any], mock_mode: bool = True):
        """
        Initialize the service.
        
        Args:
            config: Configuration dictionary with SMS settings
            mock_mode: Whether to run in mock mode (no actual SMS)
        """
        self.mock_mode = mock_mode
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        self.sms_api_key = config.get("sms_api_key", "mock_api_key")
        self.sms_sender_id = config.get("sms_sender_id", "NEFTPY")
        
        if self.mock_mode:
            self.logger.warning("SMS Notification Service initialized in mock mode. No actual SMS will be sent.")
    
    def _get_customer_phone(self, customer_id: Optional[str]) -> Optional[str]:
        """
        Get customer phone number from customer ID.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Optional[str]: Phone number if found, None otherwise
        """
        if not customer_id:
            return None
            
        # In a real implementation, this would query a database or service
        # For now, just return a mock phone number
        return f"+91{customer_id[-10:]}" if len(customer_id) >= 10 else None
    
    def notify_transaction_initiated(self, transaction: NEFTTransaction) -> bool:
        """
        Notify that a transaction has been initiated.
        
        Args:
            transaction: The transaction that was initiated
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if self.mock_mode:
            return self._mock_send_sms(
                transaction.customer_id,
                f"NEFT transfer of Rs.{transaction.payment_details.amount:.2f} to {transaction.payment_details.beneficiary_name} "
                f"initiated. Ref: {transaction.transaction_reference}"
            )
        
        try:
            phone = self._get_customer_phone(transaction.customer_id)
            if not phone:
                self.logger.warning(f"No phone number for customer ID: {transaction.customer_id}")
                return False
            
            # Construct message
            message = (
                f"NEFT transfer of Rs.{transaction.payment_details.amount:.2f} to {transaction.payment_details.beneficiary_name} "
                f"initiated. Ref: {transaction.transaction_reference}"
            )
            
            # Call SMS API (implementation would depend on the provider)
            # This is a placeholder
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending transaction initiated SMS: {str(e)}")
            return False
    
    def notify_transaction_completed(self, transaction: NEFTTransaction) -> bool:
        """
        Notify that a transaction has been completed.
        
        Args:
            transaction: The completed transaction
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if self.mock_mode:
            return self._mock_send_sms(
                transaction.customer_id,
                f"NEFT transfer of Rs.{transaction.payment_details.amount:.2f} to {transaction.payment_details.beneficiary_name} "
                f"completed successfully. UTR: {transaction.utr_number}"
            )
        
        try:
            phone = self._get_customer_phone(transaction.customer_id)
            if not phone:
                self.logger.warning(f"No phone number for customer ID: {transaction.customer_id}")
                return False
            
            # Construct message
            message = (
                f"NEFT transfer of Rs.{transaction.payment_details.amount:.2f} to {transaction.payment_details.beneficiary_name} "
                f"completed successfully. UTR: {transaction.utr_number}"
            )
            
            # Call SMS API (implementation would depend on the provider)
            # This is a placeholder
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending transaction completed SMS: {str(e)}")
            return False
    
    def notify_transaction_failed(self, transaction: NEFTTransaction) -> bool:
        """
        Notify that a transaction has failed.
        
        Args:
            transaction: The failed transaction
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if self.mock_mode:
            return self._mock_send_sms(
                transaction.customer_id,
                f"NEFT transfer of Rs.{transaction.payment_details.amount:.2f} to {transaction.payment_details.beneficiary_name} "
                f"has failed. Reason: {transaction.error_message}. Ref: {transaction.transaction_reference}"
            )
        
        try:
            phone = self._get_customer_phone(transaction.customer_id)
            if not phone:
                self.logger.warning(f"No phone number for customer ID: {transaction.customer_id}")
                return False
            
            # Construct message
            message = (
                f"NEFT transfer of Rs.{transaction.payment_details.amount:.2f} to {transaction.payment_details.beneficiary_name} "
                f"has failed. Reason: {transaction.error_message}. Ref: {transaction.transaction_reference}"
            )
            
            # Call SMS API (implementation would depend on the provider)
            # This is a placeholder
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending transaction failed SMS: {str(e)}")
            return False
    
    def notify_batch_completed(self, batch_number: str, success_count: int, fail_count: int) -> bool:
        """
        Notify that a batch has been completed.
        
        Args:
            batch_number: The batch number
            success_count: Number of successful transactions
            fail_count: Number of failed transactions
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        # Batch notifications are typically for bank staff, not customers
        # This could notify system administrators or operations team
        
        if self.mock_mode:
            self.logger.info(
                f"[MOCK ADMIN SMS] NEFT batch {batch_number} processed: "
                f"{success_count} successful, {fail_count} failed."
            )
            return True
        
        try:
            # Get admin phone numbers from config
            admin_phones = self.config.get("admin_phone_numbers", [])
            if not admin_phones:
                self.logger.warning("No admin phone numbers configured for batch notifications")
                return False
            
            # Construct message
            message = (
                f"NEFT batch {batch_number} processed: "
                f"{success_count} successful, {fail_count} failed."
            )
            
            # Call SMS API for each admin (implementation would depend on the provider)
            # This is a placeholder
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending batch completed SMS: {str(e)}")
            return False
    
    def _mock_send_sms(self, customer_id: Optional[str], message: str) -> bool:
        """
        Mock implementation of SMS sending for testing.
        
        Args:
            customer_id: Customer ID
            message: The SMS message
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Simulate processing delay
        time.sleep(0.1)
        
        phone = self._get_customer_phone(customer_id)
        if phone:
            self.logger.info(f"[MOCK SMS to {phone}] {message}")
            return True
        else:
            self.logger.warning(f"[MOCK SMS] No phone number for customer ID: {customer_id}")
            return False
