"""
KYC Rules Service

This service defines Know Your Customer (KYC) business rules for customer compliance.
"""
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from ..entities.customer import Customer, CustomerType, RiskCategory


class KycRulesService:
    """
    Domain service implementing Know Your Customer (KYC) business rules.
    
    This service is responsible for validating KYC compliance and 
    determining risk categories for customers.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the KYC rules service with configuration.
        
        Args:
            config: Optional configuration parameters for KYC rules
        """
        self.config = config or {}
        self.required_documents = {
            CustomerType.INDIVIDUAL: ["national_id", "proof_of_address"],
            CustomerType.CORPORATE: ["registration_certificate", "tax_registration", "director_id"],
            CustomerType.JOINT: ["national_id", "proof_of_address", "joint_declaration"],
            CustomerType.MINOR: ["birth_certificate", "guardian_id"]
        }
        
        # Threshold values for risk assessment
        self.high_value_threshold = self.config.get("high_value_threshold", 1000000)
        self.medium_value_threshold = self.config.get("medium_value_threshold", 100000)
        self.high_risk_countries = self.config.get("high_risk_countries", [])
        self.documents_validity_period = self.config.get("documents_validity_period", 365)  # days
    
    def determine_risk_category(self, customer: Customer, avg_monthly_balance: float = 0,
                               transaction_volume: float = 0, countries_transacted: List[str] = None) -> RiskCategory:
        """
        Determine the risk category for a customer based on various factors.
        
        Args:
            customer: The customer to assess
            avg_monthly_balance: Average monthly balance in primary accounts
            transaction_volume: Monthly transaction volume
            countries_transacted: List of countries customer transacts with
            
        Returns:
            RiskCategory: Assessed risk category
        """
        countries_transacted = countries_transacted or []
        risk_score = 0
        
        # Check if customer is a politically exposed person
        if customer.pep_status:
            return RiskCategory.HIGH
            
        # Check for high-risk countries
        if any(country in self.high_risk_countries for country in countries_transacted):
            return RiskCategory.HIGH
            
        # Check transaction volume and balance
        if transaction_volume > self.high_value_threshold or avg_monthly_balance > self.high_value_threshold:
            risk_score += 3
        elif transaction_volume > self.medium_value_threshold or avg_monthly_balance > self.medium_value_threshold:
            risk_score += 2
        else:
            risk_score += 1
            
        # Check customer type
        if customer.customer_type == CustomerType.CORPORATE:
            risk_score += 1
            
        # Assign risk category based on score
        if risk_score >= 3:
            return RiskCategory.HIGH
        elif risk_score == 2:
            return RiskCategory.MEDIUM
        else:
            return RiskCategory.LOW
    
    def validate_kyc_requirements(self, customer: Customer) -> Dict[str, Any]:
        """
        Validate if a customer meets KYC requirements.
        
        Args:
            customer: The customer to validate
            
        Returns:
            Dict with validation results
        """
        required_docs = self.required_documents.get(customer.customer_type, [])
        provided_docs = {doc["doc_type"] for doc in customer.documents}
        
        missing_docs = [doc for doc in required_docs if doc not in provided_docs]
        expired_docs = []
        
        # Check for expired documents
        today = date.today()
        for doc in customer.documents:
            if doc.get("expiry_date") and doc["expiry_date"] < today:
                expired_docs.append(doc["doc_type"])
                
        # Check if any documents are close to expiry
        expiring_soon = []
        expiry_warning_date = today + timedelta(days=30)
        for doc in customer.documents:
            if doc.get("expiry_date") and today < doc["expiry_date"] <= expiry_warning_date:
                expiring_soon.append(doc["doc_type"])
        
        is_compliant = len(missing_docs) == 0 and len(expired_docs) == 0
        
        return {
            "is_compliant": is_compliant,
            "missing_documents": missing_docs,
            "expired_documents": expired_docs,
            "expiring_soon": expiring_soon
        }
    
    def evaluate_document_requirements(self, customer: Customer) -> List[str]:
        """
        Determine what documents are required for a customer.
        
        Args:
            customer: The customer to evaluate
            
        Returns:
            List of required document types
        """
        base_requirements = self.required_documents.get(customer.customer_type, [])
        
        # Add additional requirements based on risk category
        if customer.risk_category == RiskCategory.HIGH:
            base_requirements.append("source_of_funds")
            
        # Add requirements for foreign nationals
        if customer.customer_type == CustomerType.INDIVIDUAL:
            for address in customer.addresses:
                if address.country != "US":  # Assuming US as base country, adjust as needed
                    base_requirements.append("visa_or_residence_permit")
                    break
        
        return base_requirements
    
    def calculate_document_validity(self, document_type: str, issue_date: date) -> date:
        """
        Calculate the validity period for a document.
        
        Args:
            document_type: Type of document
            issue_date: Date the document was issued
            
        Returns:
            Expiry date for the document
        """
        # Define document-specific validity periods
        validity_periods = {
            "national_id": 3650,  # 10 years
            "passport": 3650,     # 10 years
            "driver_license": 1825,  # 5 years
            "proof_of_address": 180,  # 6 months
            "visa": 365,          # 1 year
            "residence_permit": 730  # 2 years
        }
        
        # Get validity period for document type, or use default
        days_valid = validity_periods.get(document_type, self.documents_validity_period)
        
        return issue_date + timedelta(days=days_valid)
