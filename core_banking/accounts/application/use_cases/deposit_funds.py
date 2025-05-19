"""
Deposit Funds Use Case

This module implements the use case for depositing funds into an account.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from uuid import UUID

from ...domain.entities.account import Account
from ...domain.entities.transaction import Transaction, TransactionType, TransactionStatus
from ...domain.validators.account_validator import AccountValidator
from ..interfaces.account_repository import AccountRepositoryInterface
from ..interfaces.transaction_repository import TransactionRepositoryInterface
from ..interfaces.notification_service import NotificationServiceInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class DepositFundsUseCase:
    """Use case for depositing funds into an account"""
    
    def __init__(
        self,
        account_repository: AccountRepositoryInterface,
        transaction_repository: TransactionRepositoryInterface,
        notification_service: NotificationServiceInterface
    ):
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository
        self.notification_service = notification_service
    
    def execute(
        self,
        account_number: str,
        amount: Decimal,
        reference_id: str = None,
        description: str = None
    ) -> Dict[str, Any]:
        """
        Execute the deposit funds use case
        
        Args:
            account_number: The account number
            amount: The amount to deposit
            reference_id: Optional reference ID
            description: Optional description
            
        Returns:
            Dictionary with deposit result
        """
        # Get account
        account = self.account_repository.get_by_account_number(account_number)
        if not account:
            return {
                "success": False,
                "message": "Account not found",
                "errors": ["Account not found"]
            }
        
        # Validate deposit
        validation = AccountValidator.validate_deposit(account, amount)
        if not validation["valid"]:
            return {
                "success": False,
                "message": "Invalid deposit",
                "errors": validation["errors"]
            }
        
        # Create transaction
        transaction = Transaction(
            account_id=account.account_number,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            status=TransactionStatus.PENDING,
            reference_id=reference_id,
            description=description or "Deposit"
        )
        
        try:
            # Process the deposit
            if not account.deposit(amount):
                return {
                    "success": False,
                    "message": "Failed to deposit funds",
                    "errors": ["Failed to deposit funds"]
                }
            
            # Update account in repository
            updated_account = self.account_repository.update(account)
            
            # Complete the transaction
            transaction.complete(balance_after=updated_account.balance)
            created_transaction = self.transaction_repository.create(transaction)
            
            # Send notification
            try:
                self.notification_service.send_transaction_notification(
                    account_number=account.account_number,
                    transaction_type="DEPOSIT",
                    amount=amount,
                    balance=updated_account.balance,
                    timestamp=transaction.timestamp.isoformat(),
                    reference_id=reference_id
                )
            except Exception:
                # Don't fail the operation if notification fails
                pass
            
            return {
                "success": True,
                "message": "Funds deposited successfully",
                "data": {
                    "transaction_id": str(created_transaction.id),
                    "account_number": account.account_number,
                    "amount": str(amount),
                    "balance": str(updated_account.balance),
                    "timestamp": transaction.timestamp.isoformat(),
                    "reference_id": reference_id
                }
            }
        except Exception as e:
            # If anything fails, mark the transaction as failed
            try:
                transaction.fail()
                self.transaction_repository.create(transaction)
            except Exception:
                pass
            
            return {
                "success": False,
                "message": f"Failed to process deposit: {str(e)}",
                "errors": [str(e)]
            }
