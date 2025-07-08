# database/python/models/international_models.py
"""
International Banking Identifiers Module

This module contains models for international banking identifiers like IBAN and SWIFT/BIC
used in international transactions.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Date, Text
from sqlalchemy.orm import relationship
from datetime import datetime

# Import base class
from database.python.models.base_models import Base

# IBAN (International Bank Account Number) Model
class IBAN(Base):
    __tablename__ = 'iban_registry'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    iban = Column(String(50), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    country_code = Column(String(2), nullable=False)
    check_digits = Column(String(2), nullable=False)
    bank_code = Column(String(20), nullable=False)
    branch_code = Column(String(20))
    account_number = Column(String(30), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_validated = Column(DateTime)
    
    def __repr__(self):
        return f"<IBAN {self.iban[:6]}...{self.iban[-4:]}>"

# SWIFT/BIC Code Model
class SWIFT(Base):
    __tablename__ = 'swift_registry'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    swift_code = Column(String(11), unique=True, nullable=False, index=True)
    bank_name = Column(String(100), nullable=False)
    country_code = Column(String(2), nullable=False)
    location_code = Column(String(2), nullable=False)
    branch_code = Column(String(3))
    address = Column(Text)
    city = Column(String(50))
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with correspondent banks
    correspondents = relationship("TransactionCorrespondent", back_populates="swift")
    
    def __repr__(self):
        return f"<SWIFT {self.swift_code}: {self.bank_name}>"

# ISO Country Codes for International Banking
class ISOCountry(Base):
    __tablename__ = 'iso_countries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    country_name = Column(String(100), nullable=False)
    alpha2 = Column(String(2), unique=True, nullable=False)
    alpha3 = Column(String(3), unique=True, nullable=False)
    numeric_code = Column(String(3), unique=True, nullable=False)
    iban_format = Column(String(255))
    sepa_member = Column(Boolean, default=False)
    swift_format = Column(String(255))
    
    def __repr__(self):
        return f"<ISOCountry {self.alpha2}: {self.country_name}>"

# Bank Identifier Model for various formats
class BankIdentifier(Base):
    __tablename__ = 'bank_identifiers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier_type = Column(String(20), nullable=False)  # SWIFT, IFSC, BSB, etc.
    identifier_value = Column(String(50), nullable=False)
    bank_name = Column(String(100), nullable=False)
    country_code = Column(String(2), nullable=False)
    address = Column(Text)
    city = Column(String(50))
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        # Composite unique constraint on type and value
        {'UniqueConstraint': ('identifier_type', 'identifier_value')}
    )
    
    def __repr__(self):
        return f"<BankIdentifier {self.identifier_type}: {self.identifier_value}>"

# Correspondent Bank Model for international transfers
class TransactionCorrespondent(Base):
    __tablename__ = 'transaction_correspondents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    swift_id = Column(Integer, ForeignKey('swift_registry.id'), nullable=False)
    correspondent_swift = Column(String(11), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # Nostro, Vostro, etc.
    account_number = Column(String(50))
    currency = Column(String(3), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationship with SWIFT registry
    swift = relationship("SWIFT", back_populates="correspondents")
    
    def __repr__(self):
        return f"<Correspondent {self.relationship_type}: {self.correspondent_swift} ({self.currency})>"
