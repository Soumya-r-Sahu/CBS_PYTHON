"""
Transaction Service

This module provides application services for handling transactions,
leveraging the centralized utilities for validation and business rules.
"""

import uuid
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple

from core_banking.accounts.application.interfaces.account_repository import AccountRepositoryInterface
from core_banking.accounts.domain.entities.account import Account, AccountStatus
from core_banking.transactions.application.interfaces.transaction_repository import TransactionRepositoryInterface
from core_banking.transactions.domain.entities.transaction import (
    Transaction, TransactionType, TransactionStatus
)
from core_banking.utils.core_banking_utils import (
    ValidationException,
    BusinessRuleException,
    DatabaseException,
    MoneyUtility
)


class TransactionService:
    """Service for handling banking transactions"""
    
    def __init__(
        self,
        transaction_repository: TransactionRepositoryInterface,
        account_repository: AccountRepositoryInterface
    ):
        """
        Initialize transaction service
        
        Args:
            transaction_repository: Repository for transaction data
            account_repository: Repository for account data
        """
        self.transaction_repository = transaction_repository
        self.account_repository = account_repository
        self.logger = logging.getLogger(__name__)
    
    def deposit(
        self,
        account_id: uuid.UUID,
        amount: Decimal,
        description: str,
        reference_number: Optional[str] = None,
        processed_by: Optional[str] = None
    ) -> Transaction:
        """
        Process a deposit transaction
        
        Args:
            account_id: ID of the account to deposit into
            amount: Amount to deposit
            description: Description of the transaction
            reference_number: Optional reference number
            processed_by: ID or name of the user/system processing the transaction
            
        Returns:
            The completed transaction
            
        Raises:
            ValidationException: If the transaction data is invalid
            BusinessRuleException: If the transaction violates business rules
            DatabaseException: If there's an error updating the database
        """
        # Validate amount
        if amount <= Decimal('0'):
            raise ValidationException("Deposit amount must be positive", "INVALID_AMOUNT")
        
        # Get the account
        account = self.account_repository.get_by_id(account_id)
        if not account:
            raise ValidationException(f"Account with ID {account_id} not found", "ACCOUNT_NOT_FOUND")
        
        # Check if account is active
        if account.status != AccountStatus.ACTIVE:
            raise BusinessRuleException(
                f"Cannot deposit to an account with status {account.status.value}",
                "INACTIVE_ACCOUNT"
            )
        
        # Generate transaction ID
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8]}"
        
        # Create the transaction
        transaction = Transaction(
            transaction_id=transaction_id,
            account_id=account_id,
            amount=amount,
            transaction_type=TransactionType.DEPOSIT,
            description=description,
            reference_number=reference_number,
            destination_account_id=account_id,
            currency=account.currency
        )
        
        try:
            # Save the transaction
            saved_transaction = self.transaction_repository.create(transaction)
            
            # Update account balance
            account.balance += amount
            self.account_repository.update(account)
            
            # Mark transaction as completed
            saved_transaction.complete(processed_by)
            self.transaction_repository.update(saved_transaction)
            
            self.logger.info(f"Deposit of {amount} to account {account_id} completed successfully")
            return saved_transaction
            
        except Exception as e:
            self.logger.error(f"Error processing deposit: {str(e)}")
            if isinstance(e, (ValidationException, BusinessRuleException, DatabaseException)):
                raise
            raise DatabaseException(f"Error processing deposit: {str(e)}", "TRANSACTION_PROCESSING_ERROR")
    
    def withdraw(
        self,
        account_id: uuid.UUID,
        amount: Decimal,
        description: str,
        reference_number: Optional[str] = None,
        processed_by: Optional[str] = None
    ) -> Transaction:
        """
        Process a withdrawal transaction
        
        Args:
            account_id: ID of the account to withdraw from
            amount: Amount to withdraw
            description: Description of the transaction
            reference_number: Optional reference number
            processed_by: ID or name of the user/system processing the transaction
            
        Returns:
            The completed transaction
            
        Raises:
            ValidationException: If the transaction data is invalid
            BusinessRuleException: If the transaction violates business rules
            DatabaseException: If there's an error updating the database
        """
        # Validate amount
        if amount <= Decimal('0'):
            raise ValidationException("Withdrawal amount must be positive", "INVALID_AMOUNT")
        
        # Get the account
        account = self.account_repository.get_by_id(account_id)
        if not account:
            raise ValidationException(f"Account with ID {account_id} not found", "ACCOUNT_NOT_FOUND")
        
        # Check if account is active
        if account.status != AccountStatus.ACTIVE:
            raise BusinessRuleException(
                f"Cannot withdraw from an account with status {account.status.value}",
                "INACTIVE_ACCOUNT"
            )
        
        # Check if account has sufficient balance
        if account.balance < amount:
            # Check for overdraft if it's a current account
            overdraft_limit = account.overdraft_limit or Decimal('0')
            if account.balance + overdraft_limit < amount:
                raise BusinessRuleException(
                    "Insufficient funds for withdrawal",
                    "INSUFFICIENT_FUNDS"
                )
        
        # Generate transaction ID
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8]}"
        
        # Create the transaction
        transaction = Transaction(
            transaction_id=transaction_id,
            account_id=account_id,
            amount=amount,
            transaction_type=TransactionType.WITHDRAWAL,
            description=description,
            reference_number=reference_number,
            source_account_id=account_id,
            currency=account.currency
        )
        
        try:
            # Save the transaction
            saved_transaction = self.transaction_repository.create(transaction)
            
            # Update account balance
            account.balance -= amount
            self.account_repository.update(account)
            
            # Mark transaction as completed
            saved_transaction.complete(processed_by)
            self.transaction_repository.update(saved_transaction)
            
            self.logger.info(f"Withdrawal of {amount} from account {account_id} completed successfully")
            return saved_transaction
            
        except Exception as e:
            self.logger.error(f"Error processing withdrawal: {str(e)}")
            if isinstance(e, (ValidationException, BusinessRuleException, DatabaseException)):
                raise
            raise DatabaseException(f"Error processing withdrawal: {str(e)}", "TRANSACTION_PROCESSING_ERROR")
    
    def transfer(
        self,
        source_account_id: uuid.UUID,
        destination_account_id: uuid.UUID,
        amount: Decimal,
        description: str,
        reference_number: Optional[str] = None,
        processed_by: Optional[str] = None
    ) -> Tuple[Transaction, Transaction]:
        """
        Process a transfer between accounts
        
        Args:
            source_account_id: ID of the source account
            destination_account_id: ID of the destination account
            amount: Amount to transfer
            description: Description of the transaction
            reference_number: Optional reference number
            processed_by: ID or name of the user/system processing the transaction
            
        Returns:
            Tuple of (source transaction, destination transaction)
            
        Raises:
            ValidationException: If the transaction data is invalid
            BusinessRuleException: If the transaction violates business rules
            DatabaseException: If there's an error updating the database
        """
        # Validate amount
        if amount <= Decimal('0'):
            raise ValidationException("Transfer amount must be positive", "INVALID_AMOUNT")
        
        # Validate accounts
        source_account = self.account_repository.get_by_id(source_account_id)
        if not source_account:
            raise ValidationException(f"Source account with ID {source_account_id} not found", "SOURCE_ACCOUNT_NOT_FOUND")
        
        destination_account = self.account_repository.get_by_id(destination_account_id)
        if not destination_account:
            raise ValidationException(f"Destination account with ID {destination_account_id} not found", "DESTINATION_ACCOUNT_NOT_FOUND")
        
        # Check if accounts are active
        if source_account.status != AccountStatus.ACTIVE:
            raise BusinessRuleException(
                f"Cannot transfer from an account with status {source_account.status.value}",
                "INACTIVE_SOURCE_ACCOUNT"
            )
        
        if destination_account.status != AccountStatus.ACTIVE:
            raise BusinessRuleException(
                f"Cannot transfer to an account with status {destination_account.status.value}",
                "INACTIVE_DESTINATION_ACCOUNT"
            )
        
        # Check if source account has sufficient balance
        if source_account.balance < amount:
            # Check for overdraft if it's a current account
            overdraft_limit = source_account.overdraft_limit or Decimal('0')
            if source_account.balance + overdraft_limit < amount:
                raise BusinessRuleException(
                    "Insufficient funds for transfer",
                    "INSUFFICIENT_FUNDS"
                )
        
        # Generate transaction IDs and reference number if not provided
        transfer_ref = reference_number or f"TRF{datetime.now().strftime('%Y%m%d%H%M%S')}"
        source_transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}S{str(uuid.uuid4())[:8]}"
        dest_transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}D{str(uuid.uuid4())[:8]}"
        
        # Handle currency conversion if needed
        final_amount = amount
        if source_account.currency != destination_account.currency:
            # In a real system, we would use a currency conversion service
            # For now, we'll assume a simple conversion factor
            final_amount = MoneyUtility.convert_currency(
                amount, 
                source_account.currency, 
                destination_account.currency
            )
        
        # Create the source transaction (withdrawal)
        source_transaction = Transaction(
            transaction_id=source_transaction_id,
            account_id=source_account_id,
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            description=f"{description} - Transfer to {destination_account.account_number}",
            reference_number=transfer_ref,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            currency=source_account.currency
        )
        
        # Create the destination transaction (deposit)
        destination_transaction = Transaction(
            transaction_id=dest_transaction_id,
            account_id=destination_account_id,
            amount=final_amount,
            transaction_type=TransactionType.TRANSFER,
            description=f"{description} - Transfer from {source_account.account_number}",
            reference_number=transfer_ref,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            currency=destination_account.currency
        )
        
        try:
            # Save both transactions first
            saved_source_transaction = self.transaction_repository.create(source_transaction)
            saved_dest_transaction = self.transaction_repository.create(destination_transaction)
            
            # Update account balances
            source_account.balance -= amount
            destination_account.balance += final_amount
            
            self.account_repository.update(source_account)
            self.account_repository.update(destination_account)
            
            # Mark transactions as completed
            saved_source_transaction.complete(processed_by)
            saved_dest_transaction.complete(processed_by)
            
            self.transaction_repository.update(saved_source_transaction)
            self.transaction_repository.update(saved_dest_transaction)
            
            self.logger.info(f"Transfer of {amount} from account {source_account_id} to {destination_account_id} completed successfully")
            return (saved_source_transaction, saved_dest_transaction)
            
        except Exception as e:
            self.logger.error(f"Error processing transfer: {str(e)}")
            if isinstance(e, (ValidationException, BusinessRuleException, DatabaseException)):
                raise
            raise DatabaseException(f"Error processing transfer: {str(e)}", "TRANSACTION_PROCESSING_ERROR")
    
    def get_transaction_history(
        self,
        account_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """
        Get transaction history for an account
        
        Args:
            account_id: ID of the account
            start_date: Filter by start date
            end_date: Filter by end date
            transaction_type: Filter by transaction type
            status: Filter by transaction status
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of transactions
        """
        try:
            return self.transaction_repository.get_account_transactions(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type,
                status=status,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            self.logger.error(f"Error retrieving transaction history: {str(e)}")
            if isinstance(e, DatabaseException):
                raise
            raise DatabaseException(f"Error retrieving transaction history: {str(e)}", "QUERY_ERROR")
