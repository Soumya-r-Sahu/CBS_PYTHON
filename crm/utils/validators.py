"""
CRM Data Validation Utilities

This module provides validation utilities for CRM data.
It includes functions to validate customer data, campaign data, and lead data.
"""

import logging
import re
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

def validate_customer_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate customer data
    
    Args:
        data: Customer data to validate
        
    Returns:
        Tuple containing (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = ["name", "email", "phone"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate email format if provided
    if "email" in data and data["email"]:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data["email"]):
            errors.append("Invalid email format")
    
    # Validate phone format if provided
    if "phone" in data and data["phone"]:
        phone_pattern = r'^\+?[\d\s\-\(\)]{8,20}$'
        if not re.match(phone_pattern, data["phone"]):
            errors.append("Invalid phone number format")
    
    return len(errors) == 0, errors

def validate_campaign_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate campaign data
    
    Args:
        data: Campaign data to validate
        
    Returns:
        Tuple containing (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = ["name", "type", "start_date"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate campaign type
    valid_types = ["email", "sms", "social", "call", "direct_mail"]
    if "type" in data and data["type"] not in valid_types:
        errors.append(f"Invalid campaign type. Must be one of: {', '.join(valid_types)}")
    
    # Validate date format
    if "start_date" in data:
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, data["start_date"]):
            errors.append("Invalid date format. Use YYYY-MM-DD")
    
    return len(errors) == 0, errors

def validate_lead_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate lead data
    
    Args:
        data: Lead data to validate
        
    Returns:
        Tuple containing (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = ["name", "source", "contact_info"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate lead source
    valid_sources = ["web", "referral", "advertisement", "direct", "partner", "other"]
    if "source" in data and data["source"] not in valid_sources:
        errors.append(f"Invalid lead source. Must be one of: {', '.join(valid_sources)}")
    
    # Validate contact info
    if "contact_info" in data and isinstance(data["contact_info"], dict):
        contact_info = data["contact_info"]
        if not any(k in contact_info and contact_info[k] for k in ["email", "phone"]):
            errors.append("At least one contact method (email or phone) must be provided")
    
    return len(errors) == 0, errors
