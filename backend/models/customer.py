"""
Customer model for banking customers.
"""

from datetime import date
from typing import Optional

from sqlalchemy import Column, String, Date, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import BaseModel

class Customer(BaseModel):
    """
    Customer model representing banking customers.
    """
    __tablename__ = "customers"
    
    # Basic information
    customer_id = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=True)
    
    # Identification documents (India specific)
    pan_number = Column(String(10), unique=True, nullable=True, index=True)
    aadhar_number = Column(String(12), unique=True, nullable=True, index=True)
    
    # Contact information
    email = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    
    # Address information
    address_line1 = Column(String(100), nullable=False)
    address_line2 = Column(String(100), nullable=True)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(10), nullable=False)
    country = Column(String(50), default="India", nullable=False)
    
    # System information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", backref="customer_profile")
    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    
    @property
    def full_name(self) -> str:
        """Get customer's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self) -> str:
        """Get customer's full address."""
        address_parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ", ".join(part for part in address_parts if part)
    
    def __repr__(self) -> str:
        return f"<Customer(customer_id={self.customer_id}, name={self.full_name})>"
