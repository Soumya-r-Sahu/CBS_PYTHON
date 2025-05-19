"""
GDPR Compliance Utilities for Core Banking System

This module provides utilities for ensuring GDPR compliance in data handling 
throughout the Core Banking System.
"""

import re
import logging
import json
from typing import Dict, Any, List, Union, Optional, Tuple
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

# Sensitive data patterns (for identifying PII)
SENSITIVE_DATA_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b(?:\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b',
    'credit_card': r'\b(?:\d{4}[- ]?){3}\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',  # US Social Security Number
    'pan': r'\b[A-Z]{5}\d{4}[A-Z]\b',  # Permanent Account Number (India)
    'aadhar': r'\b\d{4}\s?\d{4}\s?\d{4}\b',  # Aadhar Number (India)
    'passport': r'\b[A-Z]{1,2}\d{6,9}\b',  # Passport Number (generic)
    'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
}

# Default data retention periods (in days)
DEFAULT_RETENTION_PERIODS = {
    'customer_data': 2555,  # ~7 years
    'transaction_data': 3650,  # 10 years (for financial regulations)
    'marketing_data': 730,  # 2 years
    'session_data': 90,  # 3 months
    'log_data': 365,  # 1 year
    'analytics_data': 180  # 6 months
}


def detect_pii(text: str) -> Dict[str, List[str]]:
    """
    Detect personally identifiable information (PII) in text.
    
    Args:
        text: The text to check for PII
        
    Returns:
        Dictionary of PII type to list of matches
    """
    if not text:
        return {}
    
    results = {}
    
    for pii_type, pattern in SENSITIVE_DATA_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            results[pii_type] = matches
    
    return results


def mask_pii(text: str, mask_char: str = "*", retain_pattern: Dict[str, str] = None) -> str:
    """
    Mask personally identifiable information in text.
    
    Args:
        text: The text containing PII to mask
        mask_char: Character to use for masking
        retain_pattern: Dictionary of PII type to pattern for which chars to retain
                      e.g. {'credit_card': 'last4'} will keep the last 4 digits of credit cards
    
    Returns:
        Text with PII masked
    """
    if not text:
        return text
    
    retain_pattern = retain_pattern or {
        'email': 'domain',
        'credit_card': 'last4',
        'phone': 'last4'
    }
    
    # Detect PII in the text
    pii_instances = detect_pii(text)
    
    # Replace each instance with a masked version
    for pii_type, instances in pii_instances.items():
        retain = retain_pattern.get(pii_type, '')
        
        for instance in instances:
            if pii_type == 'email' and retain == 'domain':
                # Mask email but keep domain
                parts = instance.split('@')
                if len(parts) == 2:
                    masked = f"{mask_char * len(parts[0])}@{parts[1]}"
                    text = text.replace(instance, masked)
            elif pii_type == 'credit_card' and retain == 'last4':
                # Mask credit card but keep last 4 digits
                last4 = instance[-4:]
                masked = f"{mask_char * (len(instance) - 4)}{last4}"
                text = text.replace(instance, masked)
            elif pii_type == 'phone' and retain == 'last4':
                # Mask phone but keep last 4 digits
                last4 = instance[-4:]
                masked = f"{mask_char * (len(instance) - 4)}{last4}"
                text = text.replace(instance, masked)
            else:
                # Default masking - replace all chars
                masked = mask_char * len(instance)
                text = text.replace(instance, masked)
    
    return text


def is_data_expired(creation_date: datetime, data_type: str) -> bool:
    """
    Check if data has exceeded its retention period.
    
    Args:
        creation_date: When the data was created
        data_type: Type of data (customer_data, transaction_data, etc.)
        
    Returns:
        True if data has exceeded retention period
    """
    if not creation_date:
        # If no creation date, consider expired
        return True
    
    # Get retention period for this data type
    retention_days = DEFAULT_RETENTION_PERIODS.get(data_type, 365)  # Default 1 year
    
    # Calculate expiration date
    expiration_date = creation_date + timedelta(days=retention_days)
    
    # Check if current date is past expiration
    return datetime.now() > expiration_date


def anonymize_data(data: Dict[str, Any], fields_to_anonymize: List[str]) -> Dict[str, Any]:
    """
    Anonymize specified fields in a data dictionary.
    
    Args:
        data: The data dictionary to anonymize
        fields_to_anonymize: List of field names to anonymize
        
    Returns:
        Anonymized data dictionary
    """
    if not data or not fields_to_anonymize:
        return data
    
    # Create a copy to avoid modifying the original
    anonymized = data.copy()
    
    for field in fields_to_anonymize:
        if field in anonymized:
            # Different anonymization methods based on field type
            if isinstance(anonymized[field], str):
                if field.lower().endswith(('email', 'mail')):
                    anonymized[field] = "anonymized@example.com"
                elif field.lower().endswith(('phone', 'mobile', 'tel')):
                    anonymized[field] = "0000000000"
                elif field.lower().endswith(('name', 'firstname', 'lastname')):
                    anonymized[field] = "Anonymous"
                elif field.lower().endswith(('address', 'street')):
                    anonymized[field] = "Anonymized Address"
                elif field.lower().endswith(('id', 'number', 'card')):
                    anonymized[field] = "XXXXXXXXXXXX"
                else:
                    anonymized[field] = "ANONYMIZED"
            elif isinstance(anonymized[field], (int, float)):
                anonymized[field] = 0
            elif isinstance(anonymized[field], bool):
                anonymized[field] = False
            elif isinstance(anonymized[field], dict):
                anonymized[field] = anonymize_data(anonymized[field], fields_to_anonymize)
            elif isinstance(anonymized[field], list):
                if all(isinstance(item, dict) for item in anonymized[field]):
                    # List of dictionaries
                    anonymized[field] = [anonymize_data(item, fields_to_anonymize) for item in anonymized[field]]
                else:
                    # List of simple values
                    anonymized[field] = []
    
    return anonymized


def right_to_be_forgotten(user_id: str, callback_functions: Dict[str, Callable] = None) -> Dict[str, Any]:
    """
    Implement the GDPR right to be forgotten for a user.
    
    Args:
        user_id: The ID of the user to be forgotten
        callback_functions: Dictionary of functions to call for different data types
        
    Returns:
        Results of the deletion operation
    """
    results = {}
    
    try:
        # Log the start of this sensitive operation
        logger.info(f"Starting GDPR right to be forgotten for user {user_id}")
        
        # Default callback functions dictionary if none provided
        callback_functions = callback_functions or {}
        
        # Apply deletion to each data type
        data_types = [
            'customer_data',
            'transaction_data',
            'marketing_data',
            'session_data',
            'log_data',
            'analytics_data'
        ]
        
        for data_type in data_types:
            try:
                # If there's a specific callback for this data type, use it
                if data_type in callback_functions and callable(callback_functions[data_type]):
                    result = callback_functions[data_type](user_id)
                    results[data_type] = result
                else:
                    # Skip if no callback function
                    results[data_type] = {"status": "skipped", "reason": "No callback provided"}
            except Exception as e:
                logger.error(f"Error processing {data_type} for GDPR request: {str(e)}")
                results[data_type] = {"status": "error", "error": str(e)}
        
        # Log completion
        logger.info(f"Completed GDPR right to be forgotten for user {user_id}")
        
        # Add overall status
        if any(result.get("status") == "error" for result in results.values()):
            results["overall_status"] = "partial"
        elif all(result.get("status") == "skipped" for result in results.values()):
            results["overall_status"] = "skipped"
        else:
            results["overall_status"] = "complete"
            
    except Exception as e:
        logger.error(f"Failed to process GDPR right to be forgotten for user {user_id}: {str(e)}")
        results["overall_status"] = "error"
        results["error"] = str(e)
    
    return results


def export_user_data(user_id: str, callback_functions: Dict[str, Callable] = None) -> Dict[str, Any]:
    """
    Export all data for a user as per GDPR data portability requirements.
    
    Args:
        user_id: The ID of the user whose data should be exported
        callback_functions: Dictionary of functions to call for different data types
        
    Returns:
        Collected user data
    """
    data = {}
    
    try:
        # Log the start of this sensitive operation
        logger.info(f"Starting GDPR data export for user {user_id}")
        
        # Default callback functions dictionary if none provided
        callback_functions = callback_functions or {}
        
        # Apply collection to each data type
        data_types = [
            'customer_data',
            'transaction_data',
            'marketing_data',
            'analytics_data'
        ]
        
        for data_type in data_types:
            try:
                # If there's a specific callback for this data type, use it
                if data_type in callback_functions and callable(callback_functions[data_type]):
                    result = callback_functions[data_type](user_id)
                    data[data_type] = result
                else:
                    # Skip if no callback function
                    data[data_type] = {"status": "skipped", "reason": "No callback provided"}
            except Exception as e:
                logger.error(f"Error exporting {data_type} for GDPR request: {str(e)}")
                data[data_type] = {"status": "error", "error": str(e)}
        
        # Log completion
        logger.info(f"Completed GDPR data export for user {user_id}")
        
        # Add metadata
        data["metadata"] = {
            "export_date": datetime.now().isoformat(),
            "user_id": user_id,
            "format_version": "1.0"
        }
            
    except Exception as e:
        logger.error(f"Failed to process GDPR data export for user {user_id}: {str(e)}")
        data["status"] = "error"
        data["error"] = str(e)
    
    return data


def create_consent_record(user_id: str, purpose: str, data_categories: List[str], 
                         expiry_days: int = 365, additional_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a GDPR-compliant consent record.
    
    Args:
        user_id: The ID of the user giving consent
        purpose: The purpose for which consent is given
        data_categories: List of data categories covered by this consent
        expiry_days: Number of days until consent expires
        additional_info: Any additional metadata to include
        
    Returns:
        Consent record
    """
    now = datetime.now()
    expiry = now + timedelta(days=expiry_days)
    
    consent_record = {
        "user_id": user_id,
        "purpose": purpose,
        "data_categories": data_categories,
        "consent_given_at": now.isoformat(),
        "consent_expires_at": expiry.isoformat(),
        "consent_id": f"consent-{user_id}-{now.strftime('%Y%m%d%H%M%S')}",
        "is_active": True
    }
    
    if additional_info:
        consent_record.update(additional_info)
    
    return consent_record


def revoke_consent(consent_id: str, callback_function: Callable = None) -> Dict[str, Any]:
    """
    Revoke a previously given consent.
    
    Args:
        consent_id: The ID of the consent to revoke
        callback_function: Function to call to actually revoke consent in the database
        
    Returns:
        Result of the revocation operation
    """
    result = {
        "consent_id": consent_id,
        "revoked_at": datetime.now().isoformat(),
        "status": "pending"
    }
    
    try:
        # Log the start of this sensitive operation
        logger.info(f"Revoking consent ID {consent_id}")
        
        # If there's a callback function, use it
        if callback_function and callable(callback_function):
            cb_result = callback_function(consent_id)
            result.update(cb_result)
            result["status"] = "complete"
        else:
            # Skip if no callback function
            result["status"] = "skipped"
            result["reason"] = "No callback provided"
        
        # Log completion
        logger.info(f"Completed consent revocation for ID {consent_id}")
            
    except Exception as e:
        logger.error(f"Failed to revoke consent ID {consent_id}: {str(e)}")
        result["status"] = "error"
        result["error"] = str(e)
    
    return result
