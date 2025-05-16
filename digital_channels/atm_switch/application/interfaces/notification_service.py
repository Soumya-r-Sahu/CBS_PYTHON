"""
Notification Service Interface

This module defines the notification service interface for the ATM module.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime


class NotificationServiceInterface(ABC):
    """Interface for notification service operations"""
    
    @abstractmethod
    def send_withdrawal_notification(
        self,
        account_number: str,
        amount: Decimal,
        transaction_id: str,
        balance: Decimal,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send withdrawal notification
        
        Args:
            account_number: Account number
            amount: Withdrawal amount
            transaction_id: Transaction ID
            balance: Remaining balance
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_deposit_notification(
        self,
        account_number: str,
        amount: Decimal,
        transaction_id: str,
        balance: Decimal,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send deposit notification
        
        Args:
            account_number: Account number
            amount: Deposit amount
            transaction_id: Transaction ID
            balance: Updated balance
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_balance_inquiry_notification(
        self,
        account_number: str,
        balance: Decimal,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send balance inquiry notification
        
        Args:
            account_number: Account number
            balance: Account balance
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_pin_change_notification(
        self,
        card_number: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send PIN change notification
        
        Args:
            card_number: Card number (masked)
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_card_blocked_notification(
        self,
        card_number: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send card blocked notification
        
        Args:
            card_number: Card number (masked)
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
