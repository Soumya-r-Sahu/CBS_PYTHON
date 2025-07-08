"""
Account Validator

This module defines validators for account operations.
"""

from decimal import Decimal
from typing import Dict, Any

from ..entities.account import Account, AccountStatus

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class AccountValidator:
    """Validator for account operations"""
    
    @staticmethod
    def validate_account_creation(
        account_number: str,
        customer_id: str,
        account_type: str,
        currency: str = "INR",
        initial_deposit: Decimal = Decimal('0.00')
    ) -> Dict[str, Any]:
        """
        Validate account creation parameters
        
        Args:
            account_number: The account number
            customer_id: The customer ID
            account_type: The type of account
            currency: The account currency
            initial_deposit: The initial deposit amount
            
        Returns:
            Dictionary with validation result
        """
        result = {
            "valid": True,
            "errors": []
        }
        
        # Validate account number
        if not account_number or len(account_number) < 8:
            result["valid"] = False
            result["errors"].append("Account number must be at least 8 characters")
            
        # Validate customer ID
        if not customer_id:
            result["valid"] = False
            result["errors"].append("Customer ID must be provided")
            
        # Validate account type
        valid_account_types = ["SAVINGS", "CURRENT", "FIXED_DEPOSIT", "LOAN"]
        if not account_type or account_type.upper() not in valid_account_types:
            result["valid"] = False
            result["errors"].append(
                f"Account type must be one of: {', '.join(valid_account_types)}"
            )
            
        # Validate currency
        if not currency or len(currency) != 3:
            result["valid"] = False
            result["errors"].append("Currency must be a valid 3-letter ISO code")
            
        # Validate initial deposit
        if initial_deposit < Decimal('0'):
            result["valid"] = False
            result["errors"].append("Initial deposit cannot be negative")
            
        return result
        
    @staticmethod
    def validate_deposit(account: Account, amount: Decimal) -> Dict[str, Any]:
        """
        Validate deposit operation
        
        Args:
            account: The account to deposit to
            amount: The amount to deposit
            
        Returns:
            Dictionary with validation result
        """
        result = {
            "valid": True,
            "errors": []
        }
        
        # Check if account is active
        if account.status != AccountStatus.ACTIVE:
            result["valid"] = False
            result["errors"].append(f"Cannot deposit to {account.status.value} account")
            
        # Check amount is positive
        if amount <= Decimal('0'):
            result["valid"] = False
            result["errors"].append("Deposit amount must be positive")
            
        return result
        
    @staticmethod
    def validate_withdrawal(account: Account, amount: Decimal) -> Dict[str, Any]:
        """
        Validate withdrawal operation
        
        Args:
            account: The account to withdraw from
            amount: The amount to withdraw
            
        Returns:
            Dictionary with validation result
        """
        result = {
            "valid": True,
            "errors": []
        }
        
        # Check if account is active
        if account.status != AccountStatus.ACTIVE:
            result["valid"] = False
            result["errors"].append(f"Cannot withdraw from {account.status.value} account")
            
        # Check amount is positive
        if amount <= Decimal('0'):
            result["valid"] = False
            result["errors"].append("Withdrawal amount must be positive")
            
        # Check sufficient balance including overdraft if applicable
        available_balance = account.balance
        if account.overdraft_limit:
            available_balance += account.overdraft_limit
            
        if amount > available_balance:
            result["valid"] = False
            result["errors"].append("Insufficient funds for withdrawal")
            
        return result
