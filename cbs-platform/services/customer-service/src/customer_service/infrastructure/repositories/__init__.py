"""
Customer Service Repository Implementations
Concrete implementations of repository interfaces using SQLAlchemy
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime
import json

from ...domain.entities import Customer, CustomerDocument, Address, ContactInfo, IdentificationDocument
from ...application.use_cases import CustomerRepository, DocumentRepository
from ...application.dto import (
    CustomerListRequest, CustomerListResponse, CustomerResponse,
    DocumentResponse, customer_to_response, document_to_response
)
from ..database import get_db_session, close_db_session, CustomerModel, DocumentModel


class SQLAlchemyCustomerRepository(CustomerRepository):
    """SQLAlchemy implementation of CustomerRepository"""
    
    def __init__(self):
        self.session: Optional[Session] = None
    
    def _get_session(self) -> Session:
        """Get database session"""
        if not self.session:
            self.session = get_db_session()
        return self.session
    
    def _close_session(self):
        """Close database session"""
        if self.session:
            close_db_session(self.session)
            self.session = None
    
    def _model_to_entity(self, model: CustomerModel) -> Customer:
        """Convert database model to domain entity"""
        address = Address(
            line1=model.address_line1 or "",
            line2=model.address_line2 or "",
            city=model.city or "",
            state=model.state or "",
            postal_code=model.postal_code or "",
            country=model.country or ""
        )
        
        contact_info = ContactInfo(
            email=model.email or "",
            phone=model.phone or "",
            alternate_phone=model.alternate_phone
        )
        
        identification = IdentificationDocument(
            id_type=model.id_type or "",
            id_number=model.id_number or "",
            issue_date=model.id_issue_date,
            expiry_date=model.id_expiry_date,
            issuing_authority=model.id_issuing_authority
        )
        
        # Parse metadata
        metadata = {}
        if model.metadata_json:
            try:
                metadata = json.loads(model.metadata_json)
            except json.JSONDecodeError:
                pass
        
        return Customer(
            customer_id=model.customer_id,
            customer_number=model.customer_number,
            customer_type=model.customer_type,
            status=model.status,
            first_name=model.first_name,
            middle_name=model.middle_name,
            last_name=model.last_name,
            date_of_birth=model.date_of_birth,
            gender=model.gender,
            nationality=model.nationality,
            marital_status=model.marital_status,
            address=address,
            contact_info=contact_info,
            identification=identification,
            occupation=model.occupation,
            employer_name=model.employer_name,
            annual_income=model.annual_income,
            income_currency=model.income_currency,
            source_of_funds=model.source_of_funds,
            risk_profile=model.risk_profile,
            aml_status=model.aml_status,
            kyc_status=model.kyc_status,
            kyc_completion_date=model.kyc_completion_date,
            sanctions_screening_status=model.sanctions_screening_status,
            pep_status=model.pep_status,
            preferred_language=model.preferred_language,
            preferred_communication_channel=model.preferred_communication_channel,
            marketing_consent=model.marketing_consent,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_by=model.updated_by,
            updated_at=model.updated_at,
            metadata=metadata,
            version=model.version
        )
    
    def _entity_to_model(self, customer: Customer) -> CustomerModel:
        """Convert domain entity to database model"""
        return CustomerModel(
            customer_id=customer.customer_id,
            customer_number=customer.customer_number,
            customer_type=customer.customer_type.value,
            status=customer.status.value,
            first_name=customer.first_name,
            middle_name=customer.middle_name,
            last_name=customer.last_name,
            full_name=customer.get_full_name(),
            date_of_birth=customer.date_of_birth,
            gender=customer.gender,
            nationality=customer.nationality,
            marital_status=customer.marital_status,
            email=customer.contact_info.email,
            phone=customer.contact_info.phone,
            alternate_phone=customer.contact_info.alternate_phone,
            address_line1=customer.address.line1,
            address_line2=customer.address.line2,
            city=customer.address.city,
            state=customer.address.state,
            postal_code=customer.address.postal_code,
            country=customer.address.country,
            id_type=customer.identification.id_type,
            id_number=customer.identification.id_number,
            id_issue_date=customer.identification.issue_date,
            id_expiry_date=customer.identification.expiry_date,
            id_issuing_authority=customer.identification.issuing_authority,
            occupation=customer.occupation,
            employer_name=customer.employer_name,
            annual_income=customer.annual_income,
            income_currency=customer.income_currency,
            source_of_funds=customer.source_of_funds,
            risk_profile=customer.risk_profile.value,
            aml_status=customer.aml_status.value,
            kyc_status=customer.kyc_status.value,
            kyc_completion_date=customer.kyc_completion_date,
            sanctions_screening_status=customer.sanctions_screening_status.value,
            pep_status=customer.pep_status,
            preferred_language=customer.preferred_language,
            preferred_communication_channel=customer.preferred_communication_channel.value,
            marketing_consent=customer.marketing_consent,
            created_by=customer.created_by,
            created_at=customer.created_at,
            updated_by=customer.updated_by,
            updated_at=customer.updated_at,
            metadata_json=json.dumps(customer.metadata),
            version=customer.version
        )
    
    async def save(self, customer: Customer) -> Customer:
        """Save customer to database"""
        try:
            session = self._get_session()
            
            # Check if customer exists
            existing = session.query(CustomerModel).filter(
                CustomerModel.customer_id == customer.customer_id
            ).first()
            
            if existing:
                # Update existing customer
                model = self._entity_to_model(customer)
                for key, value in model.__dict__.items():
                    if key != '_sa_instance_state' and hasattr(existing, key):
                        setattr(existing, key, value)
                session.commit()
                session.refresh(existing)
                return self._model_to_entity(existing)
            else:
                # Create new customer
                model = self._entity_to_model(customer)
                session.add(model)
                session.commit()
                session.refresh(model)
                return self._model_to_entity(model)
                
        except Exception as e:
            if session:
                session.rollback()
            raise e
        finally:
            self._close_session()
    
    async def find_by_id(self, customer_id: str) -> Optional[Customer]:
        """Find customer by ID"""
        try:
            session = self._get_session()
            model = session.query(CustomerModel).filter(
                CustomerModel.customer_id == customer_id
            ).first()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except Exception as e:
            raise e
        finally:
            self._close_session()
    
    async def find_by_customer_number(self, customer_number: str) -> Optional[Customer]:
        """Find customer by customer number"""
        try:
            session = self._get_session()
            model = session.query(CustomerModel).filter(
                CustomerModel.customer_number == customer_number
            ).first()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except Exception as e:
            raise e
        finally:
            self._close_session()
    
    async def find_by_email(self, email: str) -> Optional[Customer]:
        """Find customer by email"""
        try:
            session = self._get_session()
            model = session.query(CustomerModel).filter(
                CustomerModel.email == email
            ).first()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except Exception as e:
            raise e
        finally:
            self._close_session()
    
    async def find_by_phone(self, phone: str) -> Optional[Customer]:
        """Find customer by phone"""
        try:
            session = self._get_session()
            model = session.query(CustomerModel).filter(
                or_(
                    CustomerModel.phone == phone,
                    CustomerModel.alternate_phone == phone
                )
            ).first()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except Exception as e:
            raise e
        finally:
            self._close_session()
    
    async def find_by_id_number(self, id_type: str, id_number: str) -> Optional[Customer]:
        """Find customer by identification number"""
        try:
            session = self._get_session()
            model = session.query(CustomerModel).filter(
                and_(
                    CustomerModel.id_type == id_type,
                    CustomerModel.id_number == id_number
                )
            ).first()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except Exception as e:
            raise e
        finally:
            self._close_session()
    
    async def find_by_criteria(self, request: CustomerListRequest) -> CustomerListResponse:
        """Find customers by criteria with pagination"""
        try:
            session = self._get_session()
            query = session.query(CustomerModel)
            
            # Apply filters
            if request.customer_type:
                query = query.filter(CustomerModel.customer_type == request.customer_type.value)
            
            if request.status:
                query = query.filter(CustomerModel.status == request.status.value)
            
            if request.kyc_status:
                query = query.filter(CustomerModel.kyc_status == request.kyc_status.value)
            
            if request.risk_profile:
                query = query.filter(CustomerModel.risk_profile == request.risk_profile.value)
            
            if request.search_term:
                search_filter = or_(
                    CustomerModel.customer_number.ilike(f"%{request.search_term}%"),
                    CustomerModel.first_name.ilike(f"%{request.search_term}%"),
                    CustomerModel.last_name.ilike(f"%{request.search_term}%"),
                    CustomerModel.email.ilike(f"%{request.search_term}%"),
                    CustomerModel.phone.ilike(f"%{request.search_term}%")
                )
                query = query.filter(search_filter)
            
            if request.created_from:
                query = query.filter(CustomerModel.created_at >= request.created_from)
            
            if request.created_to:
                query = query.filter(CustomerModel.created_at <= request.created_to)
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            if request.sort_order.lower() == "desc":
                query = query.order_by(desc(getattr(CustomerModel, request.sort_by)))
            else:
                query = query.order_by(asc(getattr(CustomerModel, request.sort_by)))
            
            # Apply pagination
            offset = (request.page - 1) * request.size
            query = query.offset(offset).limit(request.size)
            
            # Execute query
            models = query.all()
            customers = [customer_to_response(self._model_to_entity(model)) for model in models]
            
            total_pages = (total_count + request.size - 1) // request.size
            
            return CustomerListResponse(
                customers=customers,
                total_count=total_count,
                page=request.page,
                size=request.size,
                total_pages=total_pages
            )
            
        except Exception as e:
            raise e
        finally:
            self._close_session()
    
    async def delete(self, customer_id: str) -> bool:
        """Delete customer (soft delete by updating status)"""
        try:
            session = self._get_session()
            model = session.query(CustomerModel).filter(
                CustomerModel.customer_id == customer_id
            ).first()
            
            if model:
                model.status = "DELETED"
                model.updated_at = datetime.utcnow()
                model.version += 1
                session.commit()
                return True
            
            return False
            
        except Exception as e:
            if session:
                session.rollback()
            raise e
        finally:
            self._close_session()


class SQLAlchemyDocumentRepository(DocumentRepository):
    """SQLAlchemy implementation of DocumentRepository"""
    
    def __init__(self):
        self.session: Optional[Session] = None
    
    def _get_session(self) -> Session:
        """Get database session"""
        if not self.session:
            self.session = get_db_session()
        return self.session
    
    def _close_session(self):
        """Close database session"""
        if self.session:
            close_db_session(self.session)
            self.session = None
    
    def _model_to_entity(self, model: DocumentModel) -> CustomerDocument:
        """Convert database model to domain entity"""
        return CustomerDocument(
            document_id=model.document_id,
            customer_id=model.customer_id,
            document_type=model.document_type,
            document_name=model.document_name,
            file_path=model.file_path,
            file_size=model.file_size,
            mime_type=model.mime_type,
            checksum=model.checksum,
            status=model.status,
            verification_status=model.verification_status,
            verified_by=model.verified_by,
            verified_at=model.verified_at,
            verification_notes=model.verification_notes,
            issue_date=model.issue_date,
            expiry_date=model.expiry_date,
            issuing_authority=model.issuing_authority,
            uploaded_by=model.uploaded_by,
            uploaded_at=model.uploaded_at,
            updated_at=model.updated_at,
            version=model.version
        )
    
    def _entity_to_model(self, document: CustomerDocument) -> DocumentModel:
        """Convert domain entity to database model"""
        return DocumentModel(
            document_id=document.document_id,
            customer_id=document.customer_id,
            document_type=document.document_type.value,
            document_name=document.document_name,
            file_path=document.file_path,
            file_size=document.file_size,
            mime_type=document.mime_type,
            checksum=document.checksum,
            status=document.status.value,
            verification_status=document.verification_status.value,
            verified_by=document.verified_by,
            verified_at=document.verified_at,
            verification_notes=document.verification_notes,
            issue_date=document.issue_date,
            expiry_date=document.expiry_date,
            issuing_authority=document.issuing_authority,
            uploaded_by=document.uploaded_by,
            uploaded_at=document.uploaded_at,
            updated_at=document.updated_at,
            version=document.version
        )
    
    async def save(self, document: CustomerDocument) -> CustomerDocument:
        """Save document to database"""
        try:
            session = self._get_session()
            
            # Check if document exists
            existing = session.query(DocumentModel).filter(
                DocumentModel.document_id == document.document_id
            ).first()
            
            if existing:
                # Update existing document
                model = self._entity_to_model(document)
                for key, value in model.__dict__.items():
                    if key != '_sa_instance_state' and hasattr(existing, key):
                        setattr(existing, key, value)
                session.commit()
                session.refresh(existing)
                return self._model_to_entity(existing)
            else:
                # Create new document
                model = self._entity_to_model(document)
                session.add(model)
                session.commit()
                session.refresh(model)
                return self._model_to_entity(model)
                
        except Exception as e:
            if session:
                session.rollback()
            raise e
        finally:
            self._close_session()
    
    async def find_by_id(self, document_id: str) -> Optional[CustomerDocument]:
        """Find document by ID"""
        try:
            session = self._get_session()
            model = session.query(DocumentModel).filter(
                DocumentModel.document_id == document_id
            ).first()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except Exception as e:
            raise e
        finally:
            self._close_session()
    
    async def find_by_customer_id(self, customer_id: str) -> List[CustomerDocument]:
        """Find all documents for a customer"""
        try:
            session = self._get_session()
            models = session.query(DocumentModel).filter(
                DocumentModel.customer_id == customer_id
            ).all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            raise e
        finally:
            self._close_session()
    
    async def delete(self, document_id: str) -> bool:
        """Delete document"""
        try:
            session = self._get_session()
            deleted = session.query(DocumentModel).filter(
                DocumentModel.document_id == document_id
            ).delete()
            
            session.commit()
            return deleted > 0
            
        except Exception as e:
            if session:
                session.rollback()
            raise e
        finally:
            self._close_session()
