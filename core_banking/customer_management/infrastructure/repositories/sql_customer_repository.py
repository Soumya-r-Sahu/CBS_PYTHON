"""
SQL Customer Repository

This module implements the customer repository interface using SQL database.
"""
from typing import List, Optional, Dict, Any
from datetime import date

from sqlalchemy import create_engine, Column, String, Date, Boolean, Integer, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from ...domain.entities.customer import Customer, CustomerType, CustomerStatus, RiskCategory, Address, ContactInformation
from ...application.interfaces.customer_repository_interface import CustomerRepositoryInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



# SQLAlchemy models
Base = declarative_base()

class CustomerModel(Base):
    """SQLAlchemy model for customer table"""
    __tablename__ = 'customers'
    
    customer_id = Column(String(50), primary_key=True)
    customer_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    registration_date = Column(Date, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    middle_name = Column(String(100))
    date_of_birth = Column(Date)
    company_name = Column(String(200))
    registration_number = Column(String(100))
    tax_id = Column(String(50))
    risk_category = Column(String(20), nullable=False)
    kyc_verified = Column(Boolean, default=False)
    aml_cleared = Column(Boolean, default=False)
    pep_status = Column(Boolean, default=False)
    
    # Relationships
    addresses = relationship("AddressModel", back_populates="customer", cascade="all, delete-orphan")
    contacts = relationship("ContactModel", back_populates="customer", cascade="all, delete-orphan")
    documents = relationship("DocumentModel", back_populates="customer", cascade="all, delete-orphan")
    custom_fields = relationship("CustomFieldModel", back_populates="customer", cascade="all, delete-orphan")


class AddressModel(Base):
    """SQLAlchemy model for address table"""
    __tablename__ = 'addresses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), ForeignKey('customers.customer_id'), nullable=False)
    street = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False)
    address_type = Column(String(20), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    # Relationship
    customer = relationship("CustomerModel", back_populates="addresses")


class ContactModel(Base):
    """SQLAlchemy model for contact information table"""
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), ForeignKey('customers.customer_id'), nullable=False)
    email = Column(String(100))
    primary_phone = Column(String(20))
    secondary_phone = Column(String(20))
    
    # Relationship
    customer = relationship("CustomerModel", back_populates="contacts")


class DocumentModel(Base):
    """SQLAlchemy model for document table"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), ForeignKey('customers.customer_id'), nullable=False)
    doc_type = Column(String(50), nullable=False)
    doc_id = Column(String(100), nullable=False)
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date)
    
    # Relationship
    customer = relationship("CustomerModel", back_populates="documents")


class CustomFieldModel(Base):
    """SQLAlchemy model for custom fields table"""
    __tablename__ = 'custom_fields'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), ForeignKey('customers.customer_id'), nullable=False)
    field_name = Column(String(100), nullable=False)
    field_value = Column(Text)
    
    # Relationship
    customer = relationship("CustomerModel", back_populates="custom_fields")


class SqlCustomerRepository(CustomerRepositoryInterface):
    """
    SQL implementation of customer repository interface.
    
    This class implements the customer repository interface using SQLAlchemy
    to interact with a SQL database.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize the repository with a database connection.
        
        Args:
            connection_string: Database connection string
        """
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
    
    def create(self, customer: Customer) -> Customer:
        """Create a new customer record"""
        session = self.Session()
        try:
            # Create customer model
            customer_model = CustomerModel(
                customer_id=customer.customer_id,
                customer_type=customer.customer_type.value,
                status=customer.status.value,
                registration_date=customer.registration_date,
                first_name=customer.first_name,
                last_name=customer.last_name,
                middle_name=customer.middle_name,
                date_of_birth=customer.date_of_birth,
                company_name=customer.company_name,
                registration_number=customer.registration_number,
                tax_id=customer.tax_id,
                risk_category=customer.risk_category.value,
                kyc_verified=customer.kyc_verified,
                aml_cleared=customer.aml_cleared,
                pep_status=customer.pep_status
            )
            
            # Add addresses
            for address in customer.addresses:
                address_model = AddressModel(
                    street=address.street,
                    city=address.city,
                    state=address.state,
                    postal_code=address.postal_code,
                    country=address.country,
                    address_type=address.address_type,
                    is_primary=address.is_primary
                )
                customer_model.addresses.append(address_model)
            
            # Add contact information
            if customer.contact_information:
                contact_model = ContactModel(
                    email=customer.contact_information.email,
                    primary_phone=customer.contact_information.primary_phone,
                    secondary_phone=customer.contact_information.secondary_phone
                )
                customer_model.contacts.append(contact_model)
            
            # Add documents
            for doc in customer.documents:
                doc_model = DocumentModel(
                    doc_type=doc.get("doc_type"),
                    doc_id=doc.get("doc_id"),
                    issue_date=doc.get("issue_date"),
                    expiry_date=doc.get("expiry_date")
                )
                customer_model.documents.append(doc_model)
            
            # Add custom fields
            for key, value in customer.custom_fields.items():
                field_model = CustomFieldModel(
                    field_name=key,
                    field_value=value
                )
                customer_model.custom_fields.append(field_model)
            
            # Save to database
            session.add(customer_model)
            session.commit()
            
            # Return updated customer entity with generated ID if applicable
            customer.customer_id = customer_model.customer_id
            return customer
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Retrieve a customer by their ID"""
        session = self.Session()
        try:
            customer_model = session.query(CustomerModel).filter_by(customer_id=customer_id).first()
            if not customer_model:
                return None
                
            return self._model_to_entity(customer_model)
            
        finally:
            session.close()
    
    def update(self, customer: Customer) -> Customer:
        """Update an existing customer record"""
        session = self.Session()
        try:
            # Get existing customer
            customer_model = session.query(CustomerModel).filter_by(customer_id=customer.customer_id).first()
            if not customer_model:
                raise ValueError(f"Customer not found with ID: {customer.customer_id}")
            
            # Update customer attributes
            customer_model.customer_type = customer.customer_type.value
            customer_model.status = customer.status.value
            customer_model.first_name = customer.first_name
            customer_model.last_name = customer.last_name
            customer_model.middle_name = customer.middle_name
            customer_model.date_of_birth = customer.date_of_birth
            customer_model.company_name = customer.company_name
            customer_model.registration_number = customer.registration_number
            customer_model.tax_id = customer.tax_id
            customer_model.risk_category = customer.risk_category.value
            customer_model.kyc_verified = customer.kyc_verified
            customer_model.aml_cleared = customer.aml_cleared
            customer_model.pep_status = customer.pep_status
            
            # Handle addresses (clear and recreate)
            session.query(AddressModel).filter_by(customer_id=customer.customer_id).delete()
            for address in customer.addresses:
                address_model = AddressModel(
                    customer_id=customer.customer_id,
                    street=address.street,
                    city=address.city,
                    state=address.state,
                    postal_code=address.postal_code,
                    country=address.country,
                    address_type=address.address_type,
                    is_primary=address.is_primary
                )
                session.add(address_model)
            
            # Handle contact info (clear and recreate)
            session.query(ContactModel).filter_by(customer_id=customer.customer_id).delete()
            if customer.contact_information:
                contact_model = ContactModel(
                    customer_id=customer.customer_id,
                    email=customer.contact_information.email,
                    primary_phone=customer.contact_information.primary_phone,
                    secondary_phone=customer.contact_information.secondary_phone
                )
                session.add(contact_model)
            
            # Handle documents (clear and recreate)
            session.query(DocumentModel).filter_by(customer_id=customer.customer_id).delete()
            for doc in customer.documents:
                doc_model = DocumentModel(
                    customer_id=customer.customer_id,
                    doc_type=doc.get("doc_type"),
                    doc_id=doc.get("doc_id"),
                    issue_date=doc.get("issue_date"),
                    expiry_date=doc.get("expiry_date")
                )
                session.add(doc_model)
            
            # Handle custom fields (clear and recreate)
            session.query(CustomFieldModel).filter_by(customer_id=customer.customer_id).delete()
            for key, value in customer.custom_fields.items():
                field_model = CustomFieldModel(
                    customer_id=customer.customer_id,
                    field_name=key,
                    field_value=value
                )
                session.add(field_model)
            
            # Commit changes
            session.commit()
            
            return customer
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete(self, customer_id: str) -> bool:
        """Delete a customer record"""
        session = self.Session()
        try:
            customer = session.query(CustomerModel).filter_by(customer_id=customer_id).first()
            if not customer:
                return False
                
            session.delete(customer)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def search(self, query: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[Customer]:
        """Search for customers based on query parameters"""
        session = self.Session()
        try:
            base_query = session.query(CustomerModel)
            
            # Apply filters from query
            for key, value in query.items():
                if hasattr(CustomerModel, key):
                    base_query = base_query.filter(getattr(CustomerModel, key) == value)
            
            # Apply pagination
            customer_models = base_query.limit(limit).offset(offset).all()
            
            # Convert to entities
            return [self._model_to_entity(model) for model in customer_models]
            
        finally:
            session.close()
    
    def find_by_status(self, status: CustomerStatus) -> List[Customer]:
        """Find customers by their status"""
        session = self.Session()
        try:
            customer_models = session.query(CustomerModel).filter_by(status=status.value).all()
            return [self._model_to_entity(model) for model in customer_models]
        finally:
            session.close()
    
    def find_by_document(self, document_type: str, document_id: str) -> Optional[Customer]:
        """Find a customer by a specific document"""
        session = self.Session()
        try:
            doc = session.query(DocumentModel).filter_by(
                doc_type=document_type, 
                doc_id=document_id
            ).first()
            
            if not doc:
                return None
                
            customer_model = session.query(CustomerModel).filter_by(
                customer_id=doc.customer_id
            ).first()
            
            if not customer_model:
                return None
                
            return self._model_to_entity(customer_model)
            
        finally:
            session.close()
    
    def count_by_criteria(self, criteria: Dict[str, Any]) -> int:
        """Count customers matching certain criteria"""
        session = self.Session()
        try:
            query = session.query(CustomerModel)
            
            # Apply filters from criteria
            for key, value in criteria.items():
                if hasattr(CustomerModel, key):
                    query = query.filter(getattr(CustomerModel, key) == value)
            
            return query.count()
            
        finally:
            session.close()
    
    def _model_to_entity(self, model: CustomerModel) -> Customer:
        """
        Convert database model to domain entity.
        
        Args:
            model: The database model object
            
        Returns:
            Corresponding domain entity
        """
        # Create Address entities
        addresses = []
        for addr_model in model.addresses:
            address = Address(
                street=addr_model.street,
                city=addr_model.city,
                state=addr_model.state,
                postal_code=addr_model.postal_code,
                country=addr_model.country,
                address_type=addr_model.address_type,
                is_primary=addr_model.is_primary
            )
            addresses.append(address)
        
        # Create ContactInformation entity
        contact_info = None
        if model.contacts:
            contact_model = model.contacts[0]  # Assuming one contact per customer
            contact_info = ContactInformation(
                email=contact_model.email,
                primary_phone=contact_model.primary_phone,
                secondary_phone=contact_model.secondary_phone
            )
        
        # Process documents
        documents = []
        for doc_model in model.documents:
            doc = {
                "doc_type": doc_model.doc_type,
                "doc_id": doc_model.doc_id,
                "issue_date": doc_model.issue_date,
                "expiry_date": doc_model.expiry_date
            }
            documents.append(doc)
        
        # Process custom fields
        custom_fields = {}
        for field_model in model.custom_fields:
            custom_fields[field_model.field_name] = field_model.field_value
        
        # Create and return Customer entity
        return Customer(
            customer_id=model.customer_id,
            customer_type=CustomerType(model.customer_type),
            status=CustomerStatus(model.status),
            registration_date=model.registration_date,
            first_name=model.first_name,
            last_name=model.last_name,
            middle_name=model.middle_name,
            date_of_birth=model.date_of_birth,
            company_name=model.company_name,
            registration_number=model.registration_number,
            tax_id=model.tax_id,
            contact_information=contact_info,
            addresses=addresses,
            risk_category=RiskCategory(model.risk_category),
            kyc_verified=model.kyc_verified,
            aml_cleared=model.aml_cleared,
            pep_status=model.pep_status,
            custom_fields=custom_fields,
            documents=documents
        )
