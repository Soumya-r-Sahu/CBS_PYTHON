"""
Customer Entity

This module defines the Customer entity, which is a core domain entity
in the Customer Management module.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict
from enum import Enum
import re


class CustomerStatus(Enum):
    """Enumeration of possible customer statuses"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    PENDING_VERIFICATION = "pending_verification"
    CLOSED = "closed"


class CustomerType(Enum):
    """Enumeration of customer types"""
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    JOINT = "joint"
    MINOR = "minor"


class RiskCategory(Enum):
    """Enumeration of risk categories for KYC/AML"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Address:
    """Value object representing a physical address"""
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    address_type: str  # residential, mailing, business, etc.
    is_primary: bool = False
    
    def __post_init__(self):
        """Validate address data"""
        if not self.street or not isinstance(self.street, str):
            raise ValueError("Street is required and must be a string")
        if not self.city or not isinstance(self.city, str):
            raise ValueError("City is required and must be a string")
        if not self.state or not isinstance(self.state, str):
            raise ValueError("State is required and must be a string")
        if not self.postal_code or not isinstance(self.postal_code, str):
            raise ValueError("Postal code is required and must be a string")
        if not self.country or not isinstance(self.country, str):
            raise ValueError("Country is required and must be a string")
        if not self.address_type or not isinstance(self.address_type, str):
            raise ValueError("Address type is required and must be a string")


@dataclass
class ContactInformation:
    """Value object representing contact information"""
    email: Optional[str] = None
    primary_phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    
    def __post_init__(self):
        """Validate contact information"""
        if self.email and not self._is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
        
        if self.primary_phone and not self._is_valid_phone(self.primary_phone):
            raise ValueError(f"Invalid primary phone format: {self.primary_phone}")
            
        if self.secondary_phone and not self._is_valid_phone(self.secondary_phone):
            raise ValueError(f"Invalid secondary phone format: {self.secondary_phone}")
    
    @staticmethod
    def _is_valid_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def _is_valid_phone(phone):
        """Validate phone format"""
        pattern = r'^\+?[0-9]{10,15}$'
        return re.match(pattern, phone) is not None


@dataclass
class Customer:
    """
    Customer entity representing a banking customer.
    
    The Customer entity is the core domain entity in the Customer Management module
    and contains all the essential attributes and business rules related to customers.
    """
    # Core attributes
    customer_id: str
    customer_type: CustomerType
    status: CustomerStatus
    registration_date: date
    
    # Individual or corporate specific fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    company_name: Optional[str] = None
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    
    # Contact details
    contact_information: Optional[ContactInformation] = None
    addresses: List[Address] = field(default_factory=list)
    
    # Compliance and risk
    risk_category: RiskCategory = RiskCategory.MEDIUM
    kyc_verified: bool = False
    aml_cleared: bool = False
    pep_status: bool = False  # Politically Exposed Person
    
    # Metadata
    custom_fields: Dict[str, str] = field(default_factory=dict)
    documents: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate customer data"""
        if not self.customer_id:
            raise ValueError("Customer ID is required")
            
        # Type-specific validations
        if self.customer_type == CustomerType.INDIVIDUAL:
            if not self.first_name or not self.last_name:
                raise ValueError("First and last name are required for individual customers")
            if not self.date_of_birth:
                raise ValueError("Date of birth is required for individual customers")
        elif self.customer_type == CustomerType.CORPORATE:
            if not self.company_name:
                raise ValueError("Company name is required for corporate customers")
            if not self.registration_number:
                raise ValueError("Registration number is required for corporate customers")
                
    def activate(self) -> None:
        """Activate the customer"""
        if self.status != CustomerStatus.ACTIVE:
            self.status = CustomerStatus.ACTIVE
            
    def deactivate(self) -> None:
        """Deactivate the customer"""
        if self.status == CustomerStatus.ACTIVE:
            self.status = CustomerStatus.INACTIVE
            
    def block(self) -> None:
        """Block the customer"""
        self.status = CustomerStatus.BLOCKED
        
    def close(self) -> None:
        """Close the customer relationship"""
        if self.status != CustomerStatus.CLOSED:
            self.status = CustomerStatus.CLOSED
            
    def update_risk_category(self, category: RiskCategory) -> None:
        """Update the customer's risk category"""
        self.risk_category = category
        
    def mark_kyc_verified(self) -> None:
        """Mark customer's KYC as verified"""
        self.kyc_verified = True
        
    def mark_aml_cleared(self) -> None:
        """Mark customer as cleared through AML checks"""
        self.aml_cleared = True
        
    def add_address(self, address: Address) -> None:
        """Add a new address for the customer"""
        # If this is a primary address, clear other primary flags
        if address.is_primary:
            for addr in self.addresses:
                if addr.address_type == address.address_type:
                    addr.is_primary = False
                    
        self.addresses.append(address)
        
    def update_contact_information(self, contact_info: ContactInformation) -> None:
        """Update customer contact information"""
        self.contact_information = contact_info
        
    def add_document(self, doc_type: str, doc_id: str, expiry_date: Optional[date] = None) -> None:
        """Add a document to the customer's profile"""
        document = {
            "doc_type": doc_type,
            "doc_id": doc_id,
            "issue_date": date.today(),
            "expiry_date": expiry_date
        }
        self.documents.append(document)
        
    def is_active(self) -> bool:
        """Check if the customer is active"""
        return self.status == CustomerStatus.ACTIVE
        
    def is_compliant(self) -> bool:
        """Check if the customer is compliant with KYC and AML regulations"""
        return self.kyc_verified and self.aml_cleared
        
    def is_high_risk(self) -> bool:
        """Check if the customer is high risk"""
        return self.risk_category == RiskCategory.HIGH or self.pep_status
