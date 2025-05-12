"""
Core Banking System - Data models

This module contains SQLAlchemy models for the Core Banking System.
Uses SBI Bank ID formats and standards for all identifiers.
"""

import uuid
import random
import string
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.event import listen
from sqlalchemy.sql.schema import DDL

# Import SBI ID generation utilities
from app.lib.id_generator import (
    generate_customer_id, generate_account_number, 
    generate_transaction_id, generate_card_number, generate_upi_id,
    AccountType as SBIAccountType
)

Base = declarative_base()

class Customer(Base):
    """Customer model representing bank account holders using SBI formats"""
    
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(String(12), unique=True, nullable=False, 
                        comment="SBI format customer ID: SBI+type(1 digit)+8 digits")
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(255))
    city = Column(String(50))
    state = Column(String(50))
    pin_code = Column(String(10))
    pan_number = Column(String(10), comment="PAN Card number")
    aadhar_number = Column(String(12), comment="Aadhaar number")
    date_of_birth = Column(DateTime)
    customer_type = Column(String(20), default="INDIVIDUAL", 
                          comment="Customer type: INDIVIDUAL, CORPORATE, GOVERNMENT, NRI, SENIOR_CITIZEN")
    is_active = Column(Boolean, default=True)
    kyc_status = Column(String(20), default="PENDING", 
                       comment="KYC status: PENDING, PARTIAL, COMPLETED, REJECTED, EXPIRED")
    customer_segment = Column(String(20), default="RETAIL", 
                            comment="Customer segment: RETAIL, CORPORATE, PRIORITY, NRI, SENIOR, MINOR, STUDENT")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    accounts = relationship("Account", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, customer_id='{self.customer_id}', name='{self.first_name} {self.last_name}')>"
    
    @classmethod
    def generate_id(cls):
        """Generate SBI format customer ID"""
        return generate_customer_id()


class Account(Base):
    """Account model representing bank accounts using SBI formats"""
    
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True)
    account_number = Column(String(14), unique=True, nullable=False,
                          comment="SBI format account number: 14 digits (State+Branch+Serial)")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    ifsc_code = Column(String(11), nullable=False, default="SBIN0000001",
                     comment="SBI IFSC code: SBIN + 0 + branch code")
    branch_code = Column(String(10), nullable=False, default="MAH00001",
                       comment="SBI branch code")
    account_type = Column(String(20), nullable=False, default="SAVINGS")  # SAVINGS, CURRENT, etc.
    balance = Column(Float, default=0.0)
    currency = Column(String(3), default="INR")
    interest_rate = Column(Float, default=3.5)  # SBI savings rate (typical)
    nominee_name = Column(String(100))
    nominee_relation = Column(String(50))
    account_status = Column(String(20), default="ACTIVE",
                          comment="Account status: ACTIVE, DORMANT, FROZEN, CLOSED, SUSPENDED")
    minimum_balance = Column(Float, default=1000.0)  # SBI minimum balance requirement
    is_active = Column(Boolean, default=True)
    opening_date = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
    
    def __repr__(self):
        return f"<Account(id={self.id}, account_number='{self.account_number}', type='{self.account_type}', balance={self.balance})>"
    
    @classmethod
    def generate_account_number(cls, state_code=None, branch_code=None):
        """Generate SBI format account number"""
        return generate_account_number(
            state_code=state_code or "14",  # Default to Maharashtra
            branch_code=branch_code or "00001"
        )


class Transaction(Base):
    """Transaction model representing account transactions using SBI formats"""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(18), unique=True, nullable=False,
                          comment="SBI format: 1 char channel code + 17 chars unique ID")
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False,
                            comment="WITHDRAWAL, DEPOSIT, TRANSFER, PAYMENT, etc.")
    channel = Column(String(20), nullable=False, default="MOBILE",
                   comment="ATM, BRANCH, INTERNET, MOBILE, UPI, IMPS, NEFT, RTGS")
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    description = Column(String(255))
    transaction_date = Column(DateTime, default=datetime.now)
    value_date = Column(DateTime, default=datetime.now, 
                       comment="Date when transaction is effective/available")
    reference_number = Column(String(19), 
                            comment="SBI reference format: SBI+P+date+random 8 digits")
    remarks = Column(String(255))
    status = Column(String(20), default="SUCCESS",
                  comment="SUCCESS, PENDING, FAILED, REVERSED, etc.")
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, transaction_id='{self.transaction_id}', type='{self.transaction_type}', amount={self.amount})>"
    
    @classmethod
    def generate_transaction_id(cls, channel="MOBILE"):
        """Generate SBI format transaction ID"""
        return generate_transaction_id(channel=channel)


class Card(Base):
    """Card model representing debit/credit cards using SBI formats"""
    
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True)
    card_id = Column(String(20), unique=True, nullable=False)
    card_number = Column(String(16), unique=True, nullable=False, 
                       comment="SBI 16-digit card number format")
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    card_type = Column(String(20), nullable=False, default="DEBIT",
                     comment="DEBIT, CREDIT, PREPAID, INTERNATIONAL, VIRTUAL")
    card_network = Column(String(20), nullable=False, default="RUPAY",
                        comment="VISA, MASTERCARD, RUPAY, MAESTRO")
    holder_name = Column(String(100), nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    cvv = Column(String(3), nullable=False)
    is_active = Column(Boolean, default=False)  # Card needs activation
    pin = Column(String(255), nullable=False)  # Stored encrypted
    daily_atm_limit = Column(Float, default=10000.0)
    daily_pos_limit = Column(Float, default=25000.0)
    daily_online_limit = Column(Float, default=50000.0)
    domestic_usage = Column(Boolean, default=True)
    international_usage = Column(Boolean, default=False)
    contactless_enabled = Column(Boolean, default=True)
    status = Column(String(20), default="INACTIVE",
                  comment="ACTIVE, INACTIVE, BLOCKED, EXPIRED, HOTLISTED, PENDING_ACTIVATION")
    activation_date = Column(DateTime)
    issued_date = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    account = relationship("Account")
    
    def __repr__(self):
        return f"<Card(id={self.id}, card_number='{self.card_number[:4]}...{self.card_number[-4:]}', type='{self.card_type}')>"
    
    @classmethod
    def generate_card_number(cls, card_type="DEBIT", network="RUPAY"):
        """Generate SBI format card number"""
        return generate_card_number(type=card_type, network=network)
    
    def __repr__(self):
        return f"<Card(id={self.id}, card_type='{self.card_type}', is_active={self.is_active})>"


class UPI(Base):
    """UPI model representing UPI accounts using SBI formats"""
    
    __tablename__ = "upi_accounts"
    
    id = Column(Integer, primary_key=True)
    upi_id = Column(String(50), unique=True, nullable=False, 
                  comment="SBI format UPI ID: username@sbi")
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    device_id = Column(String(100))  # Device fingerprint
    mobile_number = Column(String(15), nullable=False)
    is_active = Column(Boolean, default=True)
    daily_limit = Column(Float, default=100000.0)  # Default UPI limit
    per_transaction_limit = Column(Float, default=20000.0)
    status = Column(String(20), default="ACTIVE",
                  comment="ACTIVE, INACTIVE, BLOCKED, SUSPENDED")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    account = relationship("Account")
    customer = relationship("Customer")
    
    def __repr__(self):
        return f"<UPI(id={self.id}, upi_id='{self.upi_id}')>"
    
    @classmethod
    def generate_upi_id(cls, username=None, mobile_number=None):
        """Generate SBI format UPI ID"""
        return generate_upi_id(username=username, mobile_number=mobile_number)
