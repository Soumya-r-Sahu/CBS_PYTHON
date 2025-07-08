"""
Account Domain Entities
Business entities representing bank accounts
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal
import uuid


class AccountType(str, Enum):
    """Account type enumeration"""
    SAVINGS = "savings"
    CURRENT = "current"
    FIXED_DEPOSIT = "fixed_deposit"
    RECURRING_DEPOSIT = "recurring_deposit"
    LOAN = "loan"
    CREDIT_CARD = "credit_card"


class AccountStatus(str, Enum):
    """Account status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FROZEN = "frozen"
    CLOSED = "closed"
    DORMANT = "dormant"


class TransactionType(str, Enum):
    """Transaction type enumeration"""
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionStatus(str, Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


@dataclass
class Money:
    """Money value object"""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency is required")
        
        # Round to 2 decimal places for currency
        self.amount = self.amount.quantize(Decimal('0.01'))
    
    def add(self, other: 'Money') -> 'Money':
        """Add money amounts"""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """Subtract money amounts"""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError("Insufficient funds")
        return Money(result_amount, self.currency)
    
    def is_greater_than(self, other: 'Money') -> bool:
        """Compare if this amount is greater than other"""
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount > other.amount
    
    def is_greater_than_or_equal(self, other: 'Money') -> bool:
        """Compare if this amount is greater than or equal to other"""
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount >= other.amount
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount}"


@dataclass
class AccountLimits:
    """Account limits value object"""
    daily_withdrawal_limit: Money
    daily_transfer_limit: Money
    monthly_transaction_limit: Money
    minimum_balance: Money
    maximum_balance: Optional[Money] = None
    
    def can_withdraw(self, amount: Money, daily_withdrawn: Money) -> bool:
        """Check if withdrawal is within limits"""
        return (daily_withdrawn.add(amount).is_greater_than_or_equal(self.daily_withdrawal_limit) == False)
    
    def can_transfer(self, amount: Money, daily_transferred: Money) -> bool:
        """Check if transfer is within limits"""
        return (daily_transferred.add(amount).is_greater_than_or_equal(self.daily_transfer_limit) == False)


@dataclass
class InterestRate:
    """Interest rate configuration"""
    rate: Decimal  # Annual interest rate as percentage
    calculation_method: str = "daily"  # daily, monthly, quarterly, annually
    compounding_frequency: str = "monthly"  # daily, monthly, quarterly, annually
    effective_from: datetime = field(default_factory=datetime.utcnow)
    effective_to: Optional[datetime] = None
    
    def __post_init__(self):
        if self.rate < 0:
            raise ValueError("Interest rate cannot be negative")
        if self.rate > 100:
            raise ValueError("Interest rate cannot exceed 100%")


@dataclass
class Transaction:
    """Transaction entity"""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str = ""
    transaction_type: TransactionType = TransactionType.CREDIT
    amount: Money = field(default_factory=lambda: Money(Decimal('0')))
    balance_after: Money = field(default_factory=lambda: Money(Decimal('0')))
    description: str = ""
    reference_number: str = ""
    transaction_date: datetime = field(default_factory=datetime.utcnow)
    value_date: datetime = field(default_factory=datetime.utcnow)
    status: TransactionStatus = TransactionStatus.PENDING
    channel: str = ""  # ATM, Online, Branch, Mobile
    location: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None
    
    def __post_init__(self):
        if not self.account_id:
            raise ValueError("Account ID is required")
        if not self.reference_number:
            self.reference_number = f"TXN{self.transaction_id[:8].upper()}"
    
    def mark_completed(self):
        """Mark transaction as completed"""
        self.status = TransactionStatus.COMPLETED
    
    def mark_failed(self, reason: str = ""):
        """Mark transaction as failed"""
        self.status = TransactionStatus.FAILED
        if reason:
            self.metadata["failure_reason"] = reason
    
    def reverse(self, reversed_by: str = "") -> 'Transaction':
        """Create a reversal transaction"""
        reversal_type = TransactionType.DEBIT if self.transaction_type == TransactionType.CREDIT else TransactionType.CREDIT
        
        reversal = Transaction(
            account_id=self.account_id,
            transaction_type=reversal_type,
            amount=self.amount,
            description=f"Reversal of {self.description}",
            reference_number=f"REV{self.reference_number}",
            channel=self.channel,
            metadata={
                "original_transaction_id": self.transaction_id,
                "reversal_reason": "Transaction reversal",
                "reversed_by": reversed_by
            },
            created_by=reversed_by
        )
        
        # Mark original transaction as reversed
        self.status = TransactionStatus.REVERSED
        self.metadata["reversed_by"] = reversed_by
        self.metadata["reversal_transaction_id"] = reversal.transaction_id
        
        return reversal


@dataclass
class Account:
    """Account aggregate root"""
    account_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_number: str = ""
    customer_id: str = ""
    account_type: AccountType = AccountType.SAVINGS
    account_name: str = ""
    status: AccountStatus = AccountStatus.ACTIVE
    balance: Money = field(default_factory=lambda: Money(Decimal('0')))
    available_balance: Money = field(default_factory=lambda: Money(Decimal('0')))
    currency: str = "USD"
    limits: Optional[AccountLimits] = None
    interest_rate: Optional[InterestRate] = None
    branch_code: str = ""
    product_code: str = ""
    opened_date: datetime = field(default_factory=datetime.utcnow)
    last_transaction_date: Optional[datetime] = None
    dormant_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    version: int = 1
    
    def __post_init__(self):
        if not self.customer_id:
            raise ValueError("Customer ID is required")
        if not self.account_name:
            raise ValueError("Account name is required")
        if not self.account_number:
            self.account_number = self._generate_account_number()
        
        # Set default limits based on account type
        if not self.limits:
            self.limits = self._get_default_limits()
        
        # Ensure available balance matches balance initially
        if self.available_balance.amount == Decimal('0'):
            self.available_balance = Money(self.balance.amount, self.currency)
    
    def _generate_account_number(self) -> str:
        """Generate account number based on account type and branch"""
        prefix_map = {
            AccountType.SAVINGS: "SAV",
            AccountType.CURRENT: "CUR",
            AccountType.FIXED_DEPOSIT: "FD",
            AccountType.RECURRING_DEPOSIT: "RD",
            AccountType.LOAN: "LON",
            AccountType.CREDIT_CARD: "CC"
        }
        
        prefix = prefix_map.get(self.account_type, "ACC")
        branch = self.branch_code or "000"
        unique_id = self.account_id[:8].upper()
        
        return f"{prefix}{branch}{unique_id}"
    
    def _get_default_limits(self) -> AccountLimits:
        """Get default limits based on account type"""
        default_limits = {
            AccountType.SAVINGS: AccountLimits(
                daily_withdrawal_limit=Money(Decimal('1000'), self.currency),
                daily_transfer_limit=Money(Decimal('5000'), self.currency),
                monthly_transaction_limit=Money(Decimal('50000'), self.currency),
                minimum_balance=Money(Decimal('100'), self.currency)
            ),
            AccountType.CURRENT: AccountLimits(
                daily_withdrawal_limit=Money(Decimal('10000'), self.currency),
                daily_transfer_limit=Money(Decimal('50000'), self.currency),
                monthly_transaction_limit=Money(Decimal('500000'), self.currency),
                minimum_balance=Money(Decimal('0'), self.currency)
            )
        }
        
        return default_limits.get(
            self.account_type,
            AccountLimits(
                daily_withdrawal_limit=Money(Decimal('1000'), self.currency),
                daily_transfer_limit=Money(Decimal('5000'), self.currency),
                monthly_transaction_limit=Money(Decimal('50000'), self.currency),
                minimum_balance=Money(Decimal('0'), self.currency)
            )
        )
    
    def can_debit(self, amount: Money) -> bool:
        """Check if account can be debited"""
        if self.status != AccountStatus.ACTIVE:
            return False
        
        if amount.currency != self.currency:
            return False
        
        try:
            new_balance = self.balance.subtract(amount)
            return new_balance.is_greater_than_or_equal(self.limits.minimum_balance)
        except ValueError:
            return False
    
    def can_credit(self, amount: Money) -> bool:
        """Check if account can be credited"""
        if self.status == AccountStatus.CLOSED:
            return False
        
        if amount.currency != self.currency:
            return False
        
        if self.limits.maximum_balance:
            try:
                new_balance = self.balance.add(amount)
                return new_balance.is_greater_than_or_equal(self.limits.maximum_balance) == False
            except ValueError:
                return False
        
        return True
    
    def debit(self, amount: Money, description: str = "", reference: str = "", channel: str = "", created_by: str = "") -> Transaction:
        """Debit account and create transaction"""
        if not self.can_debit(amount):
            raise ValueError("Cannot debit account - insufficient funds or account restrictions")
        
        # Update balance
        self.balance = self.balance.subtract(amount)
        self.available_balance = Money(self.balance.amount, self.currency)
        self.last_transaction_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version += 1
        
        # Create transaction
        transaction = Transaction(
            account_id=self.account_id,
            transaction_type=TransactionType.DEBIT,
            amount=amount,
            balance_after=Money(self.balance.amount, self.currency),
            description=description or "Debit transaction",
            reference_number=reference,
            channel=channel,
            created_by=created_by
        )
        transaction.mark_completed()
        
        return transaction
    
    def credit(self, amount: Money, description: str = "", reference: str = "", channel: str = "", created_by: str = "") -> Transaction:
        """Credit account and create transaction"""
        if not self.can_credit(amount):
            raise ValueError("Cannot credit account - account restrictions or limits exceeded")
        
        # Update balance
        self.balance = self.balance.add(amount)
        self.available_balance = Money(self.balance.amount, self.currency)
        self.last_transaction_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version += 1
        
        # Create transaction
        transaction = Transaction(
            account_id=self.account_id,
            transaction_type=TransactionType.CREDIT,
            amount=amount,
            balance_after=Money(self.balance.amount, self.currency),
            description=description or "Credit transaction",
            reference_number=reference,
            channel=channel,
            created_by=created_by
        )
        transaction.mark_completed()
        
        return transaction
    
    def freeze(self, reason: str = "", frozen_by: str = ""):
        """Freeze account"""
        self.status = AccountStatus.FROZEN
        self.metadata["freeze_reason"] = reason
        self.metadata["frozen_by"] = frozen_by
        self.metadata["frozen_at"] = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def unfreeze(self, unfrozen_by: str = ""):
        """Unfreeze account"""
        self.status = AccountStatus.ACTIVE
        self.metadata["unfrozen_by"] = unfrozen_by
        self.metadata["unfrozen_at"] = datetime.utcnow().isoformat()
        if "freeze_reason" in self.metadata:
            del self.metadata["freeze_reason"]
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def close(self, reason: str = "", closed_by: str = ""):
        """Close account"""
        if self.balance.amount > Decimal('0'):
            raise ValueError("Cannot close account with positive balance")
        
        self.status = AccountStatus.CLOSED
        self.closed_date = datetime.utcnow()
        self.metadata["closure_reason"] = reason
        self.metadata["closed_by"] = closed_by
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def mark_dormant(self, reason: str = ""):
        """Mark account as dormant"""
        self.status = AccountStatus.DORMANT
        self.dormant_date = datetime.utcnow()
        self.metadata["dormant_reason"] = reason or "No transactions for extended period"
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def reactivate(self, reactivated_by: str = ""):
        """Reactivate dormant account"""
        self.status = AccountStatus.ACTIVE
        self.dormant_date = None
        self.metadata["reactivated_by"] = reactivated_by
        self.metadata["reactivated_at"] = datetime.utcnow().isoformat()
        if "dormant_reason" in self.metadata:
            del self.metadata["dormant_reason"]
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def update_limits(
        self,
        daily_withdrawal_limit: Optional[Money] = None,
        daily_transfer_limit: Optional[Money] = None,
        monthly_transaction_limit: Optional[Money] = None,
        minimum_balance: Optional[Money] = None,
        maximum_balance: Optional[Money] = None,
        updated_by: str = ""
    ):
        """Update account limits"""
        if daily_withdrawal_limit:
            self.limits.daily_withdrawal_limit = daily_withdrawal_limit
        if daily_transfer_limit:
            self.limits.daily_transfer_limit = daily_transfer_limit
        if monthly_transaction_limit:
            self.limits.monthly_transaction_limit = monthly_transaction_limit
        if minimum_balance:
            self.limits.minimum_balance = minimum_balance
        if maximum_balance:
            self.limits.maximum_balance = maximum_balance
        
        self.metadata["limits_updated_by"] = updated_by
        self.metadata["limits_updated_at"] = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def set_interest_rate(self, interest_rate: InterestRate, updated_by: str = ""):
        """Set interest rate for account"""
        self.interest_rate = interest_rate
        self.metadata["interest_rate_updated_by"] = updated_by
        self.metadata["interest_rate_updated_at"] = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def is_active(self) -> bool:
        """Check if account is active"""
        return self.status == AccountStatus.ACTIVE
    
    def is_frozen(self) -> bool:
        """Check if account is frozen"""
        return self.status == AccountStatus.FROZEN
    
    def is_closed(self) -> bool:
        """Check if account is closed"""
        return self.status == AccountStatus.CLOSED
    
    def days_since_last_transaction(self) -> Optional[int]:
        """Calculate days since last transaction"""
        if self.last_transaction_date:
            return (datetime.utcnow() - self.last_transaction_date).days
        return None
