"""
Transaction Entity

This module defines the Transaction entity for the Core Banking System.
"""

import time
import random
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal, Dict, Any

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



@dataclass
class Transaction:
    """Entity representing an ATM transaction"""
    
    amount: Decimal
    account_id: int
    transaction_type: Literal[
        "ATM_WITHDRAWAL", "ATM_DEPOSIT", "ATM_INQUIRY", 
        "ATM_TRANSFER", "ATM_FEE", "ATM_MINI_STATEMENT"
    ]
    description: str
    transaction_id: Optional[str] = None
    status: Literal["PENDING", "COMPLETED", "FAILED", "REVERSED"] = "PENDING"
    timestamp: datetime = None
    balance_before: Optional[Decimal] = None
    balance_after: Optional[Decimal] = None
    fee: Decimal = Decimal('0')
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.transaction_id is None:
            self.transaction_id = self._generate_transaction_id()
            
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
        if self.metadata is None:
            self.metadata = {}
    
    def _generate_transaction_id(self) -> str:
        """Generate a unique transaction ID"""
        prefix = "ATM"
        timestamp = time.strftime('%Y%m%d%H%M%S')
        random_digits = random.randint(1000, 9999)
        return f"{prefix}{timestamp}{random_digits}"
    
    def complete(self, balance_before: Decimal, balance_after: Decimal) -> None:
        """Mark transaction as complete and record balances"""
        self.status = "COMPLETED"
        self.balance_before = balance_before
        self.balance_after = balance_after
    
    def fail(self, reason: str = None) -> None:
        """Mark transaction as failed"""
        self.status = "FAILED"
        if reason:
            self.metadata["failure_reason"] = reason
    
    def reverse(self, reason: str = None) -> None:
        """Mark transaction as reversed"""
        self.status = "REVERSED"
        if reason:
            self.metadata["reversal_reason"] = reason
    
    def total_amount(self) -> Decimal:
        """Get total amount including fee"""
        if self.transaction_type in ["ATM_WITHDRAWAL", "ATM_TRANSFER"]:
            return self.amount + self.fee
        return self.amount
    
    def is_debit(self) -> bool:
        """Check if transaction is a debit (reduces balance)"""
        return self.transaction_type in ["ATM_WITHDRAWAL", "ATM_TRANSFER", "ATM_FEE"]
