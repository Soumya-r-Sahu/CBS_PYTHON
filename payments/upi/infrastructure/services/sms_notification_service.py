"""
SMS implementation of UPI notification service.
"""
from typing import Dict, Any, Optional

from ...domain.entities.upi_transaction import UpiTransaction
from ...application.interfaces.notification_service_interface import UpiNotificationServiceInterface


class SmsNotificationService(UpiNotificationServiceInterface):
    """SMS implementation of UPI notification service."""
    
    def __init__(self, sms_api_key: str, sms_sender_id: str, vpa_phone_mapper: callable):
        """
        Initialize with SMS API credentials.
        
        Args:
            sms_api_key: API key for SMS service
            sms_sender_id: Sender ID for SMS service
            vpa_phone_mapper: Function to map VPA to phone number
        """
        self.sms_api_key = sms_api_key
        self.sms_sender_id = sms_sender_id
        self.vpa_phone_mapper = vpa_phone_mapper
    
    def _get_phone_for_vpa(self, vpa: str) -> Optional[str]:
        """Get phone number for a VPA."""
        return self.vpa_phone_mapper(vpa)
    
    def _send_sms(self, phone: str, message: str) -> bool:
        """
        Send SMS using SMS API.
        
        Args:
            phone: Phone number to send SMS to
            message: SMS content
            
        Returns:
            Boolean indicating if SMS was sent successfully
        """
        # In a real implementation, this would call an SMS API
        print(f"Sending SMS to {phone}: {message}")
        # Mock successful send
        return True
    
    def send_transaction_initiated_notification(self, transaction: UpiTransaction, to_vpa: str) -> bool:
        """
        Send notification for transaction initiation.
        
        Args:
            transaction: The UPI transaction that was initiated
            to_vpa: The VPA to send the notification to
            
        Returns:
            Boolean indicating if notification was sent successfully
        """
        phone = self._get_phone_for_vpa(to_vpa)
        if not phone:
            return False
        
        message = (
            f"UPI transaction initiated for ₹{transaction.amount:.2f} "
            f"from {transaction.sender_vpa} to {transaction.receiver_vpa}. "
            f"Ref: {transaction.transaction_id}"
        )
        
        return self._send_sms(phone, message)
    
    def send_transaction_completed_notification(self, transaction: UpiTransaction) -> Dict[str, bool]:
        """
        Send notification for transaction completion to both sender and receiver.
        
        Args:
            transaction: The UPI transaction that was completed
            
        Returns:
            Dictionary with notification status for sender and receiver
            Example: {'sender': True, 'receiver': True}
        """
        result = {'sender': False, 'receiver': False}
        
        # Sender notification
        sender_phone = self._get_phone_for_vpa(transaction.sender_vpa)
        if sender_phone:
            sender_message = (
                f"Your UPI payment of ₹{transaction.amount:.2f} to {transaction.receiver_vpa} "
                f"is successful. Ref: {transaction.reference_id}"
            )
            result['sender'] = self._send_sms(sender_phone, sender_message)
        
        # Receiver notification
        receiver_phone = self._get_phone_for_vpa(transaction.receiver_vpa)
        if receiver_phone:
            receiver_message = (
                f"You have received ₹{transaction.amount:.2f} from {transaction.sender_vpa} "
                f"in your account. Ref: {transaction.reference_id}"
            )
            result['receiver'] = self._send_sms(receiver_phone, receiver_message)
        
        return result
    
    def send_transaction_failed_notification(self, transaction: UpiTransaction) -> bool:
        """
        Send notification for transaction failure.
        
        Args:
            transaction: The UPI transaction that failed
            
        Returns:
            Boolean indicating if notification was sent successfully
        """
        sender_phone = self._get_phone_for_vpa(transaction.sender_vpa)
        if not sender_phone:
            return False
        
        message = (
            f"Your UPI payment of ₹{transaction.amount:.2f} to {transaction.receiver_vpa} "
            f"has failed. Reason: {transaction.failure_reason}. "
            f"Ref: {transaction.transaction_id}"
        )
        
        return self._send_sms(sender_phone, message)
    
    def send_reversal_notification(self, transaction: UpiTransaction) -> Dict[str, bool]:
        """
        Send notification for transaction reversal to both sender and receiver.
        
        Args:
            transaction: The UPI transaction that was reversed
            
        Returns:
            Dictionary with notification status for sender and receiver
            Example: {'sender': True, 'receiver': True}
        """
        result = {'sender': False, 'receiver': False}
        
        # Sender notification
        sender_phone = self._get_phone_for_vpa(transaction.sender_vpa)
        if sender_phone:
            sender_message = (
                f"Your UPI payment of ₹{transaction.amount:.2f} to {transaction.receiver_vpa} "
                f"has been reversed. Reason: {transaction.failure_reason}. "
                f"Ref: {transaction.reference_id}"
            )
            result['sender'] = self._send_sms(sender_phone, sender_message)
        
        # Receiver notification
        receiver_phone = self._get_phone_for_vpa(transaction.receiver_vpa)
        if receiver_phone:
            receiver_message = (
                f"UPI payment of ₹{transaction.amount:.2f} from {transaction.sender_vpa} "
                f"has been reversed. The amount will be debited from your account. "
                f"Ref: {transaction.reference_id}"
            )
            result['receiver'] = self._send_sms(receiver_phone, receiver_message)
        
        return result
