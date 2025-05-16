"""
Create Customer Use Case

This module implements the use case for creating a new customer.
"""
from typing import Dict, Any, Optional
from datetime import date
from dataclasses import dataclass

from ...domain.entities.customer import Customer, CustomerType, CustomerStatus, RiskCategory, ContactInformation, Address
from ...domain.services.kyc_rules_service import KycRulesService
from ..interfaces.customer_repository_interface import CustomerRepositoryInterface


@dataclass
class CreateCustomerRequest:
    """Data Transfer Object for customer creation request"""
    customer_type: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    company_name: Optional[str] = None
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[str] = None
    primary_phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    addresses: list = None
    documents: list = None
    custom_fields: Dict[str, str] = None


@dataclass
class CreateCustomerResponse:
    """Data Transfer Object for customer creation response"""
    success: bool
    customer_id: Optional[str] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    validation_errors: Optional[Dict[str, str]] = None


class CreateCustomerUseCase:
    """
    Use case for creating a new customer in the system.
    
    This use case handles the validation, business rules, and persistence
    of new customer records.
    """
    
    def __init__(self, customer_repository: CustomerRepositoryInterface, kyc_rules_service: KycRulesService):
        """
        Initialize the use case with required dependencies.
        
        Args:
            customer_repository: Repository for customer data
            kyc_rules_service: Service for KYC rules and validation
        """
        self.customer_repository = customer_repository
        self.kyc_rules_service = kyc_rules_service
    
    def execute(self, request: CreateCustomerRequest) -> CreateCustomerResponse:
        """
        Execute the create customer use case.
        
        Args:
            request: The customer creation request data
            
        Returns:
            Response indicating success or failure with details
        """
        # Validate request
        validation_errors = self._validate_request(request)
        if validation_errors:
            return CreateCustomerResponse(
                success=False,
                message="Validation failed",
                error_code="validation_error",
                validation_errors=validation_errors
            )
        
        try:
            # Convert request to domain entity
            customer = self._create_customer_entity(request)
            
            # Apply business rules
            initial_risk = self.kyc_rules_service.determine_risk_category(
                customer, 
                avg_monthly_balance=0, 
                transaction_volume=0
            )
            customer.risk_category = initial_risk
            
            # Save to repository
            created_customer = self.customer_repository.create(customer)
            
            return CreateCustomerResponse(
                success=True,
                customer_id=created_customer.customer_id,
                message="Customer created successfully"
            )
            
        except ValueError as e:
            return CreateCustomerResponse(
                success=False,
                message=str(e),
                error_code="value_error"
            )
        except Exception as e:
            return CreateCustomerResponse(
                success=False,
                message=f"An error occurred: {str(e)}",
                error_code="system_error"
            )
    
    def _validate_request(self, request: CreateCustomerRequest) -> Dict[str, str]:
        """
        Validate the customer creation request.
        
        Args:
            request: The request to validate
            
        Returns:
            Dictionary of validation errors, empty if none
        """
        errors = {}
        
        # Validate customer type
        try:
            customer_type = CustomerType(request.customer_type)
        except ValueError:
            errors["customer_type"] = f"Invalid customer type: {request.customer_type}"
            return errors  # Return early as other validations depend on customer type
            
        # Type-specific validations
        if customer_type == CustomerType.INDIVIDUAL:
            if not request.first_name:
                errors["first_name"] = "First name is required for individual customers"
            if not request.last_name:
                errors["last_name"] = "Last name is required for individual customers"
            if not request.date_of_birth:
                errors["date_of_birth"] = "Date of birth is required for individual customers"
                
        elif customer_type == CustomerType.CORPORATE:
            if not request.company_name:
                errors["company_name"] = "Company name is required for corporate customers"
            if not request.registration_number:
                errors["registration_number"] = "Registration number is required for corporate customers"
                
        # Validate that at least one address is provided
        if not request.addresses or len(request.addresses) == 0:
            errors["addresses"] = "At least one address is required"
            
        # Validate contact information
        if not request.email and not request.primary_phone:
            errors["contact"] = "Either email or primary phone must be provided"
            
        return errors
    
    def _create_customer_entity(self, request: CreateCustomerRequest) -> Customer:
        """
        Convert request DTO to domain entity.
        
        Args:
            request: The customer creation request
            
        Returns:
            A new Customer domain entity
        """
        # Generate a temporary ID - will be replaced by the repository
        temp_customer_id = "TEMP_" + str(hash(frozenset(request.__dict__.items())))
        
        # Parse the date of birth if provided
        dob = None
        if request.date_of_birth:
            try:
                dob = date.fromisoformat(request.date_of_birth)
            except ValueError:
                raise ValueError(f"Invalid date format for date_of_birth: {request.date_of_birth}")
        
        # Create contact information
        contact_info = None
        if request.email or request.primary_phone or request.secondary_phone:
            contact_info = ContactInformation(
                email=request.email,
                primary_phone=request.primary_phone,
                secondary_phone=request.secondary_phone
            )
        
        # Process addresses
        addresses = []
        if request.addresses:
            for addr_data in request.addresses:
                addresses.append(Address(
                    street=addr_data.get("street", ""),
                    city=addr_data.get("city", ""),
                    state=addr_data.get("state", ""),
                    postal_code=addr_data.get("postal_code", ""),
                    country=addr_data.get("country", ""),
                    address_type=addr_data.get("address_type", "residential"),
                    is_primary=addr_data.get("is_primary", False)
                ))
        
        # Create and return the customer entity
        return Customer(
            customer_id=temp_customer_id,
            customer_type=CustomerType(request.customer_type),
            status=CustomerStatus.PENDING_VERIFICATION,
            registration_date=date.today(),
            first_name=request.first_name,
            last_name=request.last_name,
            middle_name=request.middle_name,
            date_of_birth=dob,
            company_name=request.company_name,
            registration_number=request.registration_number,
            tax_id=request.tax_id,
            contact_information=contact_info,
            addresses=addresses,
            custom_fields=request.custom_fields or {},
            documents=request.documents or []
        )
