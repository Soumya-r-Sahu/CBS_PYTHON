"""
Customer Service Use Cases
Application layer containing business use cases
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging

from ..domain.entities import (
    Customer, Address, ContactInformation, Document, 
    CustomerStatus, KYCStatus, DocumentType, RiskCategory
)
from ..application.interfaces import CustomerRepository, EventPublisher
from ..application.dto import (
    CreateCustomerRequest, UpdateCustomerRequest, CustomerResponse,
    AddAddressRequest, AddContactRequest, UpdateKYCRequest
)
from platform.shared.events import (
    DomainEvent, EventType, create_customer_event
)

logger = logging.getLogger(__name__)


class CustomerService:
    """Customer service containing business use cases"""
    
    def __init__(
        self, 
        customer_repository: CustomerRepository,
        event_publisher: EventPublisher
    ):
        self.customer_repository = customer_repository
        self.event_publisher = event_publisher
    
    async def create_customer(
        self, 
        request: CreateCustomerRequest,
        created_by: str
    ) -> CustomerResponse:
        """Create a new customer"""
        logger.info(f"Creating customer: {request.first_name} {request.last_name}")
        
        # Create customer entity
        customer = Customer(
            first_name=request.first_name,
            last_name=request.last_name,
            middle_name=request.middle_name or "",
            date_of_birth=request.date_of_birth,
            gender=request.gender or "",
            nationality=request.nationality or "",
            occupation=request.occupation or "",
            annual_income=request.annual_income,
            created_by=created_by
        )
        
        # Add primary address if provided
        if request.address:
            address = Address(
                street_address=request.address.street_address,
                city=request.address.city,
                state=request.address.state,
                postal_code=request.address.postal_code,
                country=request.address.country,
                is_primary=True
            )
            customer.add_address(address)
        
        # Add primary contact if provided
        if request.contact:
            contact = ContactInformation(
                phone_number=request.contact.phone_number,
                mobile_number=request.contact.mobile_number,
                email=request.contact.email,
                is_primary=True
            )
            customer.add_contact_info(contact)
        
        # Save customer
        saved_customer = await self.customer_repository.save(customer)
        
        # Publish event
        event = create_customer_event(
            event_type=EventType.CUSTOMER_CREATED,
            customer_id=saved_customer.customer_id,
            user_id=created_by,
            source_service="customer-service",
            data={
                "customer_id": saved_customer.customer_id,
                "full_name": saved_customer.full_name,
                "email": request.contact.email if request.contact else None
            }
        )
        await self.event_publisher.publish(event)
        
        logger.info(f"Customer created successfully: {saved_customer.customer_id}")
        return CustomerResponse.from_entity(saved_customer)
    
    async def get_customer(self, customer_id: str) -> Optional[CustomerResponse]:
        """Get customer by ID"""
        customer = await self.customer_repository.get_by_id(customer_id)
        if customer:
            return CustomerResponse.from_entity(customer)
        return None
    
    async def get_customer_by_email(self, email: str) -> Optional[CustomerResponse]:
        """Get customer by email"""
        customer = await self.customer_repository.get_by_email(email)
        if customer:
            return CustomerResponse.from_entity(customer)
        return None
    
    async def search_customers(
        self,
        query: str,
        status: Optional[CustomerStatus] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[CustomerResponse]:
        """Search customers"""
        customers = await self.customer_repository.search(
            query=query,
            status=status,
            limit=limit,
            offset=offset
        )
        return [CustomerResponse.from_entity(customer) for customer in customers]
    
    async def update_customer(
        self,
        customer_id: str,
        request: UpdateCustomerRequest,
        updated_by: str
    ) -> Optional[CustomerResponse]:
        """Update customer information"""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            return None
        
        # Update personal information
        customer.update_personal_info(
            first_name=request.first_name,
            last_name=request.last_name,
            middle_name=request.middle_name,
            occupation=request.occupation,
            annual_income=request.annual_income
        )
        
        # Save updated customer
        updated_customer = await self.customer_repository.save(customer)
        
        # Publish event
        event = create_customer_event(
            event_type=EventType.CUSTOMER_UPDATED,
            customer_id=updated_customer.customer_id,
            user_id=updated_by,
            source_service="customer-service",
            data={
                "customer_id": updated_customer.customer_id,
                "updated_fields": request.dict(exclude_unset=True)
            }
        )
        await self.event_publisher.publish(event)
        
        return CustomerResponse.from_entity(updated_customer)
    
    async def add_address(
        self,
        customer_id: str,
        request: AddAddressRequest,
        added_by: str
    ) -> Optional[CustomerResponse]:
        """Add address to customer"""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            return None
        
        address = Address(
            street_address=request.street_address,
            city=request.city,
            state=request.state,
            postal_code=request.postal_code,
            country=request.country,
            address_type=request.address_type or "home",
            is_primary=request.is_primary or False
        )
        
        customer.add_address(address)
        updated_customer = await self.customer_repository.save(customer)
        
        return CustomerResponse.from_entity(updated_customer)
    
    async def add_contact_info(
        self,
        customer_id: str,
        request: AddContactRequest,
        added_by: str
    ) -> Optional[CustomerResponse]:
        """Add contact information to customer"""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            return None
        
        contact = ContactInformation(
            phone_number=request.phone_number,
            mobile_number=request.mobile_number,
            email=request.email,
            is_primary=request.is_primary or False
        )
        
        customer.add_contact_info(contact)
        updated_customer = await self.customer_repository.save(customer)
        
        return CustomerResponse.from_entity(updated_customer)
    
    async def update_kyc_status(
        self,
        customer_id: str,
        request: UpdateKYCRequest,
        updated_by: str
    ) -> Optional[CustomerResponse]:
        """Update customer KYC status"""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            return None
        
        old_status = customer.kyc_information.status if customer.kyc_information else KYCStatus.PENDING
        
        customer.update_kyc_status(
            status=request.status,
            reviewed_by=updated_by,
            notes=request.notes or ""
        )
        
        if request.risk_score is not None and customer.kyc_information:
            customer.kyc_information.risk_score = request.risk_score
        
        if request.risk_category and customer.kyc_information:
            customer.kyc_information.risk_category = request.risk_category
        
        updated_customer = await self.customer_repository.save(customer)
        
        # Publish KYC event
        event_type = EventType.CUSTOMER_KYC_COMPLETED if request.status == KYCStatus.COMPLETED else EventType.CUSTOMER_UPDATED
        
        if request.status == KYCStatus.REJECTED:
            event_type = EventType.CUSTOMER_KYC_FAILED
        
        event = create_customer_event(
            event_type=event_type,
            customer_id=updated_customer.customer_id,
            user_id=updated_by,
            source_service="customer-service",
            data={
                "customer_id": updated_customer.customer_id,
                "old_kyc_status": old_status,
                "new_kyc_status": request.status,
                "risk_score": request.risk_score,
                "risk_category": request.risk_category
            }
        )
        await self.event_publisher.publish(event)
        
        return CustomerResponse.from_entity(updated_customer)
    
    async def add_document(
        self,
        customer_id: str,
        document_type: DocumentType,
        document_number: str,
        file_path: str,
        issue_date: Optional[date] = None,
        expiry_date: Optional[date] = None,
        issuing_authority: str = "",
        added_by: str = ""
    ) -> Optional[CustomerResponse]:
        """Add document to customer KYC"""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            return None
        
        document = Document(
            document_type=document_type,
            document_number=document_number,
            issue_date=issue_date,
            expiry_date=expiry_date,
            issuing_authority=issuing_authority,
            file_path=file_path
        )
        
        if customer.kyc_information:
            customer.kyc_information.add_document(document)
        
        updated_customer = await self.customer_repository.save(customer)
        return CustomerResponse.from_entity(updated_customer)
    
    async def suspend_customer(
        self,
        customer_id: str,
        reason: str,
        suspended_by: str
    ) -> Optional[CustomerResponse]:
        """Suspend customer account"""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            return None
        
        customer.suspend(reason)
        updated_customer = await self.customer_repository.save(customer)
        
        # Publish event
        event = create_customer_event(
            event_type=EventType.CUSTOMER_UPDATED,
            customer_id=updated_customer.customer_id,
            user_id=suspended_by,
            source_service="customer-service",
            data={
                "customer_id": updated_customer.customer_id,
                "action": "suspended",
                "reason": reason
            }
        )
        await self.event_publisher.publish(event)
        
        return CustomerResponse.from_entity(updated_customer)
    
    async def reactivate_customer(
        self,
        customer_id: str,
        reactivated_by: str
    ) -> Optional[CustomerResponse]:
        """Reactivate suspended customer"""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            return None
        
        customer.reactivate()
        updated_customer = await self.customer_repository.save(customer)
        
        # Publish event
        event = create_customer_event(
            event_type=EventType.CUSTOMER_UPDATED,
            customer_id=updated_customer.customer_id,
            user_id=reactivated_by,
            source_service="customer-service",
            data={
                "customer_id": updated_customer.customer_id,
                "action": "reactivated"
            }
        )
        await self.event_publisher.publish(event)
        
        return CustomerResponse.from_entity(updated_customer)
    
    async def get_customer_statistics(self) -> Dict[str, Any]:
        """Get customer statistics"""
        stats = await self.customer_repository.get_statistics()
        return stats
