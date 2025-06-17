"""
Transaction Service DTOs

Data Transfer Objects for transaction service API interfaces.
Provides request/response schemas with validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator

from transaction_service.domain.entities import (
    TransactionType, TransactionStatus, TransactionChannel
)


# Base DTOs
class MoneyDTO(BaseModel):
    """Money value object DTO."""
    amount: Decimal = Field(..., gt=0, description="Amount must be positive")
    currency: str = Field(default="INR", description="Currency code")
    
    class Config:
        schema_extra = {
            "example": {
                "amount": "1000.00",
                "currency": "INR"
            }
        }


class TransactionLegDTO(BaseModel):
    """Transaction leg DTO."""
    account_id: UUID
    amount: MoneyDTO
    transaction_type: TransactionType
    description: str = Field(..., min_length=1, max_length=500)
    reference: Optional[str] = Field(None, max_length=100)
    
    class Config:
        schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": {
                    "amount": "1000.00",
                    "currency": "INR"
                },
                "transaction_type": "DEBIT",
                "description": "Transfer to savings account",
                "reference": "REF123456"
            }
        }


class TransactionMetadataDTO(BaseModel):
    """Transaction metadata DTO."""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    location: Optional[str] = None
    additional_data: Dict[str, Any] = Field(default_factory=dict)


# Request DTOs
class CreateTransactionRequest(BaseModel):
    """Request to create a new transaction."""
    customer_id: Optional[UUID] = None
    channel: TransactionChannel = TransactionChannel.INTERNAL
    metadata: Optional[TransactionMetadataDTO] = None
    
    class Config:
        schema_extra = {
            "example": {
                "customer_id": "550e8400-e29b-41d4-a716-446655440000",
                "channel": "ONLINE",
                "metadata": {
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0...",
                    "device_id": "device123"
                }
            }
        }


class AddTransactionLegRequest(BaseModel):
    """Request to add a leg to transaction."""
    account_id: UUID
    amount: Decimal = Field(..., gt=0)
    transaction_type: TransactionType
    description: str = Field(..., min_length=1, max_length=500)
    currency: str = Field(default="INR")
    reference: Optional[str] = Field(None, max_length=100)
    
    class Config:
        schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": "1000.00",
                "transaction_type": "DEBIT",
                "description": "Transfer to savings account",
                "currency": "INR",
                "reference": "REF123456"
            }
        }


class ProcessTransferRequest(BaseModel):
    """Request to process a transfer."""
    from_account_id: UUID
    to_account_id: UUID
    amount: Decimal = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=500)
    customer_id: Optional[UUID] = None
    currency: str = Field(default="INR")
    channel: TransactionChannel = TransactionChannel.INTERNAL
    metadata: Optional[TransactionMetadataDTO] = None
    
    @validator('to_account_id')
    def validate_different_accounts(cls, v, values):
        if 'from_account_id' in values and v == values['from_account_id']:
            raise ValueError('Cannot transfer to same account')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "from_account_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_account_id": "550e8400-e29b-41d4-a716-446655440001",
                "amount": "1000.00",
                "description": "Monthly savings transfer",
                "customer_id": "550e8400-e29b-41d4-a716-446655440002",
                "currency": "INR",
                "channel": "ONLINE"
            }
        }


class AuthorizeTransactionRequest(BaseModel):
    """Request to authorize a transaction."""
    authorized_by: UUID
    
    class Config:
        schema_extra = {
            "example": {
                "authorized_by": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class CompleteTransactionRequest(BaseModel):
    """Request to complete a transaction."""
    settlement_date: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "settlement_date": "2024-01-15T10:30:00Z"
            }
        }


class ReverseTransactionRequest(BaseModel):
    """Request to reverse a transaction."""
    reversed_by: UUID
    reason: str = Field(..., min_length=1, max_length=500)
    
    class Config:
        schema_extra = {
            "example": {
                "reversed_by": "550e8400-e29b-41d4-a716-446655440000",
                "reason": "Customer dispute - unauthorized transaction"
            }
        }


# Response DTOs
class TransactionResponse(BaseModel):
    """Transaction response DTO."""
    transaction_id: UUID
    reference_number: str
    customer_id: Optional[UUID]
    legs: List[TransactionLegDTO]
    status: TransactionStatus
    channel: TransactionChannel
    created_at: datetime
    updated_at: datetime
    authorized_by: Optional[UUID]
    settlement_date: Optional[datetime]
    error_message: Optional[str]
    metadata: Optional[TransactionMetadataDTO]
    
    class Config:
        schema_extra = {
            "example": {
                "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
                "reference_number": "TXN20240115103000ABCD1234",
                "customer_id": "550e8400-e29b-41d4-a716-446655440001",
                "legs": [
                    {
                        "account_id": "550e8400-e29b-41d4-a716-446655440002",
                        "amount": {
                            "amount": "1000.00",
                            "currency": "INR"
                        },
                        "transaction_type": "DEBIT",
                        "description": "Transfer to savings",
                        "reference": "REF123"
                    }
                ],
                "status": "COMPLETED",
                "channel": "ONLINE",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:31:00Z",
                "authorized_by": "550e8400-e29b-41d4-a716-446655440003",
                "settlement_date": "2024-01-15T10:31:00Z"
            }
        }


class TransactionListResponse(BaseModel):
    """Response for transaction list queries."""
    transactions: List[TransactionResponse]
    total_count: int
    limit: int
    offset: int
    
    class Config:
        schema_extra = {
            "example": {
                "transactions": [],
                "total_count": 50,
                "limit": 10,
                "offset": 0
            }
        }


class TransactionSummaryResponse(BaseModel):
    """Transaction summary response."""
    total_transactions: int
    total_amount: MoneyDTO
    completed_transactions: int
    pending_transactions: int
    failed_transactions: int
    
    class Config:
        schema_extra = {
            "example": {
                "total_transactions": 100,
                "total_amount": {
                    "amount": "50000.00",
                    "currency": "INR"
                },
                "completed_transactions": 95,
                "pending_transactions": 3,
                "failed_transactions": 2
            }
        }


# Query DTOs
class TransactionQueryParams(BaseModel):
    """Query parameters for transaction search."""
    account_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    status: Optional[TransactionStatus] = None
    transaction_type: Optional[TransactionType] = None
    channel: Optional[TransactionChannel] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        if v is not None and 'min_amount' in values and values['min_amount'] is not None:
            if v < values['min_amount']:
                raise ValueError('max_amount must be greater than min_amount')
        return v
    
    @validator('to_date')
    def validate_date_range(cls, v, values):
        if v is not None and 'from_date' in values and values['from_date'] is not None:
            if v < values['from_date']:
                raise ValueError('to_date must be after from_date')
        return v


# Error DTOs
class TransactionErrorResponse(BaseModel):
    """Error response for transaction operations."""
    error_code: str
    error_message: str
    transaction_id: Optional[UUID] = None
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error_code": "INSUFFICIENT_BALANCE",
                "error_message": "Account has insufficient balance for transaction",
                "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
                "details": {
                    "required_amount": "1000.00",
                    "available_balance": "500.00"
                }
            }
        }


# Export public interface
__all__ = [
    # Base DTOs
    "MoneyDTO",
    "TransactionLegDTO", 
    "TransactionMetadataDTO",
    
    # Request DTOs
    "CreateTransactionRequest",
    "AddTransactionLegRequest",
    "ProcessTransferRequest", 
    "AuthorizeTransactionRequest",
    "CompleteTransactionRequest",
    "ReverseTransactionRequest",
    
    # Response DTOs
    "TransactionResponse",
    "TransactionListResponse",
    "TransactionSummaryResponse",
    
    # Query DTOs
    "TransactionQueryParams",
    
    # Error DTOs
    "TransactionErrorResponse"
]
