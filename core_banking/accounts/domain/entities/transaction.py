"""
Transaction Entity

This module defines the Transaction entity representing a bank transaction.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class TransactionType(Enum):
    """Transaction types"""
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    INTEREST = "INTEREST"
    FEE = "FEE"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"


class TransactionStatus(Enum):
    """Transaction status"""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    CANCELLED = "CANCELLED"


@dataclass
class Transaction:
    """
    Transaction entity
    
    Represents a financial transaction with all relevant properties.
    """
    account_id: str
    transaction_type: TransactionType
    amount: Decimal
    status: TransactionStatus = TransactionStatus.PENDING
    reference_id: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    balance_after: Optional[Decimal] = None
    fee: Decimal = field(default=Decimal('0.00'))
    id: UUID = field(default_factory=uuid4)
    source_account: Optional[str] = None
    destination_account: Optional[str] = None
    related_transaction_id: Optional[UUID] = None
    target_account_id: Optional[str] = None
    currency: str = "INR"
    
    def __post_init__(self):
        """
        Validate transaction after initialization
        
        Raises:
            ValueError: If any of the transaction properties are invalid
        """
        # Validate amount is positive
        if self.amount <= Decimal('0'):
            raise ValueError("Transaction amount must be positive")
            
        # Validate transaction type
        if self.transaction_type not in TransactionType:
            raise ValueError(f"Invalid transaction type: {self.transaction_type}")
            
        # Validate status
        if self.status not in TransactionStatus:
            raise ValueError(f"Invalid transaction status: {self.status}")
            
        # Validate target account for transfer transactions
        if self.transaction_type == TransactionType.TRANSFER and not self.target_account_id:
            raise ValueError("Target account ID is required for transfer transactions")
            
        # Validate currency code
        if not self.currency or len(self.currency.strip()) != 3:
            raise ValueError("Currency must be a valid 3-letter ISO currency code")
    
    def complete(self, balance_after: Decimal) -> None:
        """
        Mark the transaction as completed
        
        Args:
            balance_after: The account balance after the transaction
        """
        self.status = TransactionStatus.COMPLETED
        self.balance_after = balance_after
        
    def fail(self, reason: str = None) -> None:
        """
        Mark the transaction as failed
        
        Args:
            reason: The reason why the transaction failed
        """
        self.status = TransactionStatus.FAILED
        if reason:
            self.description = f"{self.description or ''} - Failed: {reason}".strip()
    
    def reverse(self) -> 'Transaction':
        """
        Create a reversal transaction
        
        Returns:
            A new transaction that reverses this transaction
        """
        if self.status != TransactionStatus.COMPLETED:
            raise ValueError("Only completed transactions can be reversed")
            
        reversed_type = self._get_reversed_type()
        
        return Transaction(
            account_id=self.account_id,
            transaction_type=reversed_type,
            amount=self.amount,
            reference_id=f"REVERSAL-{self.reference_id}" if self.reference_id else None,
            description=f"Reversal of {self.transaction_type.value} transaction {self.id}",
            related_transaction_id=self.id,
            target_account_id=self.target_account_id,
            currency=self.currency
        )
    
    def _get_reversed_type(self) -> TransactionType:
        """Get the transaction type for a reversal transaction"""
        reverse_types = {
            TransactionType.DEPOSIT: TransactionType.WITHDRAWAL,
            TransactionType.WITHDRAWAL: TransactionType.DEPOSIT,
            TransactionType.TRANSFER: TransactionType.TRANSFER,  # Special case, handled separately
            TransactionType.PAYMENT: TransactionType.REFUND,
            TransactionType.FEE: TransactionType.ADJUSTMENT,
            TransactionType.INTEREST: TransactionType.ADJUSTMENT,
        }
        return reverse_types.get(self.transaction_type, TransactionType.ADJUSTMENT)
        
    def is_completed(self) -> bool:
        """
        Check if the transaction is completed
        
        Returns:
            True if the transaction is completed, False otherwise
        """
        return self.status == TransactionStatus.COMPLETED
        
    def is_debit(self) -> bool:
        """
        Check if the transaction is a debit transaction
        
        Returns:
            True if the transaction is a debit transaction, False otherwise
        """
        return self.transaction_type in [
            TransactionType.WITHDRAWAL, 
            TransactionType.TRANSFER, 
            TransactionType.PAYMENT,
            TransactionType.FEE
        ]
        
    def is_credit(self) -> bool:
        """
        Check if the transaction is a credit transaction
        
        Returns:
            True if the transaction is a credit transaction, False otherwise
        """
        return self.transaction_type in [
            TransactionType.DEPOSIT, 
            TransactionType.INTEREST, 
            TransactionType.REFUND
        ]
