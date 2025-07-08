"""
Verify Customer KYC Use Case

This module implements the use case for verifying customer KYC requirements.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ...domain.entities.customer import Customer
from ...domain.services.kyc_rules_service import KycRulesService
from ..interfaces.customer_repository_interface import CustomerRepositoryInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



@dataclass
class VerifyCustomerKycRequest:
    """Data Transfer Object for customer KYC verification request"""
    customer_id: str
    verify_kyc: bool = False
    verify_aml: bool = False
    documents_verified: List[Dict[str, Any]] = None
    notes: Optional[str] = None


@dataclass
class VerifyCustomerKycResponse:
    """Data Transfer Object for customer KYC verification response"""
    success: bool
    is_fully_compliant: bool = False
    missing_documents: List[str] = None
    expired_documents: List[str] = None
    message: Optional[str] = None
    error_code: Optional[str] = None


class VerifyCustomerKycUseCase:
    """
    Use case for verifying a customer's KYC compliance.
    
    This use case handles the verification of customer KYC requirements
    and updates the customer record accordingly.
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
    
    def execute(self, request: VerifyCustomerKycRequest) -> VerifyCustomerKycResponse:
        """
        Execute the verify customer KYC use case.
        
        Args:
            request: The verification request data
            
        Returns:
            Response indicating success or failure with details
        """
        try:
            # Get the customer from repository
            customer = self.customer_repository.get_by_id(request.customer_id)
            if not customer:
                return VerifyCustomerKycResponse(
                    success=False,
                    message=f"Customer not found with ID: {request.customer_id}",
                    error_code="not_found"
                )
            
            # Add any verified documents
            if request.documents_verified:
                for doc in request.documents_verified:
                    customer.add_document(
                        doc_type=doc.get("doc_type"),
                        doc_id=doc.get("doc_id"),
                        expiry_date=doc.get("expiry_date")
                    )
            
            # Validate KYC requirements
            kyc_validation = self.kyc_rules_service.validate_kyc_requirements(customer)
            
            # Update customer KYC/AML verification status
            if request.verify_kyc:
                customer.mark_kyc_verified()
                
            if request.verify_aml:
                customer.mark_aml_cleared()
                
            # Save customer changes
            self.customer_repository.update(customer)
            
            return VerifyCustomerKycResponse(
                success=True,
                is_fully_compliant=kyc_validation["is_compliant"] and customer.kyc_verified and customer.aml_cleared,
                missing_documents=kyc_validation["missing_documents"],
                expired_documents=kyc_validation["expired_documents"],
                message="Customer verification processed successfully"
            )
            
        except Exception as e:
            return VerifyCustomerKycResponse(
                success=False,
                message=f"An error occurred: {str(e)}",
                error_code="system_error"
            )
    
    def get_verification_requirements(self, customer_id: str) -> Dict[str, Any]:
        """
        Get the verification requirements for a customer.
        
        Args:
            customer_id: The ID of the customer
            
        Returns:
            Dictionary containing verification requirements
        """
        try:
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                return {
                    "success": False,
                    "message": f"Customer not found with ID: {customer_id}",
                    "error_code": "not_found"
                }
            
            kyc_validation = self.kyc_rules_service.validate_kyc_requirements(customer)
            required_documents = self.kyc_rules_service.evaluate_document_requirements(customer)
            
            return {
                "success": True,
                "is_kyc_verified": customer.kyc_verified,
                "is_aml_cleared": customer.aml_cleared,
                "is_compliant": kyc_validation["is_compliant"],
                "missing_documents": kyc_validation["missing_documents"],
                "expired_documents": kyc_validation["expired_documents"],
                "expiring_soon": kyc_validation["expiring_soon"],
                "required_documents": required_documents,
                "risk_category": customer.risk_category.value
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred: {str(e)}",
                "error_code": "system_error"
            }
