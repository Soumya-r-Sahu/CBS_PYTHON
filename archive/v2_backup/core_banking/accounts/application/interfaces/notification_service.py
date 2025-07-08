"""
Notification Service Interface

This module defines the interface for notification services.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class NotificationServiceInterface(ABC):
    """Interface for notification services"""
    
    @abstractmethod
    def send_transaction_notification(self,
                                    account_number: str,
                                    transaction_type: str,
                                    amount: Decimal,
                                    balance: Decimal,
                                    timestamp: str,
                                    reference_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a notification for a transaction
        
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
        pass
    
    @abstractmethod
    def send_account_status_notification(self,
                                       account_number: str,
                                       status: str,
                                       timestamp: str,
                                       reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a notification for an account status change
        
        Args:
            account_number: The account number
            status: The new status
            timestamp: The timestamp of the change
            reason: Optional reason for the status change
            
        Returns:
            Dictionary with notification result
        """
        pass
