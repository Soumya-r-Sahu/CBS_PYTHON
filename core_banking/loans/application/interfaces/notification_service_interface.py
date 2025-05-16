"""
Notification Service Interface

This module defines the interface for notification services.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class NotificationServiceInterface(ABC):
    """
    Interface for notification service implementations.
    
    This interface defines the contract that any notification service
    implementation must fulfill, ensuring separation between the
    application and infrastructure layers.
    """
    
    @abstractmethod
    def send_notification(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        """
        Send a notification to a recipient.
        
        Args:
            recipient: The recipient of the notification (email, phone, etc.)
            subject: The notification subject
            message: The notification message
            **kwargs: Additional parameters
            
        Returns:
            True if the notification was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def notify_loan_application_received(self, recipient: str, loan_id: str, loan_details: Dict[str, Any]) -> bool:
        """
        Send notification when a loan application is received.
        
        Args:
            recipient: The recipient of the notification
            loan_id: The loan ID
            loan_details: Dictionary of loan details
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def notify_loan_approved(self, recipient: str, loan_id: str, loan_details: Dict[str, Any]) -> bool:
        """
        Send notification when a loan is approved.
        
        Args:
            recipient: The recipient of the notification
            loan_id: The loan ID
            loan_details: Dictionary of loan details
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def notify_loan_denied(self, recipient: str, loan_id: str, reason: str) -> bool:
        """
        Send notification when a loan is denied.
        
        Args:
            recipient: The recipient of the notification
            loan_id: The loan ID
            reason: Reason for denial
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def notify_payment_due(self, recipient: str, loan_id: str, payment_details: Dict[str, Any]) -> bool:
        """
        Send notification for payment due.
        
        Args:
            recipient: The recipient of the notification
            loan_id: The loan ID
            payment_details: Dictionary of payment details
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def notify_payment_overdue(self, recipient: str, loan_id: str, payment_details: Dict[str, Any]) -> bool:
        """
        Send notification for overdue payment.
        
        Args:
            recipient: The recipient of the notification
            loan_id: The loan ID
            payment_details: Dictionary of payment details
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def notify_loan_closed(self, recipient: str, loan_id: str, loan_details: Dict[str, Any]) -> bool:
        """
        Send notification when a loan is closed.
        
        Args:
            recipient: The recipient of the notification
            loan_id: The loan ID
            loan_details: Dictionary of loan details
            
        Returns:
            True if successful, False otherwise
        """
        pass
