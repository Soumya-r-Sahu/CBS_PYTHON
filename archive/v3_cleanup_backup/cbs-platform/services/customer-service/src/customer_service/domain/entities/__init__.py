"""
Customer Domain Entities
Business entities representing customers in the banking domain
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class CustomerStatus(str, Enum):
    """Customer status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class KYCStatus(str, Enum):
    """KYC status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class DocumentType(str, Enum):
    """Document type enumeration"""
    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    INCOME_PROOF = "income_proof"
    PHOTO = "photo"


class RiskCategory(str, Enum):
    """Risk category enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class Address:
    """Address value object"""
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str
    address_type: str = "home"  # home, work, mailing
    is_primary: bool = False
    
    def __post_init__(self):
        if not self.street_address or not self.city:
            raise ValueError("Street address and city are required")


@dataclass
class ContactInformation:
    """Contact information value object"""
    phone_number: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[str] = None
    is_primary: bool = False
    
    def __post_init__(self):
        if not any([self.phone_number, self.mobile_number, self.email]):
            raise ValueError("At least one contact method is required")


@dataclass
class Document:
    """Document value object"""
    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_type: DocumentType = DocumentType.NATIONAL_ID
    document_number: str = ""
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: str = ""
    file_path: Optional[str] = None
    verification_status: str = "pending"  # pending, verified, rejected
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.document_number:
            raise ValueError("Document number is required")
    
    def is_expired(self) -> bool:
        """Check if document is expired"""
        if self.expiry_date:
            return self.expiry_date < date.today()
        return False
    
    def is_verified(self) -> bool:
        """Check if document is verified"""
        return self.verification_status == "verified"


@dataclass
class KYCInformation:
    """KYC information value object"""
    kyc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: KYCStatus = KYCStatus.PENDING
    documents: List[Document] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_notes: str = ""
    risk_score: int = 0
    risk_category: RiskCategory = RiskCategory.MEDIUM
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def add_document(self, document: Document):
        """Add document to KYC"""
        self.documents.append(document)
        self.last_updated = datetime.utcnow()
    
    def get_document(self, document_type: DocumentType) -> Optional[Document]:
        """Get document by type"""
        for doc in self.documents:
            if doc.document_type == document_type:
                return doc
        return None
    
    def is_complete(self) -> bool:
        """Check if KYC is complete"""
        return self.status == KYCStatus.COMPLETED
    
    def has_required_documents(self) -> bool:
        """Check if all required documents are present and verified"""
        required_docs = [DocumentType.NATIONAL_ID, DocumentType.PHOTO]
        for doc_type in required_docs:
            doc = self.get_document(doc_type)
            if not doc or not doc.is_verified():
                return False
        return True


@dataclass
class Customer:
    """Customer aggregate root"""
    customer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str = ""
    last_name: str = ""
    middle_name: str = ""
    date_of_birth: Optional[date] = None
    gender: str = ""
    nationality: str = ""
    occupation: str = ""
    annual_income: Optional[float] = None
    status: CustomerStatus = CustomerStatus.ACTIVE
    addresses: List[Address] = field(default_factory=list)
    contact_info: List[ContactInformation] = field(default_factory=list)
    kyc_information: Optional[KYCInformation] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    version: int = 1
    
    def __post_init__(self):
        if not self.first_name or not self.last_name:
            raise ValueError("First name and last name are required")
        
        if self.kyc_information is None:
            self.kyc_information = KYCInformation()
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> Optional[int]:
        """Calculate age from date of birth"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    def add_address(self, address: Address):
        """Add address to customer"""
        # If this is the first address or marked as primary, make it primary
        if not self.addresses or address.is_primary:
            # Remove primary flag from other addresses
            for addr in self.addresses:
                addr.is_primary = False
            address.is_primary = True
        
        self.addresses.append(address)
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def add_contact_info(self, contact: ContactInformation):
        """Add contact information to customer"""
        # If this is the first contact or marked as primary, make it primary
        if not self.contact_info or contact.is_primary:
            # Remove primary flag from other contacts
            for info in self.contact_info:
                info.is_primary = False
            contact.is_primary = True
        
        self.contact_info.append(contact)
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def get_primary_address(self) -> Optional[Address]:
        """Get primary address"""
        for address in self.addresses:
            if address.is_primary:
                return address
        return self.addresses[0] if self.addresses else None
    
    def get_primary_contact(self) -> Optional[ContactInformation]:
        """Get primary contact information"""
        for contact in self.contact_info:
            if contact.is_primary:
                return contact
        return self.contact_info[0] if self.contact_info else None
    
    def update_kyc_status(self, status: KYCStatus, reviewed_by: Optional[str] = None, notes: str = ""):
        """Update KYC status"""
        if self.kyc_information:
            self.kyc_information.status = status
            self.kyc_information.reviewed_by = reviewed_by
            self.kyc_information.review_notes = notes
            self.kyc_information.last_updated = datetime.utcnow()
            
            if status == KYCStatus.COMPLETED:
                self.kyc_information.completed_at = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def is_kyc_complete(self) -> bool:
        """Check if customer's KYC is complete"""
        return self.kyc_information and self.kyc_information.is_complete()
    
    def can_open_account(self) -> bool:
        """Check if customer can open new accounts"""
        return (
            self.status == CustomerStatus.ACTIVE and
            self.is_kyc_complete() and
            self.get_primary_address() is not None and
            self.get_primary_contact() is not None
        )
    
    def suspend(self, reason: str = ""):
        """Suspend customer"""
        self.status = CustomerStatus.SUSPENDED
        if reason:
            self.preferences["suspension_reason"] = reason
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def reactivate(self):
        """Reactivate customer"""
        self.status = CustomerStatus.ACTIVE
        if "suspension_reason" in self.preferences:
            del self.preferences["suspension_reason"]
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def close_account(self, reason: str = ""):
        """Close customer account"""
        self.status = CustomerStatus.CLOSED
        if reason:
            self.preferences["closure_reason"] = reason
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def update_personal_info(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        occupation: Optional[str] = None,
        annual_income: Optional[float] = None
    ):
        """Update personal information"""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if middle_name is not None:
            self.middle_name = middle_name
        if occupation is not None:
            self.occupation = occupation
        if annual_income is not None:
            self.annual_income = annual_income
        
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def set_preference(self, key: str, value: Any):
        """Set customer preference"""
        self.preferences[key] = value
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get customer preference"""
        return self.preferences.get(key, default)
