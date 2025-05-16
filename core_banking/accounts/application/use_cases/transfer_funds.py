"""
Transfer Funds Use Case

This module defines the use case for transferring funds between accounts.
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


class TransferFundsUseCase:
    """
    Use case for transferring funds between accounts
    
    This use case orchestrates the process of transferring funds between two accounts,
    creating transaction records for both accounts, and notifying customers.
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
        source_account_id: UUID,
        target_account_id: UUID,
        amount: Decimal,
        description: str = None,
        reference_id: str = None
    ) -> Dict[str, Any]:
        """
        Execute the transfer funds use case
        
        Args:
            source_account_id: ID of the source account
            target_account_id: ID of the target account
            amount: Amount to transfer
            description: Optional transaction description
            reference_id: Optional external reference ID
            
        Returns:
            Result dictionary with transaction details
            
        Raises:
            ValueError: If either account does not exist
            ValueError: If the source account is not active
            ValueError: If the target account is not active
            ValueError: If the amount is not positive
            ValueError: If there are insufficient funds
        """
        # Convert amount to Money value object
        money_amount = Money(amount)
        
        # Validate the amount using AccountRules
        self.account_rules.validate_withdrawal_limit(money_amount)
        
        # Get the source account
        source_account = self.account_repository.get_by_id(source_account_id)
        
        # Get the target account
        target_account = self.account_repository.get_by_id(target_account_id)
        
        # Validate accounts using AccountRules
        self.account_rules.validate_account_exists(source_account)
        self.account_rules.validate_account_exists(target_account)
        self.account_rules.validate_account_active(source_account)
        self.account_rules.validate_account_active(target_account)
        self.account_rules.validate_minimum_balance(source_account, money_amount)
        
        # Validate the transfer specifically
        self.account_rules.validate_transfer(source_account, target_account, money_amount)
        
        # Create the transfer transactions
        outgoing_tx, incoming_tx = Transaction.create_transfer(
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            amount=money_amount,
            description=description,
            reference_id=reference_id
        )
        
        # Save the pending transactions
        self.transaction_repository.save(outgoing_tx)
        self.transaction_repository.save(incoming_tx)
        
        try:
            # Perform the withdrawal from the source account
            source_account.withdraw(money_amount)
            
            # Update the source account in the repository
            self.account_repository.update(source_account)
            
            # Perform the deposit to the target account
            target_account.deposit(money_amount)
            
            # Update the target account in the repository
            self.account_repository.update(target_account)
            
            # Complete the transactions
            outgoing_tx.complete(source_account.balance)
            incoming_tx.complete(target_account.balance)
            
            # Update the transactions in the repository
            self.transaction_repository.update(outgoing_tx)
            self.transaction_repository.update(incoming_tx)
            
            # Send notifications to both customers
            self.notification_service.send_transfer_notification(
                source_account_id=source_account_id,
                target_account_id=target_account_id,
                amount=money_amount.value,
                balance=source_account.balance.value,
                transaction_id=outgoing_tx.transaction_id
            )
            
            # Return the result
            return {
                "success": True,
                "source_transaction_id": str(outgoing_tx.transaction_id),
                "target_transaction_id": str(incoming_tx.transaction_id),
                "amount": str(money_amount.value),
                "source_balance": str(source_account.balance.value),
                "target_balance": str(target_account.balance.value),
                "status": outgoing_tx.status.value,
                "timestamp": outgoing_tx.completed_at.isoformat()
            }
            
        except ValueError as e:
            # If transfer fails, mark both transactions as failed
            outgoing_tx.fail(str(e))
            incoming_tx.fail(str(e))
            self.transaction_repository.update(outgoing_tx)
            self.transaction_repository.update(incoming_tx)
            
            # Return error result
            return {
                "success": False,
                "error": str(e),
                "source_transaction_id": str(outgoing_tx.transaction_id),
                "target_transaction_id": str(incoming_tx.transaction_id),
                "status": outgoing_tx.status.value
            }
