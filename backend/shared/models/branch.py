"""
Branch Model for Core Banking System V3.0
"""

from sqlalchemy import Column, String, Boolean, Text
from .base import BaseModel

class Branch(BaseModel):
    """Branch model for bank branches"""
    __tablename__ = "branches"
    
    # Branch Information
    branch_code = Column(String(10), unique=True, nullable=False)
    ifsc_code = Column(String(11), unique=True, nullable=False)
    branch_name = Column(String(100), nullable=False)
    
    # Address Information
    address_line1 = Column(String(100), nullable=False)
    address_line2 = Column(String(100))
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(10), nullable=False)
    country = Column(String(50), default="India")
    
    # Contact Information
    phone = Column(String(20))
    email = Column(String(100))
    fax = Column(String(20))
    
    # Branch Management
    manager_name = Column(String(100))
    manager_phone = Column(String(20))
    manager_email = Column(String(100))
    
    # Operational Information
    is_head_office = Column(Boolean, default=False)
    is_regional_office = Column(Boolean, default=False)
    region = Column(String(50))
    zone = Column(String(50))
    
    # Services
    services_offered = Column(Text)  # JSON string of services
    working_hours = Column(Text)  # JSON string of working hours
    
    # Status
    is_operational = Column(Boolean, default=True)
    
    def get_full_address(self):
        """Get complete address"""
        address_parts = [self.address_line1]
        if self.address_line2:
            address_parts.append(self.address_line2)
        address_parts.extend([self.city, self.state, self.postal_code, self.country])
        return ", ".join(address_parts)
    
    def get_branch_info(self):
        """Get branch information"""
        return {
            'branch_code': self.branch_code,
            'ifsc_code': self.ifsc_code,
            'branch_name': self.branch_name,
            'address': self.get_full_address(),
            'phone': self.phone,
            'email': self.email,
            'manager_name': self.manager_name,
            'is_operational': self.is_operational
        }
