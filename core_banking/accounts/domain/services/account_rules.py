"""
Account Rules Service

This module defines the service for enforcing account rules and policies.
"""

from decimal import Decimal
from typing import Optional

from ..entities.account import Account, AccountType, AccountStatus, AccountStatus
from ..value_objects.money import Money

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class AccountRules:
    """
    Service for enforcing account rules and policies
    
    This service provides methods to enforce business rules related to accounts,
    including minimum balance requirements, withdrawal limits, and account type
    specific restrictions.
    """
    
    def __init__(
        self,
        min_balance: Decimal,
        withdrawal_limit: Decimal,
        daily_transaction_limit: Optional[int] = None,
        monthly_transaction_limit: Optional[int] = None
    ):
        """
        Initialize the account rules service
        
        Args:
            min_balance: Minimum balance required for accounts
            withdrawal_limit: Maximum amount for a single withdrawal
            daily_transaction_limit: Maximum number of transactions per day (optional)
            monthly_transaction_limit: Maximum number of transactions per month (optional)
        """
        self.min_balance = Money(min_balance)
        self.withdrawal_limit = Money(withdrawal_limit)
        self.daily_transaction_limit = daily_transaction_limit
        self.monthly_transaction_limit = monthly_transaction_limit
        
        # Account type specific minimum balances
        self._account_type_min_balance = {
            AccountType.SAVINGS: self.min_balance,
            AccountType.CURRENT: Money("500.00"),
            AccountType.FIXED_DEPOSIT: Money("1000.00"),
            AccountType.LOAN: Money("0.00")
        }
    
    def validate_minimum_balance(self, account: Account, amount: Money) -> bool:
        """
        Check if a withdrawal would violate minimum balance requirements
        
        Args:
            account: The account to check
            amount: Amount to be withdrawn
            
        Returns:
            True if the withdrawal is valid, False otherwise
            
        Raises:
            ValueError: If the withdrawal would violate minimum balance requirements
        """
        min_required = self.get_minimum_balance_for_type(account.account_type)
        balance_after = account.balance - amount
        
        if balance_after < min_required:
            raise ValueError(
                f"Withdrawal of {amount} would cause balance ({balance_after}) to fall below "
                f"minimum required balance of {min_required} for {account.account_type.value} account"
            )
        
        return True
    
    def validate_withdrawal_limit(self, amount: Money) -> bool:
        """
        Check if a withdrawal exceeds the maximum withdrawal limit
        
        Args:
            amount: Amount to be withdrawn
            
        Returns:
            True if the withdrawal is valid, False otherwise
            
        Raises:
            ValueError: If the withdrawal amount exceeds the limit
        """
        if amount > self.withdrawal_limit:
            raise ValueError(f"Withdrawal amount {amount} exceeds limit of {self.withdrawal_limit}")
        
        return True
    
    def get_minimum_balance_for_type(self, account_type: AccountType) -> Money:
        """
        Get the minimum balance requirement for a specific account type
        
        Args:
            account_type: Type of account
            
        Returns:
            Minimum balance amount for the account type
        """
        return self._account_type_min_balance.get(account_type, self.min_balance)
    
    def can_close_account(self, account: Account) -> bool:
        """
        Check if an account can be closed
        
        Args:
            account: The account to check
            
        Returns:
            True if the account can be closed, False otherwise
            
        Raises:
            ValueError: If the account cannot be closed
        """
        # Check for outstanding balance for loan accounts
        if account.account_type == AccountType.LOAN and account.balance > Money("0.00"):
            raise ValueError("Cannot close loan account with outstanding balance")
        
        # Check for minimum holding period for fixed deposits
        # This is a simplified check - in a real system, we would check against the creation date
        if account.account_type == AccountType.FIXED_DEPOSIT:
            # Implementation would typically check if maturity date has been reached
            pass
        
        return True
    
    def validate_account_exists(self, account: Optional[Account]) -> bool:
        """
        Validate that an account exists
        
        Args:
            account: The account to check
            
        Returns:
            True if the account exists
            
        Raises:
            ValueError: If the account does not exist
        """
        if account is None:
            raise ValueError("Account does not exist")
        
        return True
    
    def validate_account_active(self, account: Account) -> bool:
        """
        Validate that an account is active
        
        Args:
            account: The account to check
            
        Returns:
            True if the account is active
            
        Raises:
            ValueError: If the account is not active
        """
        if not account.is_active():
            raise ValueError(f"Account is not active. Current status: {account.status.value}")
        
        return True

    def validate_account_status(self, account: Account) -> bool:
        """
        Check if the account is in a valid status for transactions
        
        Args:
            account: The account to check
            
        Returns:
            True if the account status is valid, False otherwise
            
        Raises:
            ValueError: If the account status is not valid for transactions
        """
        if account.status == AccountStatus.CLOSED:
            raise ValueError("Cannot perform operations on a closed account")
            
        if account.status == AccountStatus.BLOCKED:
            raise ValueError("Cannot perform operations on a blocked account")
            
        if account.status == AccountStatus.INACTIVE:
            raise ValueError("Cannot perform operations on an inactive account")
            
        return True
    
    def validate_transfer(
        self, 
        source_account: Account, 
        target_account: Account, 
        amount: Money
    ) -> bool:
        """
        Validate a transfer between accounts
        
        Args:
            source_account: Source account for the transfer
            target_account: Target account for the transfer
            amount: Amount to transfer
            
        Returns:
            True if the transfer is valid, False otherwise
            
        Raises:
            ValueError: If the transfer is not valid
        """
        # Check account statuses
        self.validate_account_status(source_account)
        self.validate_account_status(target_account)
        
        # Check withdrawal limit
        self.validate_withdrawal_limit(amount)
        
        # Check minimum balance
        self.validate_minimum_balance(source_account, amount)
        
        # Check currency match
        if source_account.currency != target_account.currency:
            raise ValueError(
                f"Cannot transfer between accounts with different currencies: "
                f"{source_account.currency} and {target_account.currency}"
            )
            
        return True
    
    def validate_account_type_specific_rules(self, account: Account, transaction_type: str, amount: Money) -> bool:
        """
        Validate account type specific rules for a transaction
        
        Args:
            account: The account to validate
            transaction_type: Type of transaction (deposit, withdrawal, transfer)
            amount: Transaction amount
            
        Returns:
            True if the transaction is valid according to account type rules
            
        Raises:
            ValueError: If the transaction violates account type specific rules
        """
        if account.account_type == AccountType.FIXED_DEPOSIT and transaction_type in ["withdrawal", "transfer"]:
            # Example rule: Cannot withdraw from fixed deposit before maturity
            # Note: In reality, we would check maturity date, but we don't have that property
            raise ValueError("Cannot withdraw or transfer from a fixed deposit account before maturity")
            
        if account.account_type == AccountType.LOAN and transaction_type == "withdrawal":
            # Example rule: Cannot withdraw from a loan account
            raise ValueError("Cannot withdraw from a loan account")
            
        if account.account_type == AccountType.SAVINGS:
            # Example rule: Savings accounts have a monthly withdrawal limit
            # This would require tracking withdrawals over time, simplified here
            pass
            
        return True
