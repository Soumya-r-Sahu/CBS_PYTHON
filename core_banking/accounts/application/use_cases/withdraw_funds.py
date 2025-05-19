"""
Withdraw Funds Use Case

This module defines the use case for withdrawing funds from an account.
"""

from decimal import Decimal
from typing import Dict, Any
from uuid import UUID

from ...domain.entities.account import Account
from ...domain.entities.transaction import Transaction, TransactionType, TransactionStatus
from ...domain.services.account_rules import AccountRules
from ...domain.value_objects.money import Money
from ..interfaces.account_repository import AccountRepository
from ..interfaces.transaction_repository import TransactionRepository
from ..interfaces.notification_service import NotificationService

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class WithdrawFundsUseCase:
    """
    Use case for withdrawing funds from an account
    
    This use case orchestrates the process of withdrawing funds from an account,
    creating a transaction record, and notifying the customer.
    """   
    def __init__(
        self,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
        notification_service: NotificationService,
        account_rules: AccountRules
    ):
        """
        Initialize the use case
        
        Args:
            account_repository: Repository for account data access
            transaction_repository: Repository for transaction data access
            notification_service: Service for sending notifications
            account_rules: Service for enforcing account rules
        """
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository
        self.notification_service = notification_service
        self.account_rules = account_rules
    
    def execute(
        self,
        account_id: UUID,
        amount: Decimal,
        description: str = None,
        reference_id: str = None
    ) -> Dict[str, Any]:
        """
        Execute the withdraw funds use case
        
        Args:
            account_id: ID of the account to withdraw from
            amount: Amount to withdraw
            description: Optional transaction description
            reference_id: Optional external reference ID
            
        Returns:
            Result dictionary with transaction details
            
        Raises:
            ValueError: If the account does not exist
            ValueError: If the account is not active
            ValueError: If the amount is not positive
            ValueError: If there are insufficient funds
        """
        # Convert amount to Money value object
        money_amount = Money(amount)
          # Get the account
        account = self.account_repository.get_by_id(account_id)
        
        # Validate that the account exists and is active
        self.account_rules.validate_account_exists(account)
        self.account_rules.validate_account_active(account)
        
        # Validate withdrawal against account rules
        self.account_rules.validate_withdrawal_limit(money_amount)
        self.account_rules.validate_minimum_balance(account, money_amount)
        
        # Create a withdrawal transaction
        transaction = Transaction.create(
            account_id=account_id,
            amount=money_amount,
            description=description,
            reference_id=reference_id
        )
        
        # Save the pending transaction
        self.transaction_repository.save(transaction)
        
        try:
            # Perform the withdrawal on the account
            account.withdraw(money_amount)
            
            # Update the account in the repository
            self.account_repository.update(account)
            
            # Complete the transaction
            transaction.complete(account.balance)
            self.transaction_repository.update(transaction)
            
            # Send notification to the customer
            self.notification_service.send_withdrawal_notification(
                account_id=account_id,
                amount=money_amount.value,
                balance=account.balance.value,
                transaction_id=transaction.transaction_id
            )
            
            # Return the result
            return {
                "success": True,
                "transaction_id": str(transaction.transaction_id),
                "amount": str(money_amount.value),
                "balance": str(account.balance.value),
                "status": transaction.status.value,
                "timestamp": transaction.completed_at.isoformat()
            }
            
        except ValueError as e:
            # If withdrawal fails, mark the transaction as failed
            transaction.fail(str(e))
            self.transaction_repository.update(transaction)
            
            # Return error result
            return {
                "success": False,
                "error": str(e),
                "transaction_id": str(transaction.transaction_id),
                "status": transaction.status.value
            }
