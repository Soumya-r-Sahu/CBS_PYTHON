"""
Account Service Interface

Defines the interface for account operations used by transaction services.
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


class AccountServiceInterface(ABC):
    """Interface for account services required by transactions"""
    
    @abstractmethod
    def get_account(self, account_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get account data by ID
        
        Args:
            account_id: Account ID to retrieve
            
        Returns:
            Account data if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update_balance(self, account_id: UUID, amount: Decimal, is_credit: bool) -> Optional[Dict[str, Any]]:
        """
        Update account balance
        
        Args:
            account_id: Account ID to update
            amount: Amount to add or subtract
            is_credit: True for credit (increase balance), False for debit (decrease balance)
            
        Returns:
            Updated account data if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def validate_account_status(self, account_id: UUID) -> Dict[str, Any]:
        """
        Validate if an account is active and can perform transactions
        
        Args:
            account_id: Account ID to validate
            
        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "can_debit": bool,
                "can_credit": bool,
                "errors": List[str]
            }
        """
        pass
    
    @abstractmethod
    def check_balance(self, account_id: UUID, required_amount: Decimal) -> Dict[str, Any]:
        """
        Check if account has sufficient balance
        
        Args:
            account_id: Account ID to check
            required_amount: Amount required
            
        Returns:
            Dictionary with check results:
            {
                "has_funds": bool,
                "current_balance": Decimal,
                "available_balance": Decimal
            }
        """
        pass
