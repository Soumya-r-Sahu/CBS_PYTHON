"""
SMS Notification Service for Loans

This module implements SMS notification services for the loans module.
"""

from typing import Dict, Any, List, Optional
from ...application.interfaces.notification_service_interface import NotificationServiceInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class SmsNotificationService(NotificationServiceInterface):
    """
    SMS Notification Service
    
    This service handles sending SMS notifications related to loans.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SMS Notification Service
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.sms_provider = self.config.get('sms_provider', 'default_provider')
        self.sender_id = self.config.get('sender_id', 'BANKNAME')
        self.api_key = self.config.get('api_key', 'default_api_key')
    
    def send_notification(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        """
        Send an SMS notification
        
        Args:
            recipient: Phone number of recipient
            subject: Not used for SMS (included for interface compatibility)
            message: SMS message
            **kwargs: Additional parameters
            
        Returns:
            True if successful, False otherwise
        """
        # In a real implementation, this would connect to an SMS gateway
        # For now, we'll just log the message
        print(f"[SMS] To: {recipient}")
        print(f"[SMS] Message: {message}")
        
        # Always return success for this demo implementation
        return True
    
    def notify_loan_application_received(self, customer_phone: str, loan_id: str, loan_details: Dict[str, Any]) -> bool:
        """
        Send notification when a loan application is received
        
        Args:
            customer_phone: Customer's phone number
            loan_id: Loan ID
            loan_details: Dictionary of loan details
            
        Returns:
            True if successful, False otherwise
        """
        message = f"Your loan application (ID: {loan_id}) for {loan_details.get('amount', 'N/A')} has been received. We will keep you updated on its status."
        
        return self.send_notification(customer_phone, "Loan Application Received", message)
    
    def notify_loan_approved(self, customer_phone: str, loan_id: str, loan_details: Dict[str, Any]) -> bool:
        """
        Send notification when a loan is approved
        
        Args:
            customer_phone: Customer's phone number
            loan_id: Loan ID
            loan_details: Dictionary of loan details
            
        Returns:
            True if successful, False otherwise
        """
        message = f"Congratulations! Your loan application (ID: {loan_id}) for {loan_details.get('amount', 'N/A')} has been approved. Our representative will contact you shortly."
        
        return self.send_notification(customer_phone, "Loan Approved", message)
    
    def notify_loan_denied(self, customer_phone: str, loan_id: str, reason: str) -> bool:
        """
        Send notification when a loan is denied
        
        Args:
            customer_phone: Customer's phone number
            loan_id: Loan ID
            reason: Reason for denial
            
        Returns:
            True if successful, False otherwise
        """
        message = f"We regret to inform you that your loan application (ID: {loan_id}) could not be approved at this time. Please contact our customer service for more information."
        
        return self.send_notification(customer_phone, "Loan Application Update", message)
    
    def notify_payment_due(self, customer_phone: str, loan_id: str, payment_details: Dict[str, Any]) -> bool:
        """
        Send notification for payment due
        
        Args:
            customer_phone: Customer's phone number
            loan_id: Loan ID
            payment_details: Dictionary of payment details
            
        Returns:
            True if successful, False otherwise
        """
        message = f"REMINDER: Your loan payment of {payment_details.get('amount', 'N/A')} for loan ID {loan_id} is due on {payment_details.get('due_date', 'N/A')}."
        
        return self.send_notification(customer_phone, "Payment Due", message)
    
    def notify_payment_overdue(self, customer_phone: str, loan_id: str, payment_details: Dict[str, Any]) -> bool:
        """
        Send notification for overdue payment
        
        Args:
            customer_phone: Customer's phone number
            loan_id: Loan ID
            payment_details: Dictionary of payment details
            
        Returns:
            True if successful, False otherwise
        """
        message = f"URGENT: Your loan payment of {payment_details.get('amount', 'N/A')} for loan ID {loan_id} is overdue by {payment_details.get('days_overdue', 'N/A')} days. Please make payment immediately to avoid penalties."
        
        return self.send_notification(customer_phone, "Payment Overdue", message)
    
    def notify_loan_closed(self, customer_phone: str, loan_id: str, loan_details: Dict[str, Any]) -> bool:
        """
        Send notification when a loan is closed
        
        Args:
            customer_phone: Customer's phone number
            loan_id: Loan ID
            loan_details: Dictionary of loan details
            
        Returns:
            True if successful, False otherwise
        """
        message = f"Congratulations! Your loan (ID: {loan_id}) has been fully paid and closed. Thank you for your business."
        
        return self.send_notification(customer_phone, "Loan Closed", message)
