"""
Transaction Service Use Cases

Application layer for transaction processing with comprehensive
business logic implementation and proper error handling.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from transaction_service.domain.entities import (
    Transaction, TransactionType, TransactionStatus, 
    TransactionChannel, Money, TransactionMetadata
)
from platform.shared.events import EventBus
from platform.shared.auth import require_permission


logger = logging.getLogger(__name__)


class TransactionRepository:
    """Repository interface for transaction persistence."""
    
    async def save(self, transaction: Transaction) -> None:
        """Save transaction to persistence store."""
        raise NotImplementedError
    
    async def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get transaction by ID."""
        raise NotImplementedError
    
    async def get_by_reference(self, reference_number: str) -> Optional[Transaction]:
        """Get transaction by reference number."""
        raise NotImplementedError
    
    async def get_by_account(
        self, 
        account_id: UUID, 
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """Get transactions for an account."""
        raise NotImplementedError
    
    async def get_by_customer(
        self, 
        customer_id: UUID,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Transaction]:
        """Get transactions for a customer."""
        raise NotImplementedError


class AccountService:
    """Interface for account operations."""
    
    async def get_balance(self, account_id: UUID) -> Money:
        """Get current account balance."""
        raise NotImplementedError
    
    async def check_sufficient_balance(
        self, 
        account_id: UUID, 
        amount: Money
    ) -> bool:
        """Check if account has sufficient balance."""
        raise NotImplementedError
    
    async def reserve_funds(
        self, 
        account_id: UUID, 
        amount: Money,
        transaction_id: UUID
    ) -> None:
        """Reserve funds for pending transaction."""
        raise NotImplementedError
    
    async def release_funds(
        self, 
        account_id: UUID, 
        amount: Money,
        transaction_id: UUID
    ) -> None:
        """Release reserved funds."""
        raise NotImplementedError


class CreateTransactionUseCase:
    """Use case for creating new transactions."""
    
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        account_service: AccountService,
        event_bus: EventBus
    ):
        self.transaction_repo = transaction_repo
        self.account_service = account_service
        self.event_bus = event_bus
    
    @require_permission("transaction:create")
    async def execute(
        self,
        customer_id: Optional[UUID] = None,
        channel: TransactionChannel = TransactionChannel.INTERNAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """Create a new transaction."""
        try:
            logger.info(f"Creating new transaction for customer {customer_id}")
            
            transaction = Transaction(customer_id=customer_id)
            transaction.channel = channel
            
            if metadata:
                transaction.metadata = TransactionMetadata(**metadata)
            
            await self.transaction_repo.save(transaction)
            
            logger.info(f"Transaction {transaction.transaction_id} created successfully")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to create transaction: {str(e)}")
            raise


class AddTransactionLegUseCase:
    """Use case for adding legs to transactions."""
    
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        account_service: AccountService,
        event_bus: EventBus
    ):
        self.transaction_repo = transaction_repo
        self.account_service = account_service
        self.event_bus = event_bus
    
    @require_permission("transaction:modify")
    async def execute(
        self,
        transaction_id: UUID,
        account_id: UUID,
        amount: Decimal,
        transaction_type: TransactionType,
        description: str,
        currency: str = "INR",
        reference: Optional[str] = None
    ) -> Transaction:
        """Add a leg to an existing transaction."""
        try:
            # Get transaction
            transaction = await self.transaction_repo.get_by_id(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            if transaction.status != TransactionStatus.PENDING:
                raise ValueError("Can only add legs to pending transactions")
            
            # Create money object
            money = Money(amount=amount, currency=currency)
            
            # Add leg based on type
            if transaction_type in [TransactionType.DEBIT, TransactionType.WITHDRAWAL]:
                transaction.add_debit_leg(account_id, money, description, reference)
            elif transaction_type in [TransactionType.CREDIT, TransactionType.DEPOSIT]:
                transaction.add_credit_leg(account_id, money, description, reference)
            else:
                raise ValueError(f"Unsupported transaction type: {transaction_type}")
            
            await self.transaction_repo.save(transaction)
            
            logger.info(f"Added {transaction_type} leg to transaction {transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to add transaction leg: {str(e)}")
            raise


class ProcessTransferUseCase:
    """Use case for processing account transfers."""
    
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        account_service: AccountService,
        event_bus: EventBus
    ):
        self.transaction_repo = transaction_repo
        self.account_service = account_service
        self.event_bus = event_bus
    
    @require_permission("transaction:transfer")
    async def execute(
        self,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: Decimal,
        description: str,
        customer_id: Optional[UUID] = None,
        currency: str = "INR",
        channel: TransactionChannel = TransactionChannel.INTERNAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """Process a transfer between accounts."""
        try:
            logger.info(f"Processing transfer: {amount} from {from_account_id} to {to_account_id}")
            
            # Validate inputs
            if from_account_id == to_account_id:
                raise ValueError("Cannot transfer to same account")
            
            if amount <= 0:
                raise ValueError("Transfer amount must be positive")
            
            money = Money(amount=amount, currency=currency)
            
            # Check sufficient balance
            sufficient_balance = await self.account_service.check_sufficient_balance(
                from_account_id, money
            )
            if not sufficient_balance:
                raise ValueError("Insufficient balance for transfer")
            
            # Create transaction
            transaction = Transaction(customer_id=customer_id)
            transaction.channel = channel
            
            if metadata:
                transaction.metadata = TransactionMetadata(**metadata)
            
            # Add debit leg (from account)
            transaction.add_debit_leg(
                account_id=from_account_id,
                amount=money,
                description=f"Transfer to {to_account_id}: {description}",
                reference=None
            )
            
            # Add credit leg (to account)
            transaction.add_credit_leg(
                account_id=to_account_id,
                amount=money,
                description=f"Transfer from {from_account_id}: {description}",
                reference=None
            )
            
            await self.transaction_repo.save(transaction)
            
            logger.info(f"Transfer transaction {transaction.transaction_id} created")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to process transfer: {str(e)}")
            raise


class AuthorizeTransactionUseCase:
    """Use case for authorizing transactions."""
    
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        account_service: AccountService,
        event_bus: EventBus
    ):
        self.transaction_repo = transaction_repo
        self.account_service = account_service
        self.event_bus = event_bus
    
    @require_permission("transaction:authorize")
    async def execute(
        self,
        transaction_id: UUID,
        authorized_by: UUID
    ) -> Transaction:
        """Authorize a pending transaction."""
        try:
            # Get transaction
            transaction = await self.transaction_repo.get_by_id(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            # Reserve funds for debit legs
            for leg in transaction.legs:
                if leg.is_debit():
                    await self.account_service.reserve_funds(
                        leg.account_id, leg.amount, transaction_id
                    )
            
            # Authorize transaction
            transaction.authorize(authorized_by)
            
            await self.transaction_repo.save(transaction)
            
            # Publish events
            for event in transaction.events:
                await self.event_bus.publish(event)
            
            logger.info(f"Transaction {transaction_id} authorized by {authorized_by}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to authorize transaction: {str(e)}")
            # Release any reserved funds on failure
            try:
                for leg in transaction.legs:
                    if leg.is_debit():
                        await self.account_service.release_funds(
                            leg.account_id, leg.amount, transaction_id
                        )
            except:
                pass
            raise


class CompleteTransactionUseCase:
    """Use case for completing transactions."""
    
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        account_service: AccountService,
        event_bus: EventBus
    ):
        self.transaction_repo = transaction_repo
        self.account_service = account_service
        self.event_bus = event_bus
    
    @require_permission("transaction:complete")
    async def execute(
        self,
        transaction_id: UUID,
        settlement_date: Optional[datetime] = None
    ) -> Transaction:
        """Complete a processing transaction."""
        try:
            # Get transaction
            transaction = await self.transaction_repo.get_by_id(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            # Complete transaction
            transaction.complete(settlement_date)
            
            await self.transaction_repo.save(transaction)
            
            # Publish events
            for event in transaction.events:
                await self.event_bus.publish(event)
            
            logger.info(f"Transaction {transaction_id} completed")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to complete transaction: {str(e)}")
            raise


class ReverseTransactionUseCase:
    """Use case for reversing transactions."""
    
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        account_service: AccountService,
        event_bus: EventBus
    ):
        self.transaction_repo = transaction_repo
        self.account_service = account_service
        self.event_bus = event_bus
    
    @require_permission("transaction:reverse")
    async def execute(
        self,
        transaction_id: UUID,
        reversed_by: UUID,
        reason: str
    ) -> Transaction:
        """Reverse a completed transaction."""
        try:
            # Get original transaction
            original_transaction = await self.transaction_repo.get_by_id(transaction_id)
            if not original_transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            # Create reversal
            reversal_transaction = original_transaction.reverse(reversed_by, reason)
            
            # Save reversal transaction
            await self.transaction_repo.save(reversal_transaction)
            
            # Update original transaction status
            original_transaction.status = TransactionStatus.REVERSED
            await self.transaction_repo.save(original_transaction)
            
            # Publish events
            for event in original_transaction.events:
                await self.event_bus.publish(event)
            
            logger.info(f"Transaction {transaction_id} reversed")
            return reversal_transaction
            
        except Exception as e:
            logger.error(f"Failed to reverse transaction: {str(e)}")
            raise


class GetTransactionUseCase:
    """Use case for retrieving transactions."""
    
    def __init__(self, transaction_repo: TransactionRepository):
        self.transaction_repo = transaction_repo
    
    @require_permission("transaction:read")
    async def execute(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get transaction by ID."""
        return await self.transaction_repo.get_by_id(transaction_id)


class GetTransactionByReferenceUseCase:
    """Use case for retrieving transactions by reference."""
    
    def __init__(self, transaction_repo: TransactionRepository):
        self.transaction_repo = transaction_repo
    
    @require_permission("transaction:read")
    async def execute(self, reference_number: str) -> Optional[Transaction]:
        """Get transaction by reference number."""
        return await self.transaction_repo.get_by_reference(reference_number)


class GetAccountTransactionsUseCase:
    """Use case for retrieving account transactions."""
    
    def __init__(self, transaction_repo: TransactionRepository):
        self.transaction_repo = transaction_repo
    
    @require_permission("transaction:read")
    async def execute(
        self, 
        account_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """Get transactions for an account."""
        return await self.transaction_repo.get_by_account(account_id, limit, offset)


# Export public interface
__all__ = [
    "CreateTransactionUseCase",
    "AddTransactionLegUseCase", 
    "ProcessTransferUseCase",
    "AuthorizeTransactionUseCase",
    "CompleteTransactionUseCase",
    "ReverseTransactionUseCase",
    "GetTransactionUseCase",
    "GetTransactionByReferenceUseCase",
    "GetAccountTransactionsUseCase",
    "TransactionRepository",
    "AccountService"
]
