"""
Account Service DTOs
Data Transfer Objects for API communication
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


# Request DTOs
@dataclass
class CreateAccountRequest:
    """Request DTO for creating an account"""
    customer_id: str
    account_type: str
    currency: str = "USD"
    initial_deposit: Optional[Decimal] = None
    daily_withdrawal_limit: Optional[Decimal] = None
    daily_transfer_limit: Optional[Decimal] = None
    monthly_transaction_limit: Optional[Decimal] = None
    minimum_balance: Optional[Decimal] = None
    maximum_balance: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    maintenance_fee: Optional[Decimal] = None
    overdraft_limit: Optional[Decimal] = None
    overdraft_fee: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


@dataclass
class UpdateAccountRequest:
    """Request DTO for updating an account"""
    daily_withdrawal_limit: Optional[Decimal] = None
    daily_transfer_limit: Optional[Decimal] = None
    monthly_transaction_limit: Optional[Decimal] = None
    minimum_balance: Optional[Decimal] = None
    maximum_balance: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    maintenance_fee: Optional[Decimal] = None
    overdraft_limit: Optional[Decimal] = None
    overdraft_fee: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


@dataclass
class DepositRequest:
    """Request DTO for depositing funds"""
    amount: Decimal
    currency: str = "USD"
    description: Optional[str] = None
    reference_number: Optional[str] = None
    channel: Optional[str] = None
    location: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WithdrawRequest:
    """Request DTO for withdrawing funds"""
    amount: Decimal
    currency: str = "USD"
    description: Optional[str] = None
    reference_number: Optional[str] = None
    channel: Optional[str] = None
    location: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TransferRequest:
    """Request DTO for transferring funds"""
    to_account_id: str
    amount: Decimal
    currency: str = "USD"
    description: Optional[str] = None
    reference_number: Optional[str] = None
    channel: Optional[str] = None
    location: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AccountSearchRequest:
    """Request DTO for searching accounts"""
    customer_id: Optional[str] = None
    account_type: Optional[str] = None
    status: Optional[str] = None
    min_balance: Optional[Decimal] = None
    max_balance: Optional[Decimal] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


@dataclass
class TransactionSearchRequest:
    """Request DTO for searching transactions"""
    account_id: str
    transaction_type: Optional[str] = None
    status: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


# Response DTOs
@dataclass
class MoneyDTO:
    """DTO for money amounts"""
    amount: Decimal
    currency: str


@dataclass
class AccountLimitsDTO:
    """DTO for account limits"""
    daily_withdrawal_limit: MoneyDTO
    daily_transfer_limit: MoneyDTO
    monthly_transaction_limit: MoneyDTO
    minimum_balance: MoneyDTO
    maximum_balance: Optional[MoneyDTO] = None


@dataclass
class AccountDTO:
    """DTO for account information"""
    id: str
    account_number: str
    customer_id: str
    account_type: str
    status: str
    balance: MoneyDTO
    limits: AccountLimitsDTO
    interest_rate: Optional[Decimal] = None
    maintenance_fee: Optional[MoneyDTO] = None
    overdraft_limit: Optional[MoneyDTO] = None
    overdraft_fee: Optional[MoneyDTO] = None
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int


@dataclass
class TransactionDTO:
    """DTO for transaction information"""
    id: str
    transaction_id: str
    account_id: str
    transaction_type: str
    amount: MoneyDTO
    status: str
    description: Optional[str] = None
    reference_number: Optional[str] = None
    related_account_id: Optional[str] = None
    balance_before: MoneyDTO
    balance_after: MoneyDTO
    processing_fee: Optional[MoneyDTO] = None
    exchange_rate: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None
    channel: Optional[str] = None
    location: Optional[str] = None
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    authorized_by: Optional[str] = None


@dataclass
class AccountSummaryDTO:
    """DTO for account summary"""
    customer_id: str
    total_accounts: int
    total_balance: Decimal
    by_type: Dict[str, Dict[str, Any]]
    by_status: Dict[str, Dict[str, Any]]


@dataclass
class TransactionSummaryDTO:
    """DTO for transaction summary"""
    account_id: str
    total_transactions: int
    total_credits: Decimal
    total_debits: Decimal
    total_fees: Decimal
    net_amount: Decimal
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


@dataclass
class PaginatedResponse:
    """DTO for paginated responses"""
    items: List[Any]
    total_count: int
    limit: int
    offset: int
    has_more: bool


@dataclass
class CreateAccountResponse:
    """Response DTO for account creation"""
    account: AccountDTO
    message: str
    success: bool


@dataclass
class TransactionResponse:
    """Response DTO for transaction operations"""
    transaction: TransactionDTO
    account_balance: MoneyDTO
    message: str
    success: bool


@dataclass
class ErrorResponse:
    """DTO for error responses"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


# Mapper functions
def money_to_dto(money) -> MoneyDTO:
    """Convert Money entity to DTO"""
    if not money:
        return None
    return MoneyDTO(amount=money.amount, currency=money.currency)


def account_limits_to_dto(limits) -> AccountLimitsDTO:
    """Convert AccountLimits entity to DTO"""
    return AccountLimitsDTO(
        daily_withdrawal_limit=money_to_dto(limits.daily_withdrawal_limit),
        daily_transfer_limit=money_to_dto(limits.daily_transfer_limit),
        monthly_transaction_limit=money_to_dto(limits.monthly_transaction_limit),
        minimum_balance=money_to_dto(limits.minimum_balance),
        maximum_balance=money_to_dto(limits.maximum_balance)
    )


def account_to_dto(account) -> AccountDTO:
    """Convert Account entity to DTO"""
    return AccountDTO(
        id=str(account.id),
        account_number=account.account_number,
        customer_id=str(account.customer_id),
        account_type=account.account_type.value,
        status=account.status.value,
        balance=money_to_dto(account.balance),
        limits=account_limits_to_dto(account.limits),
        interest_rate=account.interest_rate,
        maintenance_fee=money_to_dto(account.maintenance_fee),
        overdraft_limit=money_to_dto(account.overdraft_limit),
        overdraft_fee=money_to_dto(account.overdraft_fee),
        metadata=account.metadata,
        notes=account.notes,
        created_at=account.created_at,
        updated_at=account.updated_at,
        created_by=account.created_by,
        updated_by=account.updated_by,
        version=account.version
    )


def transaction_to_dto(transaction) -> TransactionDTO:
    """Convert Transaction entity to DTO"""
    return TransactionDTO(
        id=str(transaction.id),
        transaction_id=transaction.transaction_id,
        account_id=str(transaction.account_id),
        transaction_type=transaction.transaction_type.value,
        amount=money_to_dto(transaction.amount),
        status=transaction.status.value,
        description=transaction.description,
        reference_number=transaction.reference_number,
        related_account_id=str(transaction.related_account_id) if transaction.related_account_id else None,
        balance_before=money_to_dto(transaction.balance_before),
        balance_after=money_to_dto(transaction.balance_after),
        processing_fee=money_to_dto(transaction.processing_fee),
        exchange_rate=transaction.exchange_rate,
        metadata=transaction.metadata,
        channel=transaction.channel,
        location=transaction.location,
        initiated_at=transaction.initiated_at,
        completed_at=transaction.completed_at,
        created_by=transaction.created_by,
        authorized_by=transaction.authorized_by
    )


__all__ = [
    # Request DTOs
    "CreateAccountRequest",
    "UpdateAccountRequest", 
    "DepositRequest",
    "WithdrawRequest",
    "TransferRequest",
    "AccountSearchRequest",
    "TransactionSearchRequest",
    
    # Response DTOs
    "MoneyDTO",
    "AccountLimitsDTO",
    "AccountDTO",
    "TransactionDTO",
    "AccountSummaryDTO",
    "TransactionSummaryDTO",
    "PaginatedResponse",
    "CreateAccountResponse",
    "TransactionResponse",
    "ErrorResponse",
    
    # Mappers
    "money_to_dto",
    "account_limits_to_dto",
    "account_to_dto",
    "transaction_to_dto"
]
