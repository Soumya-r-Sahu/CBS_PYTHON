# database/python/models/banking_models.py
"""
Core Banking Models

This module contains the SQLAlchemy models for core banking entities like
Customer, Account, Transaction, Cards, Loans, etc.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean, Date, Enum, Text, DECIMAL
from sqlalchemy.orm import relationship
import datetime
import enum

# Import base models
from database.python.models.base_models import (
    Base, CustomerStatus, KYCStatus, CustomerSegment, 
    RiskCategory, Gender, AccountType, TransactionType, 
    TransactionStatus
)

# Customer Model
class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50))
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    nationality = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20), nullable=False)
    address_line1 = Column(String(100), nullable=False)
    address_line2 = Column(String(100))
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False)
    identification_type = Column(String(50), nullable=False)
    identification_number = Column(String(50), nullable=False, unique=True)
    customer_status = Column(Enum(CustomerStatus), default=CustomerStatus.ACTIVE)
    kyc_status = Column(Enum(KYCStatus), default=KYCStatus.PENDING)
    segment = Column(Enum(CustomerSegment), default=CustomerSegment.RETAIL)
    risk_category = Column(Enum(RiskCategory), default=RiskCategory.LOW)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    accounts = relationship("Account", back_populates="customer")
    cards = relationship("CardDetails", back_populates="customer")
    loans = relationship("Loan", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer {self.customer_id}: {self.first_name} {self.last_name}>"

# Account Model
class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_number = Column(String(20), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    balance = Column(DECIMAL(18, 2), nullable=False, default=0)
    available_balance = Column(DECIMAL(18, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="ACTIVE")
    interest_rate = Column(Float, default=0)
    date_opened = Column(DateTime, default=datetime.datetime.utcnow)
    last_transaction_date = Column(DateTime)
    
    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
    
    def __repr__(self):
        return f"<Account {self.account_number}: {self.account_type.value}>"

# Transaction Model
class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(30), unique=True, nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(DECIMAL(18, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    transaction_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    description = Column(String(255))
    reference_id = Column(String(50))
    beneficiary_account = Column(String(50))
    beneficiary_name = Column(String(100))
    beneficiary_bank = Column(String(100))
    source_account = Column(String(50))
    source_name = Column(String(100))
    source_bank = Column(String(100))
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction {self.transaction_id}: {self.amount} {self.currency}>"

# Card Details Model
class CardDetails(Base):
    __tablename__ = 'card_details'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_number = Column(String(16), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    card_type = Column(String(20), nullable=False)
    expiry_date = Column(Date, nullable=False)
    card_status = Column(String(20), default="ACTIVE")
    issue_date = Column(Date, nullable=False)
    daily_limit = Column(DECIMAL(18, 2))
    
    # Relationships
    customer = relationship("Customer", back_populates="cards")
    
    def __repr__(self):
        return f"<Card {self.card_number[-4:]}: {self.card_type}>"

# Loan Model
class Loan(Base):
    __tablename__ = 'loans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_account_number = Column(String(20), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    loan_type = Column(String(50), nullable=False)
    loan_amount = Column(DECIMAL(18, 2), nullable=False)
    interest_rate = Column(Float, nullable=False)
    term_months = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    outstanding_amount = Column(DECIMAL(18, 2), nullable=False)
    status = Column(String(20), default="ACTIVE")
    
    # Relationships
    customer = relationship("Customer", back_populates="loans")
    
    def __repr__(self):
        return f"<Loan {self.loan_account_number}: {self.loan_type}>"
