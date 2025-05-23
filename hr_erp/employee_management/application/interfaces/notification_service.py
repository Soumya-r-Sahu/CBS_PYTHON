"""
Notification Service Interface

This module defines the interface for notification services 
that can be used by application use cases.
"""

from abc import ABC, abstractmethod
from uuid import UUID


class NotificationService(ABC):
    """
    Interface for sending notifications across the system.
    
    This abstract class defines the contract that any notification service
    implementation must follow to be used by application use cases.
    """
    
    @abstractmethod
    def send_onboarding_notification(self, employee_id: UUID, employee_name: str, email: str) -> bool:
        """
        Send onboarding notification to a new employee
        
        Args:
            employee_id: The unique identifier of the employee
            employee_name: The employee's first name
            email: The employee's email address
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def notify_manager(self, manager_id: UUID, subject: str, message: str) -> bool:
        """
        Send notification to a manager
        
        Args:
            manager_id: The unique identifier of the manager
            subject: The notification subject
            message: The notification message
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_document_reminder(self, employee_id: UUID, document_type: str, due_date: str) -> bool:
        """
        Send document reminder notification
        
        Args:
            employee_id: The unique identifier of the employee
            document_type: The type of document needed
            due_date: The date by which the document is required
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        pass
