"""
Core Banking System - Data models

This module contains SQLAlchemy models for the Core Banking System.
Uses Bank of Baroda and RBI standards for all banking identifiers.
"""

import os
import sys
import uuid
import random
import string
from pathlib import Path
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.event import listen
from sqlalchemy.sql.schema import DDL

# Use centralized import system
from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
fix_path()  # Ensures the project root is in sys.path


# Try to import environment module
try:
    from core_banking.utils.config import get_environment_name, is_production, is_development, is_test
except ImportError:
    # Fallback environment detection
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def get_environment_name(): return env_str.capitalize()

# Set table prefix based on environment for isolation
if is_production():
    TABLE_PREFIX = ""  # No prefix in production
else:
    TABLE_PREFIX = f"{get_environment_name().lower()}_"  # e.g. "development_"

# Import SQLAlchemy and set up Base
try:
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    print("SQLAlchemy imported successfully")
    Base = declarative_base()
    print("Using Base from core_banking.database")
except ImportError:
    # If SQLAlchemy is not available, create a simple mock
    print("SQLAlchemy not found. Using mock Base class")
    class Base:
        __tablename__ = ""
        metadata = None

# Customer model
class Customer(Base):
    """Customer model in the Core Banking System"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(20), unique=True, nullable=False)  # Customer ID format: CUS-YYYYMMDD-XXXXX
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(DateTime)
    gender = Column(String(10))
    pan_number = Column(String(10))  # PAN Card number (India)
    aadhar_number = Column(String(12))  # Aadhar number (India)
    address_line1 = Column(String(100))
    address_line2 = Column(String(100))
    city = Column(String(50))
    state = Column(String(50))
    postal_code = Column(String(10))
    country = Column(String(50), default="India")
    email = Column(String(100))
    phone = Column(String(20))
    status = Column(String(20), default="ACTIVE")  # ACTIVE, INACTIVE, SUSPENDED, CLOSED
    registration_date = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    accounts = relationship("Account", back_populates="customer")
    
# Account model
class Account(Base):
    """Account model for different types of bank accounts"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_number = Column(String(20), unique=True, nullable=False)  # Account number format: AC-YYYYMMDD-XXXXX
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    account_type = Column(String(20), nullable=False)  # SAVINGS, CURRENT, FIXED_DEPOSIT, LOAN
    balance = Column(Float, default=0.0)
    currency = Column(String(3), default="INR")
    interest_rate = Column(Float)
    open_date = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, INACTIVE, SUSPENDED, CLOSED
    last_transaction_date = Column(DateTime)
    branch_code = Column(String(10))
    
    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
    
# Transaction model
class Transaction(Base):
    """Transaction model for all banking transactions"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(30), unique=True, nullable=False)  # Transaction ID format: TXN-YYYYMMDD-XXXXX
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # DEPOSIT, WITHDRAWAL, TRANSFER, PAYMENT
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    transaction_date = Column(DateTime, default=datetime.now)
    description = Column(String(200))
    reference_number = Column(String(50))
    status = Column(String(20), default="COMPLETED")  # PENDING, COMPLETED, FAILED, REVERSED
    created_by = Column(String(50))  # User or system that created the transaction
    
    # Relationships
    account = relationship("Account", back_populates="transactions")

# Beneficiary model
class Beneficiary(Base):
    """Beneficiary model for fund transfers"""
    __tablename__ = "beneficiaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    beneficiary_name = Column(String(100), nullable=False)
    account_number = Column(String(20), nullable=False)
    ifsc_code = Column(String(20), nullable=False)
    bank_name = Column(String(100))
    branch_name = Column(String(100))
    relation_type = Column(String(50))  # Changed from 'relationship' to avoid conflict
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # SQLAlchemy relationship reference to Customer
    customer = relationship("Customer")

# Standing Instruction model
class StandingInstruction(Base):
    """Standing instruction model for recurring transfers"""
    __tablename__ = "standing_instructions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    beneficiary_id = Column(Integer, ForeignKey("beneficiaries.id"), nullable=False)
    amount = Column(Float, nullable=False)
    frequency = Column(String(20), nullable=False)  # DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY
    next_execution_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    description = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    account = relationship("Account")
    beneficiary = relationship("Beneficiary")

# Branch model
class Branch(Base):
    """Bank branch model"""
    __tablename__ = "branches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_code = Column(String(10), unique=True, nullable=False)
    ifsc_code = Column(String(11), unique=True, nullable=False)
    branch_name = Column(String(100), nullable=False)
    address_line1 = Column(String(100))
    address_line2 = Column(String(100))
    city = Column(String(50))
    state = Column(String(50))
    postal_code = Column(String(20))
    phone = Column(String(20))
    email = Column(String(100))
    manager_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    
# Card model for bank cards (debit, credit, etc)
class Card(Base):
    """Card model for banking cards"""
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    card_number = Column(String(20), nullable=False)
    card_type = Column(String(20), nullable=False)  # DEBIT, CREDIT, etc.
    cardholder_name = Column(String(100), nullable=False)
    expiry_date = Column(String(7), nullable=False)  # MM/YYYY format
    cvv = Column(String(3), nullable=False)
    pin_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    daily_limit = Column(Float, default=10000.0)
    created_at = Column(DateTime, default=datetime.now)
    
    account = relationship("Account")

# Database function to initialize all tables
def initialize_db(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)