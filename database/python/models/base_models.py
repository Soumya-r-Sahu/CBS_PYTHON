# database/python/models/base_models.py
"""
Base models for SQLAlchemy ORM.
"""

from sqlalchemy.ext.declarative import declarative_base
import enum

# Create Base class for SQLAlchemy models
Base = declarative_base()

# Common enum classes used across models

class CustomerStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"

class KYCStatus(enum.Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL" 
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class CustomerSegment(enum.Enum):
    RETAIL = "RETAIL"
    CORPORATE = "CORPORATE"
    PRIORITY = "PRIORITY"
    NRI = "NRI"
    SENIOR = "SENIOR"
    MINOR = "MINOR"
    STUDENT = "STUDENT"

class RiskCategory(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Gender(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"

class AccountType(enum.Enum):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    SALARY = "SALARY"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    RECURRING_DEPOSIT = "RECURRING_DEPOSIT"
    LOAN = "LOAN"
    CREDIT_CARD = "CREDIT_CARD"
    NRO = "NRO"
    NRE = "NRE"

class TransactionType(enum.Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"
    REVERSAL = "REVERSAL"
    FEE = "FEE"
    INTEREST = "INTEREST"

class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    HOLD = "HOLD"
