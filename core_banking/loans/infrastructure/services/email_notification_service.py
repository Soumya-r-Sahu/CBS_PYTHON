"""
Email Notification Service for Loans

This module implements email notification services for the loans module.
"""

from typing import Dict, Any, List, Optional
from ...application.interfaces.notification_service_interface import NotificationServiceInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class EmailNotificationService(NotificationServiceInterface):
    """
    Email Notification Service
    
    This service handles sending email notifications related to loans.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Email Notification Service
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.smtp_server = self.config.get('smtp_server', 'smtp.example.com')
        self.smtp_port = self.config.get('smtp_port', 587)
        self.sender_email = self.config.get('sender_email', 'loans@bank.example.com')
        self.email_template_path = self.config.get('email_template_path', 'templates/email/')
    
    def send_notification(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        """
        Send a notification email
        
        Args:
            recipient: Email address of recipient
            subject: Email subject
            message: Email message
            **kwargs: Additional parameters
            
        Returns:
            True if successful, False otherwise
        """
        # In a real implementation, this would connect to an SMTP server and send the email
        # For now, we'll just log the message
        print(f"[EMAIL] To: {recipient}, Subject: {subject}")
        print(f"[EMAIL] Message: {message}")
        
        # Additional parameters
        attachments = kwargs.get('attachments', [])
        if attachments:
            print(f"[EMAIL] Attachments: {attachments}")
        
        # Always return success for this demo implementation
        return True
    
    def notify_loan_application_received(self, customer_email: str, loan_id: str, loan_details: Dict[str, Any]) -> bool:
        """
        Send notification when a loan application is received
        
        Args:
            customer_email: Customer's email address
            loan_id: Loan ID
            loan_details: Dictionary of loan details
            
        Returns:
            True if successful, False otherwise
        """
        subject = "Your Loan Application Has Been Received"
        message = f"""
        Dear Customer,
        
        Thank you for your loan application. Your application has been received and is being processed.
        
        Loan Application Details:
        - Loan ID: {loan_id}
        - Loan Type: {loan_details.get('loan_type', 'N/A')}
        - Amount: {loan_details.get('amount', 'N/A')}
        - Application Date: {loan_details.get('application_date', 'N/A')}
        
        We will notify you as soon as there is an update on your application.
        
        Best regards,
        Your Bank
        """
        
        return self.send_notification(customer_email, subject, message)
    
    def notify_loan_approved(self, customer_email: str, loan_id: str, loan_details: Dict[str, Any]) -> bool:
        """
        Send notification when a loan is approved
        
        Args:
            customer_email: Customer's email address
            loan_id: Loan ID
            loan_details: Dictionary of loan details
            
        Returns:
            True if successful, False otherwise
        """
        subject = "Your Loan Application Has Been Approved"
        message = f"""
        Dear Customer,
        
        We are pleased to inform you that your loan application has been approved.
        
        Loan Details:
        - Loan ID: {loan_id}
        - Loan Type: {loan_details.get('loan_type', 'N/A')}
        - Approved Amount: {loan_details.get('amount', 'N/A')}
        - Interest Rate: {loan_details.get('interest_rate', 'N/A')}
        - Term: {loan_details.get('term_months', 'N/A')} months
        
        Next Steps:
        Our representative will contact you shortly to guide you through the disbursement process.
        
        Best regards,
        Your Bank
        """
        
        return self.send_notification(customer_email, subject, message)
    
    def notify_loan_denied(self, customer_email: str, loan_id: str, reason: str) -> bool:
        """
        Send notification when a loan is denied
        
        Args:
            customer_email: Customer's email address
            loan_id: Loan ID
            reason: Reason for denial
            
        Returns:
            True if successful, False otherwise
        """
        subject = "Update on Your Loan Application"
        message = f"""
        Dear Customer,
        
        We regret to inform you that we are unable to approve your loan application at this time.
        
        Loan Application ID: {loan_id}
        
        Our decision was based on: {reason}
        
        If you have any questions or would like to discuss other financial options, 
        please contact our customer service at customer.service@bank.example.com.
        
        Best regards,
        Your Bank
        """
        
        return self.send_notification(customer_email, subject, message)
    
    def notify_payment_due(self, customer_email: str, loan_id: str, payment_details: Dict[str, Any]) -> bool:
        """
        Send notification for payment due
        
        Args:
            customer_email: Customer's email address
            loan_id: Loan ID
            payment_details: Dictionary of payment details
            
        Returns:
            True if successful, False otherwise
        """
        subject = "Loan Payment Due Reminder"
        message = f"""
        Dear Customer,
        
        This is a reminder that your loan payment is due soon.
        
        Payment Details:
        - Loan ID: {loan_id}
        - Due Date: {payment_details.get('due_date', 'N/A')}
        - Amount Due: {payment_details.get('amount', 'N/A')}
        
        Please ensure that your account has sufficient funds for the payment.
        
        Best regards,
        Your Bank
        """
        
        return self.send_notification(customer_email, subject, message)
    
    def notify_payment_overdue(self, customer_email: str, loan_id: str, payment_details: Dict[str, Any]) -> bool:
        """
        Send notification for overdue payment
        
        Args:
            customer_email: Customer's email address
            loan_id: Loan ID
            payment_details: Dictionary of payment details
            
        Returns:
            True if successful, False otherwise
        """
        subject = "IMPORTANT: Loan Payment Overdue"
        message = f"""
        Dear Customer,
        
        Our records indicate that your loan payment is overdue.
        
        Payment Details:
        - Loan ID: {loan_id}
        - Due Date: {payment_details.get('due_date', 'N/A')}
        - Amount Due: {payment_details.get('amount', 'N/A')}
        - Days Overdue: {payment_details.get('days_overdue', 'N/A')}
        - Late Fee: {payment_details.get('late_fee', 'N/A')}
        
        Please make the payment as soon as possible to avoid further late fees and 
        potential impact on your credit score.
        
        If you have already made the payment, please disregard this message.
        
        Best regards,
        Your Bank
        """
        
        return self.send_notification(customer_email, subject, message)
    
    def notify_loan_closed(self, customer_email: str, loan_id: str, loan_details: Dict[str, Any]) -> bool:
        """
        Send notification when a loan is closed
        
        Args:
            customer_email: Customer's email address
            loan_id: Loan ID
            loan_details: Dictionary of loan details
            
        Returns:
            True if successful, False otherwise
        """
        subject = "Loan Successfully Closed"
        message = f"""
        Dear Customer,
        
        Congratulations! Your loan has been successfully paid off and closed.
        
        Loan Details:
        - Loan ID: {loan_id}
        - Loan Type: {loan_details.get('loan_type', 'N/A')}
        - Closing Date: {loan_details.get('closing_date', 'N/A')}
        
        We appreciate your business and look forward to serving you in the future.
        
        Best regards,
        Your Bank
        """
        
        return self.send_notification(customer_email, subject, message)
