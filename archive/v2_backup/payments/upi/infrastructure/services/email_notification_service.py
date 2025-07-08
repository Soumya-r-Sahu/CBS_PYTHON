"""
Email implementation of UPI notification service.
"""
from typing import Dict, Any, Optional

from ...domain.entities.upi_transaction import UpiTransaction
from ...application.interfaces.notification_service_interface import UpiNotificationServiceInterface


class EmailNotificationService(UpiNotificationServiceInterface):
    """Email implementation of UPI notification service."""
    
    def __init__(self, smtp_config: Dict[str, Any], vpa_email_mapper: callable):
        """
        Initialize with SMTP configuration.
        
        Args:
            smtp_config: SMTP configuration for email sending
            vpa_email_mapper: Function to map VPA to email address
        """
        self.smtp_config = smtp_config
        self.vpa_email_mapper = vpa_email_mapper
        self.from_email = smtp_config.get('from_email', 'upi-notifications@bank.com')
    
    def _get_email_for_vpa(self, vpa: str) -> Optional[str]:
        """Get email address for a VPA."""
        return self.vpa_email_mapper(vpa)
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Send email using SMTP configuration.
        
        Args:
            to_email: Email address to send to
            subject: Email subject
            body: Email content
            
        Returns:
            Boolean indicating if email was sent successfully
        """
        # In a real implementation, this would use smtplib to send emails
        print(f"Sending email to {to_email}: {subject}\n{body}")
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
        email = self._get_email_for_vpa(to_vpa)
        if not email:
            return False
        
        subject = "UPI Transaction Initiated"
        body = f"""
        Dear Customer,
        
        A UPI transaction has been initiated with the following details:
        
        Amount: ₹{transaction.amount:.2f}
        From: {transaction.sender_vpa}
        To: {transaction.receiver_vpa}
        Reference ID: {transaction.transaction_id}
        Date/Time: {transaction.transaction_date}
        
        If you didn't initiate this transaction, please contact our customer service immediately.
        
        Regards,
        UPI Payment Services
        """
        
        return self._send_email(email, subject, body)
    
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
        sender_email = self._get_email_for_vpa(transaction.sender_vpa)
        if sender_email:
            sender_subject = "UPI Payment Successful"
            sender_body = f"""
            Dear Customer,
            
            Your UPI payment has been successfully completed:
            
            Amount: ₹{transaction.amount:.2f}
            To: {transaction.receiver_vpa}
            Reference ID: {transaction.reference_id}
            Transaction ID: {transaction.transaction_id}
            Date/Time: {transaction.transaction_date}
            Remarks: {transaction.remarks or 'No remarks'}
            
            Thank you for using our UPI services.
            
            Regards,
            UPI Payment Services
            """
            
            result['sender'] = self._send_email(sender_email, sender_subject, sender_body)
        
        # Receiver notification
        receiver_email = self._get_email_for_vpa(transaction.receiver_vpa)
        if receiver_email:
            receiver_subject = "UPI Payment Received"
            receiver_body = f"""
            Dear Customer,
            
            You have received a UPI payment:
            
            Amount: ₹{transaction.amount:.2f}
            From: {transaction.sender_vpa}
            Reference ID: {transaction.reference_id}
            Transaction ID: {transaction.transaction_id}
            Date/Time: {transaction.transaction_date}
            Remarks: {transaction.remarks or 'No remarks'}
            
            Thank you for using our UPI services.
            
            Regards,
            UPI Payment Services
            """
            
            result['receiver'] = self._send_email(receiver_email, receiver_subject, receiver_body)
        
        return result
    
    def send_transaction_failed_notification(self, transaction: UpiTransaction) -> bool:
        """
        Send notification for transaction failure.
        
        Args:
            transaction: The UPI transaction that failed
            
        Returns:
            Boolean indicating if notification was sent successfully
        """
        sender_email = self._get_email_for_vpa(transaction.sender_vpa)
        if not sender_email:
            return False
        
        subject = "UPI Payment Failed"
        body = f"""
        Dear Customer,
        
        Your UPI payment could not be completed:
        
        Amount: ₹{transaction.amount:.2f}
        To: {transaction.receiver_vpa}
        Transaction ID: {transaction.transaction_id}
        Date/Time: {transaction.transaction_date}
        Reason: {transaction.failure_reason}
        
        Please try again or contact our customer service if you need assistance.
        
        Regards,
        UPI Payment Services
        """
        
        return self._send_email(sender_email, subject, body)
    
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
        sender_email = self._get_email_for_vpa(transaction.sender_vpa)
        if sender_email:
            sender_subject = "UPI Payment Reversed"
            sender_body = f"""
            Dear Customer,
            
            Your UPI payment has been reversed:
            
            Amount: ₹{transaction.amount:.2f}
            To: {transaction.receiver_vpa}
            Reference ID: {transaction.reference_id}
            Transaction ID: {transaction.transaction_id}
            Date/Time: {transaction.transaction_date}
            Reason: {transaction.failure_reason}
            
            The reversed amount should be credited back to your account.
            
            Regards,
            UPI Payment Services
            """
            
            result['sender'] = self._send_email(sender_email, sender_subject, sender_body)
        
        # Receiver notification
        receiver_email = self._get_email_for_vpa(transaction.receiver_vpa)
        if receiver_email:
            receiver_subject = "UPI Payment Reversed"
            receiver_body = f"""
            Dear Customer,
            
            A UPI payment you received has been reversed:
            
            Amount: ₹{transaction.amount:.2f}
            From: {transaction.sender_vpa}
            Reference ID: {transaction.reference_id}
            Transaction ID: {transaction.transaction_id}
            Date/Time: {transaction.transaction_date}
            Reason: {transaction.failure_reason}
            
            The amount will be debited from your account.
            
            Regards,
            UPI Payment Services
            """
            
            result['receiver'] = self._send_email(receiver_email, receiver_subject, receiver_body)
        
        return result
