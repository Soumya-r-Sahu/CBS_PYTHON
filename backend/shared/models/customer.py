"""
Customer Model for Core Banking System V3.0
"""

from sqlalchemy import Column, String, Date, Enum
from sqlalchemy.orm import relationship
from datetime import date
import enum

from .base import BaseModel

class Gender(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class CustomerStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"

class Customer(BaseModel):
    """Customer model for banking customers"""
    __tablename__ = "customers"
    
    # Personal Information
    customer_id = Column(String(20), unique=True, nullable=False)  # CUS-YYYYMMDD-XXXXX
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    
    # Identification Documents
    pan_number = Column(String(10), unique=True)  # PAN Card (India)
    aadhar_number = Column(String(12), unique=True)  # Aadhar (India)
    
    # Contact Information
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    
    # Address Information
    address_line1 = Column(String(100), nullable=False)
    address_line2 = Column(String(100))
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(10), nullable=False)
    country = Column(String(50), default="India")
    
    # Status
    status = Column(Enum(CustomerStatus), default=CustomerStatus.ACTIVE)
    
    # Relationships
    accounts = relationship("Account", back_populates="customer", lazy="dynamic")
    
    def get_full_name(self):
        """Get customer's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        """Calculate customer's age"""
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
