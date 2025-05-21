"""
Validation Utilities for Risk Compliance Module

This module provides validation functions for risk compliance operations,
including risk assessment, compliance checking, and AML screening.

Tags: risk_compliance, validation, data_validation, aml, compliance_checks
AI-Metadata:
    component_type: validator
    criticality: high
    purpose: input_validation
    impact_on_failure: data_quality_issues
    regulatory_impact: high
"""

import logging
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that all required fields are present in the data dictionary
    
    Args:
        data: Dictionary containing the data to validate
        required_fields: List of field names that must be present
        
    Returns:
        Tuple containing:
            - Boolean indicating if validation passed
            - List of missing field names (empty if validation passed)
            
    AI-Metadata:
        purpose: Ensure required data is present
        criticality: high
        usage_pattern: input_validation
    """
    if not isinstance(data, dict):
        return False, ["Data must be a dictionary"]
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
        return False, missing_fields
    
    return True, []


def validate_transaction_data(transaction_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate transaction data for risk assessment and compliance checks
    
    Args:
        transaction_data: Dictionary containing transaction details
        
    Returns:
        Tuple containing:
            - Boolean indicating if validation passed
            - List of validation error messages (empty if validation passed)
            
    AI-Metadata:
        purpose: Validate transaction data for compliance
        criticality: high
        regulatory_relevance: high
    """
    errors = []
    
    # Check required fields
    required_fields = ["transaction_id", "amount", "timestamp", "source_account", "destination_account"]
    valid, missing_fields = validate_required_fields(transaction_data, required_fields)
    
    if not valid:
        errors.extend([f"Missing required field: {field}" for field in missing_fields])
    
    # Validate transaction ID format
    if "transaction_id" in transaction_data:
        if not isinstance(transaction_data["transaction_id"], str) or len(transaction_data["transaction_id"]) < 8:
            errors.append("Transaction ID must be a string of at least 8 characters")
    
    # Validate amount
    if "amount" in transaction_data:
        try:
            amount = float(transaction_data["amount"])
            if amount <= 0:
                errors.append("Transaction amount must be positive")
        except (ValueError, TypeError):
            errors.append("Transaction amount must be a valid number")
    
    # Validate timestamp
    if "timestamp" in transaction_data:
        try:
            # Try to parse datetime in ISO format
            datetime.fromisoformat(transaction_data["timestamp"].replace('Z', '+00:00'))
        except (ValueError, TypeError, AttributeError):
            errors.append("Timestamp must be a valid ISO format datetime string")
    
    # Validate account numbers
    for account_field in ["source_account", "destination_account"]:
        if account_field in transaction_data:
            if not validate_account_number(transaction_data[account_field]):
                errors.append(f"Invalid {account_field.replace('_', ' ')} format")
    
    return len(errors) == 0, errors


def validate_customer_data(customer_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate customer data for compliance and AML checks
    
    Args:
        customer_data: Dictionary containing customer details
        
    Returns:
        Tuple containing:
            - Boolean indicating if validation passed
            - List of validation error messages (empty if validation passed)
            
    AI-Metadata:
        purpose: Validate customer data for compliance
        criticality: high
        regulatory_relevance: high
    """
    errors = []
    
    # Check required fields
    required_fields = ["customer_id", "name", "date_of_birth", "identification"]
    valid, missing_fields = validate_required_fields(customer_data, required_fields)
    
    if not valid:
        errors.extend([f"Missing required field: {field}" for field in missing_fields])
    
    # Validate customer ID
    if "customer_id" in customer_data:
        if not isinstance(customer_data["customer_id"], str) or len(customer_data["customer_id"]) < 6:
            errors.append("Customer ID must be a string of at least 6 characters")
    
    # Validate name
    if "name" in customer_data:
        if not isinstance(customer_data["name"], str) or len(customer_data["name"]) < 2:
            errors.append("Customer name must be a string of at least 2 characters")
    
    # Validate date of birth
    if "date_of_birth" in customer_data:
        try:
            dob = datetime.fromisoformat(customer_data["date_of_birth"].replace('Z', '+00:00'))
            now = datetime.now()
            age = now.year - dob.year - ((now.month, now.day) < (dob.month, dob.day))
            
            if age < 18:
                errors.append("Customer must be at least 18 years old")
            elif age > 120:
                errors.append("Invalid date of birth")
        except (ValueError, TypeError, AttributeError):
            errors.append("Date of birth must be a valid ISO format date string")
    
    # Validate identification
    if "identification" in customer_data:
        id_data = customer_data["identification"]
        if not isinstance(id_data, dict):
            errors.append("Identification must be a dictionary")
        else:
            id_required_fields = ["type", "number"]
            valid, missing_id_fields = validate_required_fields(id_data, id_required_fields)
            
            if not valid:
                errors.extend([f"Missing required identification field: {field}" for field in missing_id_fields])
            
            if "type" in id_data and id_data["type"] not in ["passport", "national_id", "drivers_license"]:
                errors.append("Identification type must be passport, national_id, or drivers_license")
    
    return len(errors) == 0, errors


def validate_account_number(account_number: str) -> bool:
    """
    Validate account number format
    
    Args:
        account_number: The account number to validate
        
    Returns:
        Boolean indicating if the account number is valid
        
    AI-Metadata:
        purpose: Validate account number format
        criticality: medium
    """
    # Simple validation - can be enhanced with more specific rules
    if not isinstance(account_number, str):
        return False
    
    # Check if alphanumeric with possible hyphens
    return bool(re.match(r'^[a-zA-Z0-9\-]{5,30}$', account_number))


def validate_regulatory_report(report_data: Dict[str, Any], report_type: str) -> Tuple[bool, List[str]]:
    """
    Validate regulatory report data
    
    Args:
        report_data: Dictionary containing report data
        report_type: Type of regulatory report
        
    Returns:
        Tuple containing:
            - Boolean indicating if validation passed
            - List of validation error messages (empty if validation passed)
            
    AI-Metadata:
        purpose: Validate regulatory report data
        criticality: high
        regulatory_relevance: high
    """
    errors = []
    
    # Common required fields for all report types
    common_required_fields = ["report_id", "reporting_entity", "submission_date"]
    valid, missing_fields = validate_required_fields(report_data, common_required_fields)
    
    if not valid:
        errors.extend([f"Missing required field: {field}" for field in missing_fields])
    
    # Validate based on report type
    if report_type == "suspicious_activity":
        # SAR specific validations
        sar_required_fields = ["suspect_details", "activity_date", "activity_description", "alert_triggers"]
        valid, missing_fields = validate_required_fields(report_data, sar_required_fields)
        
        if not valid:
            errors.extend([f"Missing required SAR field: {field}" for field in missing_fields])
        
        # Validate activity description
        if "activity_description" in report_data:
            if not isinstance(report_data["activity_description"], str) or len(report_data["activity_description"]) < 50:
                errors.append("Activity description must be detailed (minimum 50 characters)")
    
    elif report_type == "currency_transaction":
        # CTR specific validations
        ctr_required_fields = ["transaction_amount", "transaction_date", "involved_parties"]
        valid, missing_fields = validate_required_fields(report_data, ctr_required_fields)
        
        if not valid:
            errors.extend([f"Missing required CTR field: {field}" for field in missing_fields])
        
        # Validate transaction amount
        if "transaction_amount" in report_data:
            try:
                amount = float(report_data["transaction_amount"])
                if amount < 10000:  # Standard CTR threshold in many jurisdictions
                    errors.append("CTR is typically required for transactions of $10,000 or more")
            except (ValueError, TypeError):
                errors.append("Transaction amount must be a valid number")
    
    # Add more report types as needed
    
    return len(errors) == 0, errors


def is_high_risk_country(country_code: str) -> bool:
    """
    Check if a country is in the high-risk list
    
    Args:
        country_code: ISO country code to check
        
    Returns:
        Boolean indicating if the country is considered high risk
        
    AI-Metadata:
        purpose: Identify high-risk jurisdictions
        criticality: high
        regulatory_relevance: high
    """
    # This is a simplified list - in production, this would come from a regularly updated database
    # based on FATF and other regulatory bodies' designations
    high_risk_countries = [
        "NK", "IR", "CU", "SY", "AF", "YE", "VE", "MM"
    ]
    
    return country_code.upper() in high_risk_countries


def validate_pep_screening_data(screening_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate politically exposed person (PEP) screening data
    
    Args:
        screening_data: Dictionary containing screening data
        
    Returns:
        Tuple containing:
            - Boolean indicating if validation passed
            - List of validation error messages (empty if validation passed)
            
    AI-Metadata:
        purpose: Validate PEP screening data
        criticality: high
        regulatory_relevance: high
    """
    errors = []
    
    # Required fields for PEP screening
    required_fields = ["name", "date_of_birth", "nationality", "screening_type"]
    valid, missing_fields = validate_required_fields(screening_data, required_fields)
    
    if not valid:
        errors.extend([f"Missing required field: {field}" for field in missing_fields])
    
    # Validate screening type
    if "screening_type" in screening_data:
        valid_types = ["pep", "sanctions", "adverse_media", "comprehensive"]
        if screening_data["screening_type"] not in valid_types:
            errors.append(f"Screening type must be one of: {', '.join(valid_types)}")
    
    # Validate name format
    if "name" in screening_data:
        if not isinstance(screening_data["name"], str) or len(screening_data["name"].split()) < 2:
            errors.append("Name should include at least first and last name")
    
    return len(errors) == 0, errors
