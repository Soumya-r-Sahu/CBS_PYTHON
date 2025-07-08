# database/python/models/__init__.py
"""
Core Banking System ORM Models

This module contains all SQLAlchemy models used for database operations.
"""

from database.python.models.base_models import Base
from database.python.models.banking_models import (
    Customer, Account, Transaction, CardDetails, 
    Loan, CustomerSegment, RiskCategory, Gender,
    CustomerStatus, KYCStatus
)
from database.python.models.international_models import (
    IBAN, SWIFT, ISOCountry, BankIdentifier, TransactionCorrespondent
)

__all__ = [
    # Base
    'Base',
    
    # Banking models
    'Customer', 'Account', 'Transaction', 'CardDetails', 
    'Loan', 'CustomerSegment', 'RiskCategory', 'Gender',
    'CustomerStatus', 'KYCStatus',
    
    # International models
    'IBAN', 'SWIFT', 'ISOCountry', 'BankIdentifier', 'TransactionCorrespondent'
]
