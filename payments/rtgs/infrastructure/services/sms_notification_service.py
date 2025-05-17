"""
SMS notification service implementation for RTGS.
"""
import logging
import requests
from typing import Dict, Any

from ...application.interfaces.rtgs_notification_service_interface import RTGSNotificationServiceInterface
from ...domain.entities.rtgs_transaction import RTGSTransaction

logger = logging.getLogger(__name__)


class SMSNotificationService(RTGSNotificationServiceInterface):
    """SMS notification service implementation."""
    
    def __init__(self, api_url: str, api_key: str, sender_id: str, use_mock: bool = False):
        """
        Initialize the SMS notification service.
        
        Args:
            api_url: SMS API URL
            api_key: API key for the SMS service
            sender_id: Sender ID for SMS
            use_mock: Whether to use mock responses (for testing)
        """
        self.api_url = api_url
        self.api_key = api_key
        self.sender_id = sender_id
        self.use_mock = use_mock
    
    def _format_amount(self, amount: float) -> str:
        """Format amount with commas and 2 decimal places."""
        return "{:,.2f}".format(amount)
    
    def notify_transaction_initiated(self, transaction: RTGSTransaction) -> Dict[str, Any]:
        """
        Send notification for an initiated transaction.
        
        Args:
            transaction: The transaction for which to send notification
            
        Returns:
            Dict[str, Any]: Notification result
        """
        if self.use_mock:
            logger.info(f"[MOCK] Sending initiation notification for RTGS transaction {transaction.id}")
            return {"status": "success", "message": "Notification sent (mock)"}
        
        # Format message
        amount = self._format_amount(transaction.payment_details.amount)
        message = (
            f"RTGS transaction initiated for Rs.{amount} to "
            f"{transaction.payment_details.beneficiary_name} "
            f"(Acc: {transaction.payment_details.beneficiary_account_number[-4:]}). "
            f"Ref: {transaction.transaction_reference}. "
            f"Status updates will follow."
        )
        
        try:
            # Send SMS via the API
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "sender_id": self.sender_id,
                    "to": "CUSTOMER_PHONE_NUMBER",  # This would come from customer profile in a real implementation
                    "message": message
                },
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to send RTGS initiation notification: {str(e)}")
            return {"status": "error", "message": f"Failed to send notification: {str(e)}"}
    
    def notify_transaction_completed(self, transaction: RTGSTransaction) -> Dict[str, Any]:
        """
        Send notification for a completed transaction.
        
        Args:
            transaction: The transaction for which to send notification
            
        Returns:
            Dict[str, Any]: Notification result
        """
        if self.use_mock:
            logger.info(f"[MOCK] Sending completion notification for RTGS transaction {transaction.id}")
            return {"status": "success", "message": "Notification sent (mock)"}
        
        # Format message
        amount = self._format_amount(transaction.payment_details.amount)
        message = (
            f"Your RTGS transaction for Rs.{amount} to "
            f"{transaction.payment_details.beneficiary_name} "
            f"is successful. UTR: {transaction.utr_number}. "
            f"Thank you for banking with us."
        )
        
        try:
            # Send SMS via the API
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "sender_id": self.sender_id,
                    "to": "CUSTOMER_PHONE_NUMBER",  # This would come from customer profile in a real implementation
                    "message": message
                },
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to send RTGS completion notification: {str(e)}")
            return {"status": "error", "message": f"Failed to send notification: {str(e)}"}
    
    def notify_transaction_failed(self, transaction: RTGSTransaction, reason: str) -> Dict[str, Any]:
        """
        Send notification for a failed transaction.
        
        Args:
            transaction: The transaction for which to send notification
            reason: Failure reason
            
        Returns:
            Dict[str, Any]: Notification result
        """
        if self.use_mock:
            logger.info(f"[MOCK] Sending failure notification for RTGS transaction {transaction.id}")
            return {"status": "success", "message": "Notification sent (mock)"}
        
        # Format message
        amount = self._format_amount(transaction.payment_details.amount)
        message = (
            f"Your RTGS transaction for Rs.{amount} to "
            f"{transaction.payment_details.beneficiary_name} "
            f"could not be processed. Reason: {reason}. "
            f"Please contact customer support for assistance."
        )
        
        try:
            # Send SMS via the API
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "sender_id": self.sender_id,
                    "to": "CUSTOMER_PHONE_NUMBER",  # This would come from customer profile in a real implementation
                    "message": message
                },
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to send RTGS failure notification: {str(e)}")
            return {"status": "error", "message": f"Failed to send notification: {str(e)}"}
