"""
Customer Service Data Transfer Objects (DTOs)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from ..domain.entities import Customer, CustomerStatus, KYCStatus, RiskCategory, DocumentType


# Request DTOs

class AddressRequestDTO(BaseModel):
    """Address request DTO"""
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str
    address_type: Optional[str] = "home"
    is_primary: Optional[bool] = False


class ContactRequestDTO(BaseModel):
    """Contact information request DTO"""
    phone_number: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[str] = None
    is_primary: Optional[bool] = False
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email address')
        return v


class CreateCustomerRequest(BaseModel):
    """Create customer request DTO"""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=10)
    nationality: Optional[str] = Field(None, max_length=50)
    occupation: Optional[str] = Field(None, max_length=100)
    annual_income: Optional[float] = Field(None, ge=0)
    address: Optional[AddressRequestDTO] = None
    contact: Optional[ContactRequestDTO] = None
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if v and v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        if v and (date.today() - v).days < 18 * 365:
            raise ValueError('Customer must be at least 18 years old')
        return v


class UpdateCustomerRequest(BaseModel):
    """Update customer request DTO"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    occupation: Optional[str] = Field(None, max_length=100)
    annual_income: Optional[float] = Field(None, ge=0)


class AddAddressRequest(BaseModel):
    """Add address request DTO"""
    street_address: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=50)
    state: str = Field(..., min_length=1, max_length=50)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=50)
    address_type: Optional[str] = Field("home", max_length=20)
    is_primary: Optional[bool] = False


class AddContactRequest(BaseModel):
    """Add contact request DTO"""
    phone_number: Optional[str] = Field(None, max_length=20)
    mobile_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = False
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email address')
        return v


class UpdateKYCRequest(BaseModel):
    """Update KYC request DTO"""
    status: KYCStatus
    notes: Optional[str] = Field(None, max_length=500)
    risk_score: Optional[int] = Field(None, ge=0, le=100)
    risk_category: Optional[RiskCategory] = None


class AddDocumentRequest(BaseModel):
    """Add document request DTO"""
    document_type: DocumentType
    document_number: str = Field(..., min_length=1, max_length=50)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = Field(None, max_length=100)
    file_path: str = Field(..., min_length=1)


# Response DTOs

class AddressResponseDTO(BaseModel):
    """Address response DTO"""
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str
    address_type: str
    is_primary: bool


class ContactResponseDTO(BaseModel):
    """Contact response DTO"""
    phone_number: Optional[str]
    mobile_number: Optional[str]
    email: Optional[str]
    is_primary: bool


class DocumentResponseDTO(BaseModel):
    """Document response DTO"""
    document_id: str
    document_type: DocumentType
    document_number: str
    issue_date: Optional[date]
    expiry_date: Optional[date]
    issuing_authority: str
    verification_status: str
    verified_by: Optional[str]
    verified_at: Optional[datetime]
    is_expired: bool
    is_verified: bool


class KYCResponseDTO(BaseModel):
    """KYC response DTO"""
    kyc_id: str
    status: KYCStatus
    documents: List[DocumentResponseDTO]
    completed_at: Optional[datetime]
    reviewed_by: Optional[str]
    review_notes: str
    risk_score: int
    risk_category: RiskCategory
    last_updated: datetime
    is_complete: bool
    has_required_documents: bool


class CustomerResponse(BaseModel):
    """Customer response DTO"""
    customer_id: str
    first_name: str
    last_name: str
    middle_name: str
    full_name: str
    date_of_birth: Optional[date]
    age: Optional[int]
    gender: str
    nationality: str
    occupation: str
    annual_income: Optional[float]
    status: CustomerStatus
    addresses: List[AddressResponseDTO]
    contact_info: List[ContactResponseDTO]
    kyc_information: Optional[KYCResponseDTO]
    preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    version: int
    can_open_account: bool
    
    @classmethod
    def from_entity(cls, customer: Customer) -> "CustomerResponse":
        """Create response DTO from customer entity"""
        
        # Convert addresses
        addresses = [
            AddressResponseDTO(
                street_address=addr.street_address,
                city=addr.city,
                state=addr.state,
                postal_code=addr.postal_code,
                country=addr.country,
                address_type=addr.address_type,
                is_primary=addr.is_primary
            )
            for addr in customer.addresses
        ]
        
        # Convert contact info
        contacts = [
            ContactResponseDTO(
                phone_number=contact.phone_number,
                mobile_number=contact.mobile_number,
                email=contact.email,
                is_primary=contact.is_primary
            )
            for contact in customer.contact_info
        ]
        
        # Convert KYC information
        kyc_info = None
        if customer.kyc_information:
            documents = [
                DocumentResponseDTO(
                    document_id=doc.document_id,
                    document_type=doc.document_type,
                    document_number=doc.document_number,
                    issue_date=doc.issue_date,
                    expiry_date=doc.expiry_date,
                    issuing_authority=doc.issuing_authority,
                    verification_status=doc.verification_status,
                    verified_by=doc.verified_by,
                    verified_at=doc.verified_at,
                    is_expired=doc.is_expired(),
                    is_verified=doc.is_verified()
                )
                for doc in customer.kyc_information.documents
            ]
            
            kyc_info = KYCResponseDTO(
                kyc_id=customer.kyc_information.kyc_id,
                status=customer.kyc_information.status,
                documents=documents,
                completed_at=customer.kyc_information.completed_at,
                reviewed_by=customer.kyc_information.reviewed_by,
                review_notes=customer.kyc_information.review_notes,
                risk_score=customer.kyc_information.risk_score,
                risk_category=customer.kyc_information.risk_category,
                last_updated=customer.kyc_information.last_updated,
                is_complete=customer.kyc_information.is_complete(),
                has_required_documents=customer.kyc_information.has_required_documents()
            )
        
        return cls(
            customer_id=customer.customer_id,
            first_name=customer.first_name,
            last_name=customer.last_name,
            middle_name=customer.middle_name,
            full_name=customer.full_name,
            date_of_birth=customer.date_of_birth,
            age=customer.age,
            gender=customer.gender,
            nationality=customer.nationality,
            occupation=customer.occupation,
            annual_income=customer.annual_income,
            status=customer.status,
            addresses=addresses,
            contact_info=contacts,
            kyc_information=kyc_info,
            preferences=customer.preferences,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            created_by=customer.created_by,
            version=customer.version,
            can_open_account=customer.can_open_account()
        )


class CustomerListResponse(BaseModel):
    """Customer list response DTO"""
    customers: List[CustomerResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class CustomerStatsResponse(BaseModel):
    """Customer statistics response DTO"""
    total_customers: int
    active_customers: int
    inactive_customers: int
    suspended_customers: int
    closed_customers: int
    kyc_completed: int
    kyc_pending: int
    kyc_rejected: int
    customers_by_risk_category: Dict[str, int]
    new_customers_this_month: int
    new_customers_this_year: int
