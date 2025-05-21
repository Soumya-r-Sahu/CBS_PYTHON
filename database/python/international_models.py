"""
International Banking Identifiers Module

This module contains models for international banking identifiers like IBAN and SWIFT/BIC
used in international transactions.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


# Import base class from existing models
try:
    from database.python.common.database_operations import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

class IBAN(Base):
    """
    International Bank Account Number (IBAN) model
    Used for international banking transactions
    """
    __tablename__ = 'cbs_ibans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    iban = Column(String(34), unique=True, nullable=False, 
                 comment="ISO 13616 IBAN format")
    account_number = Column(String(20), ForeignKey('cbs_accounts.account_number'), nullable=False)
    country_code = Column(String(2), nullable=False, comment="ISO 3166-1 country code")
    check_digits = Column(String(2), nullable=False)
    bban = Column(String(30), nullable=False, 
                 comment="Basic Bank Account Number - country-specific part")
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="ibans")
    
    def __repr__(self):
        return f"<IBAN(id={self.id}, iban='{self.iban}', country='{self.country_code}')>"

class SWIFTBIC(Base):
    """
    SWIFT/BIC (Bank Identifier Code) model
    Used to identify specific banks in international transactions
    """
    __tablename__ = 'cbs_swift_bic'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    swift_bic = Column(String(11), unique=True, nullable=False, 
                      comment="ISO 9362 SWIFT/BIC format")
    bank_code = Column(String(4), nullable=False)
    country_code = Column(String(2), nullable=False, comment="ISO 3166-1 country code")
    location_code = Column(String(2), nullable=False)
    branch_code = Column(String(3), nullable=True)
    bank_name = Column(String(100), nullable=True)
    bank_address = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SWIFTBIC(id={self.id}, swift_bic='{self.swift_bic}', bank='{self.bank_name}')>"

class EmployeeDirectory(Base):
    """
    Employee Directory model
    Contains all bank employee information with standardized employee IDs
    """
    __tablename__ = 'cbs_employee_directory'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(12), unique=True, nullable=False, 
                        comment="Bank of Baroda Format: ZZBB-DD-EEEE (Zone+Branch+Designation+Sequence)")
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    department = Column(String(50), nullable=False)
    designation = Column(String(50), nullable=False)
    branch_code = Column(String(20), nullable=False)
    joining_date = Column(Date, nullable=False)
    reporting_to = Column(String(12), ForeignKey('cbs_employee_directory.employee_id'), nullable=True)
    contact_number = Column(String(20), nullable=False)
    emergency_contact = Column(String(20))
    address = Column(String(255))
    city = Column(String(50))
    state = Column(String(50))
    pin_code = Column(String(10))
    is_active = Column(Boolean, default=True)
    access_level = Column(Integer, default=1)
    last_promotion_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admin_user = relationship("AdminUser", back_populates="employee")
    reporting_employees = relationship("EmployeeDirectory", 
                                      backref="reporting_manager", 
                                      remote_side=[employee_id])
    
    def __repr__(self):
        return f"<Employee(id={self.id}, employee_id='{self.employee_id}', name='{self.first_name} {self.last_name}')>"
