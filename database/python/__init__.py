# database/python/__init__.py
"""
Core Banking System - Database Module

This module provides database connectivity, ORM models, and utilities 
for interacting with the Core Banking System database.
"""

# Import connection components
from database.python.connection.connection_manager import (
    engine, Base, SessionLocal, get_db
)
from database.python.connection.db_connection import DatabaseConnection

# Import models
from database.python.models import (
    # Banking models
    Customer, Account, Transaction, CardDetails, Loan,
    # International models
    IBAN, SWIFT, ISOCountry, BankIdentifier, TransactionCorrespondent,
    # Enum types
    CustomerStatus, KYCStatus, CustomerSegment, RiskCategory, Gender
)

# Import utilities
from database.python.utilities import (
    compare_databases, generate_schema_report,
    create_backup, restore_backup, migrate_schema
)

__all__ = [
    # Connection components
    'engine', 'Base', 'SessionLocal', 'get_db', 'DatabaseConnection',
    
    # Models
    'Customer', 'Account', 'Transaction', 'CardDetails', 'Loan',
    'IBAN', 'SWIFT', 'ISOCountry', 'BankIdentifier', 'TransactionCorrespondent',
    'CustomerStatus', 'KYCStatus', 'CustomerSegment', 'RiskCategory', 'Gender',
    
    # Utilities
    'compare_databases', 'generate_schema_report',
    'create_backup', 'restore_backup', 'migrate_schema'
]